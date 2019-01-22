# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA-Workflow-Engine-yadage workflow state tracker."""

import ast
import datetime
import json
import logging

import adage.dagstate as dagstate
import adage.nodestate as nodestate
import jq
import networkx as nx
from yadage.utils import WithJsonRefEncoder

from .utils import REANAWorkflowStatusPublisher

log = logging.getLogger(__name__)


def analyze_progress(adageobj):
    """Analyze the workflow progress."""
    dag, rules, applied = adageobj.dag, adageobj.rules, adageobj.applied_rules
    successful, failed, running, unsubmittable = 0, 0, 0, 0

    nodestates = []
    for node in nx.topological_sort(dag):
        nodeobj = dag.getNode(node)
        is_pure_publishing = nodeobj.task.metadata['wflow_hints'].get(
            'is_purepub', False)
        if is_pure_publishing:
            continue
        if nodeobj.state == nodestate.RUNNING:
            nodestates.append(
                {'state': 'running', 'job_id': nodeobj.resultproxy.job_id}
            )
        elif dagstate.node_status(nodeobj):
            nodestates.append(
                {'state': 'succeeded', 'job_id': nodeobj.resultproxy.job_id}
            )
        elif dagstate.node_ran_and_failed(nodeobj):
            nodestates.append(
                {'state': 'failed', 'job_id': nodeobj.resultproxy.job_id}
            )
        elif dagstate.upstream_failure(dag, nodeobj):
            nodestates.append(
                {'state': 'unsubmittable', 'job_id': None}
            )
        else:
            nodestates.append(
                {'state': 'scheduled', 'job_id': None}
            )
    return nodestates


class REANATracker(object):
    """REANA specific progress tracker."""

    def __init__(self, identifier=None):
        """Build the tracker object."""
        self.workflow_id = identifier
        log.info('initializing REANA workflow tracker for id {}'.format(
            self.workflow_id))

    def initialize(self, adageobj):
        """Initialize the progress tracker."""
        self.track(adageobj)

    def track(self, adageobj):
        """Tracks progress."""
        log.info('sending progress information')
        serialized = json.dumps(adageobj.json(), cls=WithJsonRefEncoder,
                                sort_keys=True)
        purejson = json.loads(serialized)

        progress = {
            "engine_specific": None,
            "failed": {"total": 0, "job_ids": []},
            "total": {"total": 0, "job_ids": []},
            "running": {"total": 0, "job_ids": []},
            "finished": {"total": 0, "job_ids": []}
        }

        progress['engine_specific'] = jq.jq('{dag: {edges: .dag.edges, nodes: \
        [.dag.nodes[]|{metadata: {name: .task.metadata.name}, id: .id, \
        jobid: .proxy.proxydetails.job_id}]}}').transform(purejson)

        for node in analyze_progress(adageobj):
            key = {
                'running': 'running',
                'succeeded': 'finished',
                'failed': 'failed',
                'unsubmittable': 'planned',
                'scheduled': 'total',
            }[node['state']]
            progress[key]['total'] += 1
            if isinstance(node['job_id'], str):
                job_id_dict = ast.literal_eval(node['job_id'])
                job_id = job_id_dict['job_id']
                if key in ['running', 'finished', 'failed']:
                    progress[key]['job_ids'].append(job_id)

        log_message = 'this is a tracking log at {}'.format(
            datetime.datetime.now().isoformat()
        )

        log.info('''sending to REANA
                    uuid: {}
                    json:
                    {}
                    message:
                    {}
                    '''.format(self.workflow_id,
                               json.dumps(progress, indent=4), log_message))
        publisher = REANAWorkflowStatusPublisher()
        publisher.publish_workflow_status(
            self.workflow_id, status=1, logs=log_message,
            message={"progress": progress})

    def finalize(self, adageobj):
        """Finilizes the progress tracking."""
        self.track(adageobj)
