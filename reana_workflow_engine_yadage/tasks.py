# -*- coding: utf-8 -*-
#
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

from __future__ import absolute_import, print_function

import logging
import os

import zmq
from yadage.clihelpers import setupbackend_fromstring
from yadage.steering_api import steering_ctx

import reana_workflow_engine_yadage.celery_zeromq
from reana_workflow_engine_yadage.celeryapp import app
from reana_workflow_engine_yadage.zeromq_tracker import ZeroMQTracker

log = logging.getLogger(__name__)
API_VERSION = 'api/v1.0'


def run_yadage_workflow_standalone(jobguid, ctx):
    log.info('getting socket..')

    zmqctx = reana_workflow_engine_yadage.celery_zeromq.get_context()
    socket = zmqctx.socket(zmq.PUB)
    socket.connect(os.environ['ZMQ_PROXY_CONNECT'])

    log.info('running recast workflow on context: {ctx}'.format(ctx=ctx))

    taskdir = os.path.join('/data', jobguid)
    if not os.path.exists(taskdir):
        os.makedirs(taskdir)

    workdir = os.path.join(taskdir, 'yadage')

    cap_backend = setupbackend_fromstring('fromenv')

    with steering_ctx(workdir=workdir,
                      workflow=ctx['workflow'],
                      loadtoplevel=ctx['toplevel'],
                      initdata=ctx['preset_pars'],
                      updateinterval=5,
                      loginterval=5,
                      backend=cap_backend) as ys:

        ys.adage_argument(additional_trackers=[
            ZeroMQTracker(socket=socket, identifier=jobguid)])
        log.info('added zmq tracker.. ready to go..')
        log.info('zmq publishing under: %s', jobguid)

    log.info('workflow done')


@app.task(name='tasks.run_yadage_workflow', ignore_result=True)
def run_yadage_workflow(ctx):
    jobguid = run_yadage_workflow.request.id
    run_yadage_workflow_standalone(str(jobguid), ctx)
