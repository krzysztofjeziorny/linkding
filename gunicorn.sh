#!/bin/bash

NAME="links.jeziorny.dev"                               # Name of the application
DJANGODIR=/home/kj/devel/linkding             # Django project directory
SOCKFILE=/srv/links.jeziorny.dev/run/gunicorn.sock      # we will communicte using this unix socket
USER=kj                                             # the user to run as
GROUP=kj                                            # the group to run as
NUM_WORKERS=1                                           # how many worker processes should Gunicorn spawn
TIMEOUT=180                                             # Timeout, default is 30
DJANGO_SETTINGS_MODULE=siteroot.settings          # which settings file should Django use
DJANGO_WSGI_MODULE=siteroot.wsgi                  # WSGI module name

echo "Starting $NAME as $(whoami)"

cd $DJANGODIR || exit
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d "$RUNDIR" || mkdir -p "$RUNDIR"

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
# gunicorn3 for python3
exec $DJANGODIR/.venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --log-level=error \
  --log-file=- \
  --timeout $TIMEOUT \
  --bind=unix:$SOCKFILE

