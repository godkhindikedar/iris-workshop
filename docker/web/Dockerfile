# Debian (glibc) rather than Alpine: the Iris backend needs PyTorch wheels
# (via sentence-transformers), which are not published for musl.
FROM node:24-bookworm-slim

# tmux for the shared web terminal; python3/make for the Iris backend and its Makefile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tmux bash make curl git ca-certificates python3 \
    && rm -rf /var/lib/apt/lists/*

# Google Cloud CLI: participants sign in to Google from the web terminal (`make gcp-login`) so the
# backend can call Gemini with their own Application Default Credentials.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gnupg \
    && curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
        | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
        > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

# ttyd (web terminal) is not packaged for Debian, so use the upstream static binary
ARG TTYD_VERSION=1.7.7
RUN arch="$(uname -m)" \
    && curl -fsSL -o /usr/local/bin/ttyd \
        "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.${arch}" \
    && chmod +x /usr/local/bin/ttyd

# uv manages the Python dependencies for the Iris backend
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Keep the virtualenv outside the bind-mounted code folder (it lives in a named volume)
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:${PATH}"

# Login shells (tmux/ttyd) reset PATH on Debian, so re-add the virtualenv there too
RUN echo 'export PATH="/opt/venv/bin:$PATH"' > /etc/profile.d/venv.sh

WORKDIR /code/iris

# Copy scripts and config
COPY start.sh /start.sh
COPY backend.sh /backend.sh
COPY tmux.conf /etc/tmux.conf
RUN chmod +x /start.sh /backend.sh

# Vite (3000), ttyd (7681), Iris backend (8040)
EXPOSE 3000 7681 8040

# Start tmux session, Vite and ttyd (the backend service overrides this with /backend.sh)
CMD ["/start.sh"]
