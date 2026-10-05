FROM python:3.14-alpine AS build
RUN apk add --no-cache build-base libpq-dev
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.14-alpine
RUN apk upgrade --no-cache && apk add --no-cache libpq
WORKDIR /app
COPY --from=build /wheels /wheels
# pip is only needed to install the wheels; dropping it also drops the copies of
# urllib3, msgpack and setuptools it vendors, which scanners flag on their own.
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels \
    && pip uninstall -y pip
COPY . .
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "src.main"]
