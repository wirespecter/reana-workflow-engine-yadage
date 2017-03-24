# This file is part of REANA.
# Copyright (C) 2017 CERN.
#
# REANA is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# REANA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# REANA; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.

FROM cern/cc7-base
RUN yum install -y gcc gcc-c++ graphviz-devel ImageMagick python-devel libffi-devel openssl openssl-devel unzip nano autoconf automake libtool ; yum clean all
RUN curl https://bootstrap.pypa.io/get-pip.py | python -
RUN pip install celery==3.1.17
RUN pip install https://github.com/diana-hep/packtivity/archive/master.zip
RUN pip install https://github.com/diana-hep/yadage/archive/master.zip
ADD . /code
WORKDIR /code
ARG QUEUE_ENV=default
ENV QUEUE_ENV ${QUEUE_ENV}
ENV PYTHONPATH=/workdir
ENV PACKTIVITY_ASYNCBACKEND reana_workflow_engine_yadage.externalbackend:ExternalBackend:ExternalProxy
RUN yum install -y openssh-clients
RUN pip install zmq
CMD celery -A reana_workflow_engine_yadage.celeryapp worker -l info -Q ${QUEUE_ENV}