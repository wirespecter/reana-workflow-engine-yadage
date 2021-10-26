# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017-2021 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REANA Workflow Engine Yadage config."""

import os
from enum import IntEnum, Enum

MOUNT_CVMFS = os.getenv("REANA_MOUNT_CVMFS", "false")

LOGGING_MODULE = "reana-workflow-engine-yadage"

WORKFLOW_TRACKING_UPDATE_INTERVAL_SECONDS = 15

LOG_INTERVAL_SECONDS = 15


# defined in reana-db component, in reana_db/models.py file as RunStatus
class RunStatus(IntEnum):
    """Enumeration of possible run statuses of a workflow."""

    created = 0
    running = 1
    finished = 2
    failed = 3
    deleted = 4
    stopped = 5
    queued = 6
    pending = 7


# defined in reana-db component, in reana_db/models.py file as JobStatus
class JobStatus(str, Enum):
    """Enumeration of job statuses.

    Example:
        JobStatus.started == "started"  # True
    """

    # FIXME: this state is not defined in reana-db but returned by r-job-controller
    started = "started"

    created = "created"
    running = "running"
    finished = "finished"
    failed = "failed"
    stopped = "stopped"
    queued = "queued"
