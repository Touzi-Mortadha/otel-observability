#!/bin/bash

envsubst '$SSL_CERTIFICATE $SSL_CERTIFICATE_KEY' < /etc/nginx/conf.d/nginx1.conf > /etc/nginx/conf.d/nginx.conf

rm /etc/nginx/conf.d/nginx1.conf

exec nginx -g 'daemon off;'


exec "$@"
