# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA-Workflow-Engine-yadage REANA packtivity backend."""

import logging
import os
import pipes

from packtivity.asyncbackends import ExternalAsyncProxy
from packtivity.syncbackends import (build_job, finalize_inputs, packconfig,
                                     publish)
from reana_commons.api_client import JobControllerAPIClient as RJC_API_Client

from .config import LOGGING_MODULE, MOUNT_CVMFS
from .utils import REANAWorkflowStatusPublisher

log = logging.getLogger(LOGGING_MODULE)


def get_commands(job):
    """Convert a command/script into oneliner from its job."""
    _prettified_cmd, _wrapped_cmd = None, None

    if 'command' in job:
        _prettified_cmd = job['command']
        _wrapped_cmd = 'sh -c {}  '.format(pipes.quote(job['command']))

    elif 'script' in job:
        _prettified_cmd = job['script']
        _wrapped_cmd = 'sh -c {}  '.format(pipes.quote(job['script']))

    return _prettified_cmd, _wrapped_cmd


class ReanaExternalProxy(ExternalAsyncProxy):
    """REANA yadage external proxy."""

    def details(self):
        """Parse details to json format."""
        return {
            "resultdata": self.resultdata,
            "jobproxy": self.jobproxy,
            "spec": self.spec,
            "statedata": self.statedata.json(),
            "pardata": self.pardata.json(),
        }


class ExternalBackend(object):
    """REANA yadage external packtivity backend class."""

    def __init__(self):
        """Initialize the REANA packtivity backend."""
        self.config = packconfig()
        self.rjc_api_client = RJC_API_Client('reana-job-controller')

        self._fail_info = None

    def submit(self, spec, parameters, state, metadata):
        """Submit a yadage packtivity to RJC."""
        parameters, state = finalize_inputs(parameters, state)
        job = build_job(spec['process'], parameters, state, self.config)

        prettified_cmd, wrapped_cmd = get_commands(job)

        image = spec['environment']['image']
        # tag = spec['environment']['imagetag']

        kerberos = False
        compute_backend = None
        resources = spec['environment'].get('resources', None)
        if resources:
            for item in resources:
                if 'kerberos' in item.keys():
                    kerberos = item['kerberos']
                if 'compute_backend' in item.keys():
                    compute_backend = item['compute_backend']

        log.info('state context is {0}'.format(state))
        log.info('would run job {0}'.format(job))

        state.ensure()

        log.info('submitting!')

        workflow_uuid = os.getenv('workflow_uuid', 'default')
        job_request_body = {
            'workflow_uuid': workflow_uuid,
            'experiment': os.getenv('REANA_WORKFLOW_ENGINE_YADAGE_EXPERIMENT',
                                    'default'),
            'image': image,
            'cmd': wrapped_cmd,
            'prettified_cmd': prettified_cmd,
            'workflow_workspace': os.getenv('workflow_workspace', 'default'),
            'job_name': metadata['name'],
            'cvmfs_mounts': MOUNT_CVMFS,
        }

        if compute_backend:
            job_request_body['compute_backend'] = compute_backend
        if kerberos:
            job_request_body['kerberos'] = kerberos

        job_id = self.rjc_api_client.submit(**job_request_body)

        log.info('submitted job:{0}'.format(job_id))
        message = {"job_id": str(job_id)}
        workflow_uuid = os.getenv('workflow_uuid', 'default')
        status_running = 1
        try:
            publisher = REANAWorkflowStatusPublisher()
            publisher.publish_workflow_status(
                workflow_uuid, status_running,
                message=message)
        except Exception as e:
            log.info('Status: workflow - {workflow_uuid} '
                     'status - {status} message - {message}'.format(
                         workflow_uuid=workflow_uuid,
                         status=status_running,
                         message=message
                     ))
            log.info('workflow status publish failed: {0}'.format(e))

        return ReanaExternalProxy(
            jobproxy=job_id,
            spec=spec,
            pardata=parameters,
            statedata=state
        )

    def result(self, resultproxy):
        """Retrieve the result of a packtivity run by RJC."""
        resultproxy.pardata, resultproxy.statedata \
            = finalize_inputs(resultproxy.pardata, resultproxy.statedata)

        return publish(
            resultproxy.spec['publisher'],
            resultproxy.pardata, resultproxy.statedata, self.config
        )

    def _get_state(self, resultproxy):
        """Get the packtivity state."""
        status_res = self.rjc_api_client.check_status(
            resultproxy.jobproxy['job_id'])
        return status_res['status']

    def ready(self, resultproxy):
        """Check if a packtivity is finished."""
        return self._get_state(resultproxy) != 'started'

    def successful(self, resultproxy):
        """Check if the packtivity was successful."""
        return self._get_state(resultproxy) == 'succeeded'

    def fail_info(self, resultproxy):
        """Retrieve the fail info."""
        self._fail_info += "\nraw info: {}".format(resultproxy)
        return self._fail_info
