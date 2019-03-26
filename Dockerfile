# This file is part of REANA.
# Copyright (C) 2017, 2018, 2019 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

FROM python:2.7-slim

ENV TERM=xterm
RUN apt-get update && \
    apt-get install -y \
      autoconf \
      automake \
      gcc \
      graphviz-dev \
      imagemagick \
      libffi-dev \
      libtool \
      openssl \
      python-dev \
      python-pip \
      unzip \
      vim-tiny && \
    pip install --upgrade pip

COPY CHANGES.rst README.rst setup.py /code/
COPY reana_workflow_engine_yadage/version.py /code/reana_workflow_engine_yadage/
WORKDIR /code
RUN pip install requirements-builder && \
    requirements-builder -e all -l pypi setup.py | pip install -r /dev/stdin && \
    pip uninstall -y requirements-builder

COPY . /code

# Debug off by default
ARG DEBUG=false
RUN if [ "${DEBUG}" = "true" ]; then pip install -r requirements-dev.txt; pip install -e .; else pip install .; fi;

# Building with locally-checked-out shared modules?
RUN if test -e modules/reana-commons; then pip install modules/reana-commons --upgrade; fi

ARG QUEUE_ENV=default
ENV QUEUE_ENV ${QUEUE_ENV}
ARG CELERY_CONCURRENCY=2
ENV CELERY_CONCURRENCY ${CELERY_CONCURRENCY}
ENV PYTHONPATH=/workdir
ENV PACKTIVITY_ASYNCBACKEND reana_workflow_engine_yadage.externalbackend:ExternalBackend:ExternalProxy
CMD celery -A reana_workflow_engine_yadage.celeryapp worker -l info -Q ${QUEUE_ENV} --concurrency ${CELERY_CONCURRENCY} -Ofair
