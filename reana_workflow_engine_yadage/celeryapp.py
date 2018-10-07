# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""REANA-Workflow-Engine-yadage Celery application."""

from __future__ import absolute_import

from celery import Celery

from .config import BROKER

app = Celery('tasks',
             broker=BROKER,
             include=['reana_workflow_engine_yadage.tasks'])


app.conf.update(CELERY_ACCEPT_CONTENT=['json'],
                CELERY_TASK_SERIALIZER='json')

if __name__ == '__main__':
    app.start()
