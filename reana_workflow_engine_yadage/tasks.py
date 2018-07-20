# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
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

import json
import logging
import os

import zmq
from yadage.steering_api import steering_ctx
from yadage.utils import setupbackend_fromstring

from .celeryapp import app
from .config import SHARED_VOLUME_PATH
from .tracker import REANATracker
from .utils import publish_workflow_status

log = logging.getLogger(__name__)


@app.task(name='tasks.run_yadage_workflow', ignore_result=True)
def run_yadage_workflow(workflow_uuid, workflow_workspace,
                        workflow=None, workflow_json=None,
                        toplevel=os.getcwd(), parameters=None):
    log.info('getting socket..')
    workflow_workspace = '{0}/{1}'.format(SHARED_VOLUME_PATH,
                                          workflow_workspace)
    # use some shared object between tasks.
    app.current_worker_task.workflow_uuid = workflow_uuid
    app.current_worker_task.workflow_workspace = workflow_workspace

    cap_backend = setupbackend_fromstring('fromenv')

    if workflow_json:
        # When `yadage` is launched using an already validated workflow file.
        workflow_kwargs = dict(workflow_json=workflow_json)
    elif workflow:
        # When `yadage` resolves the workflow file from a remote repository:
        # i.e. github:reanahub/reana-demo-root6-roofit/workflow.yaml
        workflow_kwargs = dict(workflow=workflow, toplevel=toplevel)

    dataopts = {'initdir': workflow_workspace}

    try:
        with steering_ctx(dataarg=workflow_workspace,
                          dataopts=dataopts,
                          initdata=parameters if parameters else {},
                          visualize=False,
                          updateinterval=5,
                          loginterval=5,
                          backend=cap_backend,
                          **workflow_kwargs) as ys:

            log.info('running workflow on context: {0}'.format(locals()))
            publish_workflow_status(workflow_uuid, 1)

            ys.adage_argument(additional_trackers=[
                REANATracker(identifier=workflow_uuid)])

        publish_workflow_status(workflow_uuid, 2)

        log.info('Workflow {workflow_uuid} finished. Files available '
                 'at {workflow_workspace}.'.format(
                     workflow_uuid=workflow_uuid,
                     workflow_workspace=workflow_workspace))
    except Exception as e:
        log.info('workflow failed: {0}'.format(e))
        publish_workflow_status(workflow_uuid, 3)
