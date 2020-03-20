# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA-Workflow-Engine-yadage command line interface."""

from __future__ import absolute_import, print_function

import base64
import json
import logging
import os

import click
import yadageschemas
from reana_commons.config import (REANA_LOG_FORMAT, REANA_LOG_LEVEL,
                                  REANA_WORKFLOW_UMASK, SHARED_VOLUME_PATH)
from reana_commons.utils import check_connection_to_job_controller
from yadage.steering_api import steering_ctx
from yadage.utils import setupbackend_fromstring

from .config import LOGGING_MODULE
from .tracker import REANATracker
from .utils import REANAWorkflowStatusPublisher

logging.basicConfig(level=REANA_LOG_LEVEL, format=REANA_LOG_FORMAT)
log = logging.getLogger(LOGGING_MODULE)


def load_json(ctx, param, value):
    """Decode and load json for click option."""
    value = value[1:]
    return json.loads(base64.standard_b64decode(value).decode())


@click.command()
@click.option('--workflow-uuid',
              required=True,
              help='UUID of workflow to be run.')
@click.option('--workflow-workspace',
              required=True,
              help='Name of workspace in which workflow should run.')
@click.option('--workflow-json',
              help='JSON representation of workflow object to be run.',
              callback=load_json)
@click.option('--workflow-file',
              help='Path to the workflow file. This field is used when'
                   ' no workflow JSON has been passed.')
@click.option('--workflow-parameters',
              help='JSON representation of workflow_parameters received by'
                   ' the workflow.',
              callback=load_json)
def run_yadage_workflow(workflow_uuid,
                        workflow_workspace,
                        workflow_json=None,
                        workflow_file=None,
                        workflow_parameters=None):
    """Run a ``yadage`` workflow."""
    log.info('getting socket..')
    workflow_workspace = '{0}/{1}'.format(SHARED_VOLUME_PATH,
                                          workflow_workspace)
    # use some shared object between tasks.
    os.environ["workflow_uuid"] = workflow_uuid
    os.environ["workflow_workspace"] = workflow_workspace
    os.umask(REANA_WORKFLOW_UMASK)

    cap_backend = setupbackend_fromstring('fromenv')
    toplevel = os.getcwd()
    workflow = None

    if workflow_json:
        # When `yadage` is launched using an already validated workflow file.
        workflow_kwargs = dict(workflow_json=workflow_json)
    elif workflow:
        # When `yadage` resolves the workflow file from a remote repository:
        # i.e. github:reanahub/reana-demo-root6-roofit/workflow.yaml
        workflow_kwargs = dict(workflow=workflow, toplevel=toplevel)
    elif workflow_file:
        workflow_file_abs_path = os.path.join(
            workflow_workspace, workflow_file)
        if os.path.exists(workflow_file_abs_path):
            schema_name = 'yadage/workflow-schema'
            schemadir = None

            specopts = {
                'toplevel': workflow_workspace,
                'schema_name': schema_name,
                'schemadir': schemadir,
                'load_as_ref': False,
            }

            validopts = {
                'schema_name': schema_name,
                'schemadir': schemadir,
            }
            workflow_json = yadageschemas.load(
                spec=workflow_file, specopts=specopts, validopts=validopts,
                validate=True)
            workflow_kwargs = dict(workflow_json=workflow_json)

    dataopts = {'initdir': workflow_workspace}

    try:

        check_connection_to_job_controller()
        publisher = REANAWorkflowStatusPublisher()

        with steering_ctx(dataarg=workflow_workspace,
                          dataopts=dataopts,
                          initdata=workflow_parameters if workflow_parameters
                          else {},
                          visualize=True,
                          updateinterval=5,
                          loginterval=5,
                          backend=cap_backend,
                          **workflow_kwargs) as ys:

            log.info('running workflow on context: {0}'.format(locals()))
            publisher.publish_workflow_status(workflow_uuid, 1)

            ys.adage_argument(additional_trackers=[
                REANATracker(identifier=workflow_uuid)])

        publisher.publish_workflow_status(workflow_uuid, 2)

        log.info('Workflow {workflow_uuid} finished. Files available '
                 'at {workflow_workspace}.'.format(
                     workflow_uuid=workflow_uuid,
                     workflow_workspace=workflow_workspace))
    except Exception as e:
        log.info('workflow failed: {0}'.format(e), exc_info=True)
        if publisher:
            publisher.publish_workflow_status(
                workflow_uuid, 3, logs='workflow failed: {0}'.format(e)
            )
        else:
            log.error('Workflow {workflow_uuid} failed but status '
                      'could not be published.'.format(
                          workflow_uuid=workflow_uuid))
