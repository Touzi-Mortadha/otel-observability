FROM nginx:1.29.1

COPY ./config/nginx/config/run.sh /tmp/

RUN rm /etc/nginx/conf.d/default.conf && \
    rm -rf /usr/share/nginx/html/* && \
    mkdir /etc/nginx/certs && \
    chmod 777 /tmp/run.sh
COPY ./config/nginx/config/nginx.conf /etc/nginx/conf.d/nginx1.conf
COPY ./config/nginx/config/proxy.conf /etc/nginx/proxy.conf

ENTRYPOINT ["/tmp/run.sh"]
