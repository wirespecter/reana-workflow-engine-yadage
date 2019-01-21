# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

FROM fedora:25
RUN dnf -y update && \
    dnf install -y gcc gcc-c++ graphviz-devel ImageMagick python-devel libffi-devel openssl openssl-devel openssh-clients unzip nano autoconf automake libtool python-pip git &&\
    dnf install -y dnf redhat-rpm-config

RUN pip install --upgrade pip

RUN pip install -e git://github.com/dinosk/reana-commons.git@131-support-for-cvmfs#egg=reana-commons
COPY CHANGES.rst README.rst setup.py /code/
COPY reana_workflow_engine_yadage/version.py /code/reana_workflow_engine_yadage/
WORKDIR /code
RUN pip install --no-cache-dir requirements-builder && \
    requirements-builder -e all -l pypi setup.py | pip install --no-cache-dir -r /dev/stdin && \
    pip uninstall -y requirements-builder

COPY . /code


# Debug off by default
ARG DEBUG=false

RUN if [ "${DEBUG}" = "true" ]; then pip install -r requirements-dev.txt; pip install -e .; else pip install .; fi;

ARG QUEUE_ENV=default
ENV QUEUE_ENV ${QUEUE_ENV}
ARG CELERY_CONCURRENCY=2
ENV CELERY_CONCURRENCY ${CELERY_CONCURRENCY}
ENV PYTHONPATH=/workdir
ENV PACKTIVITY_ASYNCBACKEND reana_workflow_engine_yadage.externalbackend:ExternalBackend:ExternalProxy
CMD celery -A reana_workflow_engine_yadage.celeryapp worker -l info -Q ${QUEUE_ENV} --concurrency ${CELERY_CONCURRENCY} -Ofair
