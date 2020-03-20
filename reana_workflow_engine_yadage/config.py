# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REANA Workflow Engine Yadage config."""

import os

MOUNT_CVMFS = os.getenv('REANA_MOUNT_CVMFS', 'false')

LOGGING_MODULE = 'reana-workflow-engine-yadage'
"""REANA Workflow Engine Yadage logging module."""
