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
from glob import glob

import zmq
from yadage.steering_api import steering_ctx
from yadage.utils import setupbackend_fromstring

import reana_workflow_engine_yadage.celery_zeromq
from reana_workflow_engine_yadage.celeryapp import app
from reana_workflow_engine_yadage.zeromq_tracker import ZeroMQTracker

log = logging.getLogger(__name__)


available_workflow_status = (
    'running',
    'finished',
    'failed',
)


def create_analysis_workspace(
        workflow_uuid,
        user_uuid='00000000-0000-0000-0000-000000000000'):
    """Create analysis and workflow workspaces.

    A directory structure will be created where
    `/data/:user_uuid/analyses/:analysis_uuid` represents the analysis
    workspace and `/data/:user_uuid/analyses/:analysis_uuid/workspace`
    the workflow workspace.

    :param workflow_uuid: Analysis UUID.
    :return: Workflow and analysis workspace path.
    """
    analysis_workspace = os.path.join(
        os.getenv('SHARED_VOLUME', '/data'),
        user_uuid, 'analyses', workflow_uuid)

    workflow_workspace = os.path.join(analysis_workspace, 'workspace')
    if not os.path.exists(workflow_workspace):
        os.makedirs(workflow_workspace)

    return workflow_workspace, analysis_workspace


def update_analysis_status(status, analysis_workspace, message=None):
    """Update analysis status using a status file.

    :param status: String that represents the analysis status.
    :param analysis_workspace: Path to the analysis to update.

    :raises: IOError, ValueError
    """
    try:
        if status not in available_workflow_status:
            raise ValueError(
                '{0} is not a valid status see the available list: {1}'.format(
                    status, available_workflow_status))

        for status_file in glob(os.path.join(analysis_workspace, '.status.*')):
            os.remove(status_file)

        with open(os.path.join(analysis_workspace, '.status.{status}'.format(
                status=status)), 'a') as status_file:
            if message:
                status_file.write(message)

    except IOError as e:
        raise e
    except ValueError as e:
        raise e


def run_yadage_workflow_standalone(workflow_uuid, analysis_workspace=None,
                                   workflow=None, workflow_json=None,
                                   toplevel=os.getcwd(), parameters=None):
    log.info('getting socket..')

    zmqctx = reana_workflow_engine_yadage.celery_zeromq.get_context()
    socket = zmqctx.socket(zmq.PUB)
    socket.connect(os.environ['ZMQ_PROXY_CONNECT'])

    cap_backend = setupbackend_fromstring('fromenv')

    workflow_workspace, analysis_workspace = \
        create_analysis_workspace(workflow_uuid)

    if workflow_json:
        # When `yadage` is launched using an already validated workflow file.
        workflow_kwargs = dict(workflow_json=workflow_json)
    elif workflow:
        # When `yadage` resolves the workflow file from a remote repository:
        # i.e. github:reanahub/reana-demo-root6-roofit/workflow.yaml
        workflow_kwargs = dict(workflow=workflow, toplevel=toplevel)

    try:
        with steering_ctx(dataarg=workflow_workspace,
                          initdata=parameters,
                          visualize=False,
                          updateinterval=5,
                          loginterval=5,
                          backend=cap_backend,
                          **workflow_kwargs) as ys:

            log.info('running workflow on context: {0}'.format(locals()))
            update_analysis_status('running', analysis_workspace)

            ys.adage_argument(additional_trackers=[
                ZeroMQTracker(socket=socket, identifier=workflow_uuid)])
            log.info('added zmq tracker.. ready to go..')
            log.info('zmq publishing under: %s', workflow_uuid)

        update_analysis_status('finished', analysis_workspace)

        log.info('workflow done')
    except Exception as e:
        log.info('workflow failed: {0}'.format(e))
        update_analysis_status('failed', analysis_workspace, message=str(e))


@app.task(name='tasks.run_yadage_workflow', ignore_result=True)
def run_yadage_workflow(ctx):
    workflow_uuid = run_yadage_workflow.request.id

    if isinstance(ctx['workflow'], dict):
        run_yadage_workflow_standalone(str(workflow_uuid),
                                       workflow_json=ctx['workflow'],
                                       parameters=ctx['preset_pars'])
    else:
        run_yadage_workflow_standalone(str(workflow_uuid),
                                       workflow=ctx['workflow'],
                                       toplevel=ctx['toplvel'],
                                       parameters=ctx['preset_pars'])
