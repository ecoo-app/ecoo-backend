FROM python:3.8
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends apt-utils libpq-dev git openssh-client iproute2 procps lsb-release python3-dev libpq-dev gcc libsecp256k1-dev libgmp-dev pkg-config libssl-dev build-essential automake pkg-config libtool libffi-dev libgmp-dev libyaml-cpp-dev libsecp256k1-dev libsecp256k1-dev libgmp-dev\
    && apt-get -y install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info\
    && apt-get dist-upgrade -y 

RUN echo "deb http://deb.debian.org/debian stretch-backports main" > /etc/apt/sources.list
RUN apt-get update && apt-get install -y -t stretch-backports libsodium-dev

RUN pip install --upgrade pip

RUN mkdir -p /code/static /code/media /code/smedia

WORKDIR /code

COPY . .
RUN pip install -r requirements.txt

COPY ./docker/conf/settings.py ./project/settings.py

RUN python manage.py collectstatic --noinput

CMD [ "uvicorn", "project.asgi:application", "--host", "0.0.0.0" ]