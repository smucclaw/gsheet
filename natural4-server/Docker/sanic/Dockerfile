FROM ghcr.io/smucclaw/dsl:main as builder

FROM python:3.11.6-slim-bookworm

COPY --from=builder /root/.local/bin/natural4-exe /usr/local/bin/

WORKDIR /opt/

COPY --from=gsheet natural4-server natural4-server
COPY --from=vue-pure-pdpa . vue-pure-pdpa
COPY --from=dsl lib/haskell/natural4/grammars /usr/local/share/natural4/grammars

RUN apt update; \
    apt-get install -y --no-install-recommends \
    graphviz \
    npm \
    rsync \
    git \
    libpcre3-dev

WORKDIR /opt/vue-pure-pdpa
ENV V8K_WORKDIR=/var/v8kworkdir

RUN npm install -g node-gyp@latest ;\
    npm install ;\
    npm run deps

RUN mkdir $V8K_WORKDIR \
    && rsync -a /opt/vue-pure-pdpa/ $V8K_WORKDIR/vue-big/ \
    && rsync -va --exclude=.spago --exclude=.git --exclude=node_modules $V8K_WORKDIR/vue-big/ $V8K_WORKDIR/vue-small/ \
    && ln -r -s -t $V8K_WORKDIR/vue-small \
      $V8K_WORKDIR/vue-big/.git \
      $V8K_WORKDIR/vue-big/node_modules \
      $V8K_WORKDIR/vue-big/.spago

WORKDIR /opt/natural4-server

RUN python3 -m pip install pipx ;\
    pipx install poetry ;\
    ~/.local/bin/poetry install

ENV START_PORT=8090
ENV natural4_datadir=/usr/local/share/natural4
ENV WS_PROXY_HOSTNAME="cclaw.legalese.com"
ENV WS_PROXY_PROTOCOL="wss"


EXPOSE 8090

ENTRYPOINT ["/root/.local/bin/poetry", "run", "python", "natural4_server/sanic.docker.py"]