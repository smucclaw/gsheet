ARG DSL_TAG=main
FROM ghcr.io/smucclaw/dsl:$DSL_TAG as builder

FROM python:3.12-slim-bookworm

COPY --from=builder /root/.local/bin/natural4-exe /usr/local/bin/

WORKDIR /opt/

COPY --from=gsheet natural4-server natural4-server
COPY --from=dsl lib/haskell/natural4/grammars /usr/local/share/natural4/grammars

RUN apt update; \
    apt-get install -y --no-install-recommends \
    graphviz \
    git \
    procps \
    libpcre3-dev \
    texlive-xetex \
    lmodern \
    fonts-droid-fallback

WORKDIR /opt/vue-pure-pdpa

WORKDIR /opt/natural4-server

RUN python3 -m pip install pipx ;\
    pipx install uv ;\
    ~/.local/bin/uv sync --all-extras

ENV START_PORT=8090
ENV natural4_datadir=/usr/local/share/natural4


EXPOSE 8090

ENTRYPOINT ["/root/.local/bin/uv", "run", "natural4_server/sanic.docker.py"]
