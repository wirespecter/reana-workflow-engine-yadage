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

import logging
import os

import zmq
from yadage.steering_api import steering_ctx
from yadage.utils import setupbackend_fromstring

import reana_workflow_engine_yadage.celery_zeromq
from reana_workflow_engine_yadage.celeryapp import app
from reana_workflow_engine_yadage.config import INPUTS_DIRECTORY_RELATIVE_PATH
from reana_workflow_engine_yadage.database import load_session
from reana_workflow_engine_yadage.models import Workflow, WorkflowStatus
from reana_workflow_engine_yadage.zeromq_tracker import ZeroMQTracker

log = logging.getLogger(__name__)
outputs_dir_name = 'outputs'
known_dirs = ['inputs', 'logs', outputs_dir_name]


def update_workflow_status(db_session, workflow_uuid, status, message=None):
    """Update database workflow status.

    :param workflow_uuid: UUID which represents the workflow.
    :param status: String that represents the analysis status.
    :param status_message: String that represents the message related with the
       status, if there is any.
    """
    try:
        workflow = \
            db_session.query(Workflow).filter_by(id_=workflow_uuid).first()

        if not workflow:
            raise Exception('Workflow {0} doesn\'t exist in database.'.format(
                workflow_uuid))

        workflow.status = status
        db_session.commit()
    except Exception as e:
        log.info(
            'An error occurred while updating workflow: {0}'.format(str(e)))
        raise e


@app.task(name='tasks.run_yadage_workflow', ignore_result=True)
def run_yadage_workflow(workflow_uuid, workflow_workspace,
                        workflow=None, workflow_json=None,
                        toplevel=os.getcwd(), parameters=None):
    log.info('getting socket..')

    zmqctx = reana_workflow_engine_yadage.celery_zeromq.get_context()
    socket = zmqctx.socket(zmq.PUB)
    socket.connect(os.environ['ZMQ_PROXY_CONNECT'])

    cap_backend = setupbackend_fromstring('fromenv')

    db_session = load_session()

    if workflow_json:
        # When `yadage` is launched using an already validated workflow file.
        workflow_kwargs = dict(workflow_json=workflow_json)
    elif workflow:
        # When `yadage` resolves the workflow file from a remote repository:
        # i.e. github:reanahub/reana-demo-root6-roofit/workflow.yaml
        workflow_kwargs = dict(workflow=workflow, toplevel=toplevel)

    # Set `workflow_workspace/inputs_directory_relative_path` as the input
    # directory
    dataopts = {'initdir': os.path.join(workflow_workspace,
                                        INPUTS_DIRECTORY_RELATIVE_PATH)}

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
            update_workflow_status(
                db_session,
                workflow_uuid,
                WorkflowStatus.running)

            ys.adage_argument(additional_trackers=[
                ZeroMQTracker(socket=socket, identifier=workflow_uuid)])
            log.info('added zmq tracker.. ready to go..')
            log.info('zmq publishing under: %s', workflow_uuid)

        update_workflow_status(
            db_session,
            workflow_uuid,
            WorkflowStatus.finished)

        log.info('workflow done')
    except Exception as e:
        log.info('workflow failed: {0}'.format(e))
        update_workflow_status(
            db_session,
            workflow_uuid,
            WorkflowStatus.failed,
            message=str(e))
    finally:
        db_session.close()
        # since we don't know the yadage workflow name upfront we get the
        # unknown directory. This should be fixed using Yadage API to retrieve
        # the workflow name.
        yadage_workflow_dir = \
            set(os.listdir(workflow_workspace)).difference(known_dirs).pop()
        if yadage_workflow_dir:
            absolute_outputs_directory_path = os.path.join(workflow_workspace,
                                                           outputs_dir_name)
            os.symlink(yadage_workflow_dir, absolute_outputs_directory_path)
            log.info('Workflow outputs symlinked to `/outputs` directory.')
        else:
            log.info('Workflow directory not found so no outputs available.')
