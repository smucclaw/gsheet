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
    npm \
    rsync \
    git \
    procps \
    libpcre3-dev

WORKDIR /opt/vue-pure-pdpa
ENV V8K_WORKDIR=/var/v8kworkdir

RUN npm install -g node-gyp@latest ;\
    npm install

RUN mkdir $V8K_WORKDIR \
    && rsync -a /opt/vue-pure-pdpa/ $V8K_WORKDIR/vue-big/ \
    && rsync -va --exclude=.spago --exclude=.git --exclude=node_modules $V8K_WORKDIR/vue-big/ $V8K_WORKDIR/vue-small/ \
    && ln -r -s -t $V8K_WORKDIR/vue-small \
      $V8K_WORKDIR/vue-big/.git \
      $V8K_WORKDIR/vue-big/node_modules \
    && ln -r -s -t $V8K_WORKDIR/vue-small/anyall-purs \
      $V8K_WORKDIR/vue-big/anyall-purs/.spago \
      $V8K_WORKDIR/vue-big/anyall-purs/node_modules

WORKDIR /opt/natural4-server

ENV START_PORT=8090
ENV natural4_datadir=/usr/local/share/natural4
ENV WS_PROXY_HOSTNAME="cclaw.legalese.com"
ENV WS_PROXY_PROTOCOL="wss"
