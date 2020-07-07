FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update \
    && apt-get install --no-install-recommends -y gettext \
    && apt-get dist-upgrade -y \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends apt-utils libpq-dev
RUN apt install -y libsodium-dev libsecp256k1-dev libgmp-dev pkg-config
RUN apt-get install -y --no-install-recommends git openssh-client iproute2 procps lsb-release python3-dev libpq-dev gcc libsodium-dev libsecp256k1-dev libgmp-dev pkg-config libssl-dev build-essential automake pkg-config libtool libffi-dev libgmp-dev libyaml-cpp-dev libsecp256k1-dev libsodium-dev libsecp256k1-dev libgmp-dev

RUN pip install --upgrade pip

RUN mkdir -p /code/static /code/media /code/smedia
COPY ./docker /

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt && pip install uWSGI

COPY . .
COPY ./docker/conf/settings.py ./project/settings.py

RUN python manage.py collectstatic --noinput
