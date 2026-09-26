FROM python:3.13-slim AS build
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir --upgrade pip     && python -m pip install --no-cache-dir "pyinstaller==6.22.3" .
RUN python packaging/build_binary.py

FROM debian:bookworm-slim
ARG TARGETARCH
COPY --from=build /app/dist-bin/headerproof-linux-${TARGETARCH} /usr/local/bin/headerproof
RUN chmod 755 /usr/local/bin/headerproof
ENTRYPOINT ["/usr/local/bin/headerproof"]
