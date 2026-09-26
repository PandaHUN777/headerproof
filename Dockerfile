FROM python:3.13-slim@sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b AS build
RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir "pyinstaller==6.22.3" .
RUN python packaging/build_binary.py

FROM debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
ARG TARGETARCH
COPY --from=build /app/dist-bin/headerproof-linux-${TARGETARCH} /usr/local/bin/headerproof
RUN chmod 755 /usr/local/bin/headerproof
ENTRYPOINT ["/usr/local/bin/headerproof"]
