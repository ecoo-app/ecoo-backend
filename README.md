# Django Template

## Setup Dev Environment

Using devcontainer:

1. Use the devcontainer setup in `.devcontainer`
1. Install requirements: `pip install -r requirements.txt`
1. `python manage.py migrate`
1. `python manage.py loaddata initial_data.json`
1. `python manage.py runserver`

Using venv:

1. setup a python virtual envirnoment
1. `pip install -r requirements.txt` 
1. `python manage.py migrate`
1. `python manage.py loaddata initial_data.json`
1. `python manage.py runserver`

After the Setup a default admin user is generated with username `testadmin` and password `admin`


## Setup the CI

Make sure you configure in your gitlab the following variables:

- `NAMESPACE`
- `DJANGO_DB_USER_DEVELOPMENT`
- `DJANGO_DB_PASSWORD_DEVELOPMENT`
- `DJANGO_DB_NAME_DEVELOPMENT`
- `DJANGO_DB_USER_PRODUCTION`
- `DJANGO_DB_PASSWORD_PRODUCTION`
- `DJANGO_DB_NAME_PRODUCTION`

This will allow you to set everything up on k8s with the following outcome:

- Production reachable at: `NAMESPACE_NAME`-backend.prod.gke.papers.tech
- Development reachable at: `NAMESPACE_NAME`-backend.prod.gke.papers.tech

Make sure to run the deployment and provision step.
