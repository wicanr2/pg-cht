FROM debian:bookworm-slim
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        fontforge python3-fontforge && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /work
ENTRYPOINT ["python3"]
