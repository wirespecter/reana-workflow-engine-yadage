# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA-Workflow-Engine-yadage Celery tasks."""

from __future__ import absolute_import, print_function

import json
import logging
import os

import click
from yadage.steering_api import steering_ctx
from yadage.utils import setupbackend_fromstring

from .config import SHARED_VOLUME_PATH
from .tracker import REANATracker
from .utils import publisher

log = logging.getLogger(__name__)


def load_json(ctx, param, value):
    """Serialize click option values."""
    return json.loads(value)


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
@click.option('--workflow-parameters',
              help='JSON representation of workflow_parameters received by'
                   ' the workflow.',
              callback=load_json)
def run_yadage_workflow(workflow_uuid,
                        workflow_workspace,
                        workflow_json=None,
                        workflow_parameters=None):
    """Run a ``yadage`` workflow."""
    log.info('getting socket..')
    workflow_workspace = '{0}/{1}'.format(SHARED_VOLUME_PATH,
                                          workflow_workspace)
    # use some shared object between tasks.
    os.environ["workflow_uuid"] = workflow_uuid
    os.environ["workflow_workspace"] = workflow_workspace

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

    dataopts = {'initdir': workflow_workspace}
    try:
        with steering_ctx(dataarg=workflow_workspace,
                          dataopts=dataopts,
                          initdata=workflow_parameters if workflow_parameters
                          else {},
                          visualize=False,
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
        log.info('workflow failed: {0}'.format(e))
        publisher.publish_workflow_status(workflow_uuid, 3)
