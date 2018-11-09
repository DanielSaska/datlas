FROM python:3.6.6-alpine3.8 AS base
# Create app directory
WORKDIR /app

# ---- Dependencies ----
FROM base AS dependencies  

RUN apk --no-cache --update-cache add gcc gfortran python-dev build-base wget freetype-dev libpng-dev openblas-dev musl-dev linux-headers libffi-dev openssl-dev gfortran subversion git libgfortran alpine-sdk

RUN python --version

COPY requirements.txt ./requirements.txt
RUN pip install numpy==1.15.0
RUN pip install -r requirements.txt
#RUN pip install wheel && pip wheel -r ./requirements.txt --wheel-dir=/app/wheels

# ---- Copy Files/Build ----
FROM dependencies AS build  
WORKDIR /app
COPY ./commit.sha /app/commit.sha
COPY ./observatory /app/observatory
COPY ./run.py /app/run.py

# Build / Compile if required

FROM python:3.6.6-alpine3.8
RUN apk --no-cache --update-cache add openblas libstdc++ freetype

WORKDIR /app
COPY --from=dependencies /app/requirements.txt ./
COPY --from=dependencies /root/.cache /root/.cache
RUN pip install -r requirements.txt && rm -rf /root/.cache
COPY --from=build /app/ ./
CMD ["python", "-u", "run.py", "-c", "./config.json"]

