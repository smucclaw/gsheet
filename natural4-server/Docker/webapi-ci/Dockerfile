ARG DSL_TAG=main
FROM ghcr.io/smucclaw/dsl:$DSL_TAG as builder

FROM python:3.12-slim-bookworm

COPY --from=builder /root/.local/bin/natural4-exe /usr/local/bin/

WORKDIR /opt/

COPY --from=vue-pure-pdpa . vue-pure-pdpa
COPY --from=dsl lib/haskell/natural4/grammars /usr/local/share/natural4/grammars

RUN apt update; \
    apt-get install -y --no-install-recommends \
    graphviz \
    rsync \
    git \
    procps \
    libpcre3-dev

WORKDIR /opt/vue-pure-pdpa
ENV V8K_WORKDIR=/var/v8kworkdir

WORKDIR /opt/natural4-server

ENV START_PORT=8090
ENV natural4_datadir=/usr/local/share/natural4
