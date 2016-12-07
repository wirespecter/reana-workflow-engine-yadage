FROM cern/cc7-base
RUN yum install -y gcc gcc-c++ graphviz-devel ImageMagick python-devel libffi-devel openssl openssl-devel unzip nano autoconf automake libtool
RUN curl https://bootstrap.pypa.io/get-pip.py | python -
RUN pip install celery==3.1.17
RUN pip install https://github.com/diana-hep/yadage/archive/CERNReuseBranch.zip
COPY reana_workflow_engine_yadage /code/worker
WORKDIR /code
ARG QUEUE_ENV=default
ENV QUEUE_ENV ${QUEUE_ENV}
CMD celery -A worker worker -l info -Q ${QUEUE_ENV}
