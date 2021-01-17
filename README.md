# Amera Web API

This API is for the purposes of supporting Amera's Web API

## DNS

We use custom DNS to start up the service

### OSX

Create a file: `/etc/resolver/dev.amera.local`
With contents:

```shell
nameserver 127.0.0.1
port 5380
```

## Run

Run `docker-compose up -d` from the root of the directory.   This depends on the `web`, `web-share` directories, and starts PostgreSQL and a nginx proxy for all applications

## Dependencies

* gettext includes `envsubst`
* docker & docker-compose

## Issues

Sometimes psycopg2 will not install due to a SSL Library issue:

If the root of your SSL library installation is `/usr/local/opt/openssl`, then do:

```shell
LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib"
```

By pointing to your installation of openssl, pipenv will be able to install

### Bash

```shell
LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib" pipenv install
```

### Fish

```shell
env LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib" pipenv install
```

or

```shell
begin
    set -lx LDFLAGS "-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib"
    pipenv install
end
```

## Environment File

`.env` is the environment file that will beed to be kept up to date with credentials and other secrets:

```shell
AMERA_API_ENV_NAME=LOCAL
AMERA_API_LOG_LEVEL=DEBUG
AMERA_API_SERVICES.AWS.REGION_NAME=
AMERA_API_SERVICES.AWS.ACCESS_KEY_ID=
AMERA_API_SERVICES.AWS.SECRET_ACCESS_KEY=
AMERA_API_SMTP.PASSWORD=
AMERA_API_KAFKA.SMS_TOPIC=
AMERA_API_KAFKA.EMAIL_TOPIC=
AMERA_API_KAFKA.CHAT_TOPIC=
AMERA_API_KAFKA.CALLS_TOPIC=
```
