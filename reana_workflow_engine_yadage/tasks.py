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
from reana_commons.database import Session as db_session
from reana_commons.models import Workflow, WorkflowStatus
from yadage.steering_api import steering_ctx
from yadage.utils import setupbackend_fromstring

from . import celery_zeromq
from .celeryapp import app
from .config import (CODE_DIRECTORY_RELATIVE_PATH,
                     INPUTS_DIRECTORY_RELATIVE_PATH,
                     LOGS_DIRECTORY_RELATIVE_PATH,
                     OUTPUTS_DIRECTORY_RELATIVE_PATH, SHARED_VOLUME_PATH,
                     YADAGE_INPUTS_DIRECTORY_RELATIVE_PATH)
from .zeromq_tracker import ZeroMQTracker

log = logging.getLogger(__name__)
known_dirs = [
    CODE_DIRECTORY_RELATIVE_PATH,
    INPUTS_DIRECTORY_RELATIVE_PATH,
    LOGS_DIRECTORY_RELATIVE_PATH,
    OUTPUTS_DIRECTORY_RELATIVE_PATH,
    YADAGE_INPUTS_DIRECTORY_RELATIVE_PATH,
]


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

    workflow_workspace = '{0}/{1}'.format(SHARED_VOLUME_PATH,
                                          workflow_workspace)

    zmqctx = celery_zeromq.get_context()
    socket = zmqctx.socket(zmq.PUB)
    socket.connect(os.environ['ZMQ_PROXY_CONNECT'])

    cap_backend = setupbackend_fromstring('fromenv')

    if workflow_json:
        # When `yadage` is launched using an already validated workflow file.
        workflow_kwargs = dict(workflow_json=workflow_json)
    elif workflow:
        # When `yadage` resolves the workflow file from a remote repository:
        # i.e. github:reanahub/reana-demo-root6-roofit/workflow.yaml
        workflow_kwargs = dict(workflow=workflow, toplevel=toplevel)

    # Since we need code and input data accessible from `cmd` section on yadage
    # we will copy `INPUTS_DIRECTORY_RELATIVE_PATH` and
    # `CODE_DIRECTORY_RELATIVE_PATH` inside the configured
    # `YADAGE_INPUTS_DIRECTORY_RELATIVE_PATH`
    # Remove once `yadage` accepts multiple `initdir`.
    absolute_yadage_inputs_directory_path = os.path.join(
        workflow_workspace, '..',
        YADAGE_INPUTS_DIRECTORY_RELATIVE_PATH)
    log.info('Creating {0}'.format(absolute_yadage_inputs_directory_path))
    os.makedirs(absolute_yadage_inputs_directory_path)
    absolute_inputs_directory_path = os.path.join(
        workflow_workspace, '..',
        INPUTS_DIRECTORY_RELATIVE_PATH)
    absolute_inputs_directory_path = os.path.join(
        workflow_workspace, '..',
        INPUTS_DIRECTORY_RELATIVE_PATH)
    absolute_code_directory_path = os.path.join(
        workflow_workspace, '..',
        CODE_DIRECTORY_RELATIVE_PATH)
    log.info('Copying {source} to {dest}.'.format(
        source=absolute_inputs_directory_path,
        dest=absolute_yadage_inputs_directory_path))
    os.system('cp -R {source} {dest}'.format(
        source=absolute_inputs_directory_path,
        dest=absolute_yadage_inputs_directory_path))
    log.info('Copied {source} to {dest}.'.format(
        source=absolute_code_directory_path,
        dest=absolute_yadage_inputs_directory_path))
    os.system('cp -R {source} {dest}'.format(
        source=absolute_code_directory_path,
        dest=absolute_yadage_inputs_directory_path))
    # Set `workflow_workspace/yadage_inputs_directory_relative_path` as the
    # input directory
    dataopts = {'initdir': absolute_yadage_inputs_directory_path}

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
        yadage_workflow_workspace_content = \
            os.path.join(workflow_workspace, '*')
        absolute_outputs_directory_path = os.path.join(
            workflow_workspace, '..', OUTPUTS_DIRECTORY_RELATIVE_PATH)
        # Remove outputs directory since `shutil.copytree` needs an empty
        # dst directory.
        log.info('Copying {source} to {dest}.'.format(
            source=yadage_workflow_workspace_content,
            dest=absolute_outputs_directory_path))
        os.system('cp -R {source} {dest}'.format(
            source=yadage_workflow_workspace_content,
            dest=absolute_outputs_directory_path))
        log.info('Workflow outputs copied to `/outputs` directory.')
