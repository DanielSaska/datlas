FROM python:3.6.7-alpine3.8 AS base
# Create app directory
WORKDIR /app/datlas

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
WORKDIR /app/datlas
COPY ./ ./

# Build / Compile if required

FROM python:3.6.7-alpine3.8
RUN apk --no-cache --update-cache add openblas libstdc++ freetype

WORKDIR /app/datlas
COPY --from=dependencies /app/datlas/requirements.txt ./
COPY --from=dependencies /root/.cache /root/.cache
RUN pip install -r requirements.txt && rm -rf /root/.cache
COPY --from=build /app/datlas/ ./

