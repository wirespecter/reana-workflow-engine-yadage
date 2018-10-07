# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA-Workflow-Engine-yadage module to submit calls to RJC."""

import json
import logging

import requests
from celery import current_app

from .config import JOBCONTROLLER_HOST

log = logging.getLogger('yadage.cap.submit')


def submit(name, experiment, image, cmd, prettified_cmd):
    """Submit a job to RJC API.

    :param name: Name of the job.
    :param experiment: Experiment the job belongs to.
    :param image: Identifier of the Docker image which will run the job.
    :param cmd: String which represents the command to execute. It can be
        modified by the workflow engine i.e. prepending ``cd /some/dir/``.
    :prettified_cmd: Original command submitted by the user.
    :return: Returns the ``job_id``.
    """
    job_spec = {
        'job_name': name,
        'experiment': experiment,
        'docker_img': image,
        'cmd': cmd,
        'prettified_cmd': prettified_cmd,
        'env_vars': {},
        'workflow_workspace':
        current_app.current_worker_task.workflow_workspace,
    }

    log.info('submitting %s', json.dumps(job_spec, indent=4, sort_keys=True))

    response = requests.post(
        'http://{host}/{resource}'.format(
            host=JOBCONTROLLER_HOST,
            resource='jobs'
        ),
        json=job_spec,
        headers={'content-type': 'application/json'}
    )

    job_id = str(response.json())
    return job_id


def check_status(job_id):
    """Check the status of a given job."""
    response = requests.get(
        'http://{host}/{resource}/{id}'.format(
            host=JOBCONTROLLER_HOST,
            resource='jobs',
            id=job_id
        ),
        headers={'cache-control': 'no-cache'}
    )
    job_info = response.json()
    return job_info


def get_logs(job_id):
    """Retrieve logs for a given job."""
    response = requests.get(
        'http://{host}/{resource}/{id}/logs'.format(
            host=JOBCONTROLLER_HOST,
            resource='jobs',
            id=job_id
        ),
        headers={'cache-control': 'no-cache'}
    )

    return response.text
