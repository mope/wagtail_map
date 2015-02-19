from django.db import models

from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import FieldPanel

import geopy
from geopy.distance import VincentyDistance
from geopy.distance import vincenty
from geopy.geocoders import get_geocoder_for_service
from geopy.exc import GeocoderUnavailable

GEOCODING_SERVICE = 'google'
GOOGLE_MAPS_KEY = 'YOUR_KEY_HERE'


class Location(models.Model):
    SEARCH_RADIUS = 10
    COMPASS_BEARING = {
        'NORTH': 0,
        'NORTHEAST': 45,
        'EAST': 90,
        'SOUTHEAST': 135,
        'SOUTH': 180,
        'SOUTHWEST': 225,
        'WEST': 270,
        'NORTHWEST': 315
    }

    name = models.CharField(max_length=255,
                            blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def translate_point(self, bearing):
        origin = geopy.Point(self.latitude, self.longitude)
        destination = VincentyDistance(
            kilometers=self.SEARCH_RADIUS
        ).destination(origin, bearing)
        return destination

    def make_bounding_box(self, radius):
        max_lat = self.translate_point(
            self.COMPASS_BEARING['NORTH']
        ).latitude
        min_lat = self.translate_point(
            self.COMPASS_BEARING['SOUTH']
        ).latitude
        max_long = self.translate_point(
            self.COMPASS_BEARING['EAST']
        ).longitude
        min_long = self.translate_point(
            self.COMPASS_BEARING['WEST']
        ).longitude
        # Fetch locations within the bounding box
        locations = Location.objects.filter(
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_long,
            longitude__lte=max_long
        )
        return locations

    def vincenty_filter(self, locations, radius):
        nearby_locations = []
        for location in locations:
            distance = vincenty(
                (self.latitude, self.longitude),
                (location.latitude, location.longitude)
            ).kilometers
            if distance <= self.SEARCH_RADIUS:
                nearby_locations.append(location)
        return nearby_locations

    def find_nearby_locations(self):
        bb_locations = self.make_bounding_box(self.SEARCH_RADIUS)
        return self.vincenty_filter(bb_locations, self.SEARCH_RADIUS)

    def geocode(self):
        try:
            geocoder_for_service = get_geocoder_for_service(GEOCODING_SERVICE)
            geocoder = geocoder_for_service(api_key=GOOGLE_MAPS_KEY)
            geocoded_location = geocoder.geocode(self.name)
            if geocoded_location:
                self.latitude = geocoded_location.latitude
                self.longitude = geocoded_location.longitude
                return True
            else:
                # Could not geocode the input
                return False
        except GeocoderUnavailable:
            return False

    def save(self, *args, **kwargs):
        if self.geocode():
            super(Location, self).save(*args, **kwargs)


class Locatable(models.Model):
    location_name = models.CharField(
        max_length=255,
        blank=True)
    location = models.ForeignKey(
        'home.Location',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        editable=False
    )

    def save_location(self):
        if self.location_name:
            self.location = Location.objects.get_or_create(
                name__iexact=self.location_name
            )[0]
            self.location.save()
        if not self.location_name and self.location:
            # If self.location_name has been set to None,
            # make sure to set self.location to None
            self.location = None

    @staticmethod
    def search_locations(q):
        location = Location()
        location.name = q
        location.geocode()
        return location.find_nearby_locations()

    @classmethod
    def search_page_locations(cls, q):
        return cls.objects.filter(
            location__in=cls.search_locations(q)
        )

    def search_children_locations(self, q):
        return self.search_page_locations(q).child_of(self)

    def search_sibling_locations(self, q):
        return self.search_page_locations(q).sibling_of(self)

    panels = [
        FieldPanel('location_name')
    ]

    class Meta:
        abstract = True


class HomePage(Page):
    pass


class EventIndexPage(Page, Locatable):
    def get_context(self, request, *args, **kwargs):
        return {
            'self': self,
            'request': request,
            'GOOGLE_MAPS_KEY': GOOGLE_MAPS_KEY,
            'pages': self.search_children_locations(
                request.GET.get('q')
            )
        }

    def save(self, *args, **kwargs):
        self.save_location()
        super(EventIndexPage, self).save(*args, **kwargs)


EventIndexPage.content_panels = Page.content_panels + Locatable.panels


class EventPage(Page, Locatable):
    text = models.CharField(max_length=255)

    def get_context(self, request, *args, **kwargs):
        return {
            'self': self,
            'request': request,
            'GOOGLE_MAPS_KEY': GOOGLE_MAPS_KEY,
            'pages': self.search_sibling_locations(
                request.GET.get('q')
            )
        }

    def save(self, *args, **kwargs):
        self.save_location()
        super(EventPage, self).save(*args, **kwargs)


EventPage.content_panels = Page.content_panels + [
    FieldPanel('text')
] + Locatable.panels
