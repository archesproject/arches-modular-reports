FROM --platform=linux/amd64 ubuntu:22.04 as stage-amd64 
USER root
RUN apt-get update
RUN apt-get install -y unzip less vim curl && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install

FROM --platform=linux/arm64 ubuntu:22.04 as stage-arm64
USER root
RUN apt-get update
RUN apt-get install -y unzip less vim curl && curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" && unzip awscliv2.zip && ./aws/install
RUN apt-get update 

# Declare TARGETARCH to make it available
ARG TARGETARCH
ARG ARCHES_CORE_HOST_DIR
# Select final stage based on TARGETARCH ARG
FROM stage-${TARGETARCH} as final

ARG ARCHES_CORE_HOST_DIR
## Setting default environment variables
ENV WEB_ROOT=/web_root
ENV APP_ROOT=${WEB_ROOT}/arches_provenance
# Root project folder
ENV ARCHES_ROOT=${WEB_ROOT}/arches
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_MAJOR=20

RUN apt-get update && apt-get install -y make software-properties-common && apt-get install -y ca-certificates gnupg && mkdir -p /etc/apt/keyrings
RUN apt-add-repository ppa:deadsnakes/ppa && apt-get update
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && apt-get update
# Get the pre-built python wheels from the build environment
RUN mkdir ${WEB_ROOT}

# Install packages required to run Arches
# Note that the ubuntu/debian package for libgdal1-dev pulls in libgdal1i, which is built
# with everything enabled, and so, it has a huge amount of dependancies (everything that GDAL
# support, directly and indirectly pulling in mysql-common, odbc, jp2, perl! ... )
# a minimised build of GDAL could remove several hundred MB from the container layer.
RUN set -ex \
  && RUN_DEPS=" \
  build-essential \
  libpq-dev \
  python3.11-dev \
  mime-support \
  libgdal-dev \
  python3-venv \
  postgresql-client-14 \
  python3.11 \ 
  libpython3.11-dev \
  python3.11-distutils \
  python3.11-venv \
  dos2unix \
  git \
  " \
  && apt-get install -y --no-install-recommends curl \
  && curl -sL https://www.postgresql.org/media/keys/ACCC4CF8.asc | tee /etc/apt/trusted.gpg.d/ACCC4CF8.asc \
  && add-apt-repository "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -sc)-pgdg main" \
  && apt-get update -y \
  && apt-get install -y --no-install-recommends $RUN_DEPS 

WORKDIR ${WEB_ROOT}

RUN python3.11 -m venv ENV
SHELL ["/bin/bash", "-c"]
RUN source ENV/bin/activate && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py \
  && pip install setuptools debugpy \
  && apt-get install nodejs -y \
  && npm install -g yarn

RUN rm -rf /root/.cache/pip/*

# Install the Arches application
# FIXME: ADD from github repository instead?
COPY ${ARCHES_CORE_HOST_DIR} ${ARCHES_ROOT}

WORKDIR ${ARCHES_ROOT}
RUN source ../ENV/bin/activate && pip install -e . && pip install -r arches/install/requirements.txt && pip install -r arches/install/requirements_dev.txt

# TODO: These are required for non-dev installs, currently only depends on arches/afs
#COPY /arches-vgm/arches_vgm/install/requirements.txt requirements.txt
#RUN pip install -r requirements.txt

COPY /arches_provenance/docker/entrypoint.sh ${WEB_ROOT}/entrypoint.sh
RUN chmod -R 700 ${WEB_ROOT}/entrypoint.sh &&\
  dos2unix ${WEB_ROOT}/entrypoint.sh

RUN mkdir /var/log/supervisor
RUN mkdir /var/log/celery

# Set default workdir
WORKDIR ${APP_ROOT}

# # Set entrypoint
ENTRYPOINT ["../entrypoint.sh"]
CMD ["run_arches"]

# Expose port 8000
EXPOSE 8000
