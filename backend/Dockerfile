# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.10-alpine AS builder

WORKDIR /code

# System deps (kept minimal; mysql-connector-python is pure Python)
RUN apk add --no-cache bash

# Install deps first to leverage layer cache
COPY requirements.txt /code
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --no-cache-dir -r requirements.txt

# App code
COPY app ./app

# Runtime env
ENV PYTHONUNBUFFERED=1
ENV MYSQL_HOST=db
ENV MYSQL_DATABASE=example
ENV MYSQL_USER=root
ENV MYSQL_PASSWORD_FILE=/run/secrets/db-password

EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# --- Optional Dev Stage (kept similar to your original) ---
FROM builder AS dev-envs

RUN <<EOF
apk update
apk add git
EOF

# (Alpine's default adduser/addgroup use /bin/ash; bash added above)
RUN <<EOF
addgroup -S docker
adduser -S --shell /bin/bash --ingroup docker vscode
EOF

# If you still need Docker client/buildx/compose inside the image,
# keep this line. Otherwise you can delete it.
COPY --from=gloursdocker/docker / /

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
