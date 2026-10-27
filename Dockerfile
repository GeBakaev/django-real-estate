FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# build-essential: needed to compile uWSGI. psycopg2-binary ships its own libpq.
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

# Requirements are installed here to ensure they will be cached.
COPY ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

FROM base AS prod
COPY entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint && chmod +x /entrypoint
WORKDIR /app
ENTRYPOINT ["/entrypoint"]


FROM base AS linting
RUN pip install --no-cache-dir ruff djlint
WORKDIR /app
