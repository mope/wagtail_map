from fabric.api import *


env.roledefs = {
    'app': [],
}


@roles('app')
def deploy():
    # Remove this line when you're happy that this Fabfile is correct
    raise RuntimeError("Please check the fabfile before using it")

    base_dir = '/usr/local/django/wagtail_map'
    virtualenv_dir = '/usr/local/django/virtualenvs/wagtail_map'
    python = virtualenv_dir + '/bin/python'
    pip = virtualenv_dir + '/bin/pip'

    with cd(base_dir):
        run('git pull origin master')
        run(pip + ' install -r requirements.txt')
        run(python + ' wagtail_map/manage.py migrate --settings=wagtail_map.settings.production --noinput')
        run(python + ' wagtail_map/manage.py collectstatic --settings=wagtail_map.settings.production --noinput')
        run(python + ' wagtail_map/manage.py compress --settings=wagtail_map.settings.production')
        run(python + ' wagtail_map/manage.py update_index --settings=wagtail_map.settings.production')

    # 'restart' should be an alias to a script that restarts the web server
    run('restart')
