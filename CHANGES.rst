Changes
=======

Version 0.9.0 (UNRELEASED)
---------------------------

- Adds support for Rucio
- Adds support for propagating global Kerberos flag from workflow specification to each job.
- Adds support for specifying ``slurm_partition`` and ``slurm_time`` for Slurm compute backend jobs.

Version 0.8.2 (2022-02-08)
---------------------------

- Changes dependencies to solve compatibility issues with ``Yadage 0.20.2`` version.

Version 0.8.1 (2022-02-07)
---------------------------

- Adds support for specifying ``kubernetes_job_timeout`` for Kubernetes compute backend jobs.
- Fixes workflow stuck in pending status due to early Yadage fail.

Version 0.8.0 (2021-11-22)
---------------------------

- Adds users quota accounting.
- Changes workflow specification loading to be done in ``reana-commons``.
- Changes workflow engine to reduce the number of API calls to REANA-Job-Controller.
- Changes workflow engine to remove duplicated messages to the job status message queue.

Version 0.7.5 (2021-07-05)
--------------------------

- Changes internal dependencies to remove click.

Version 0.7.4 (2021-04-28)
--------------------------

- Adds support for specifying ``kubernetes_memory_limit`` for Kubernetes compute backend jobs.

Version 0.7.3 (2021-03-17)
--------------------------

- Changes workflow engine instantiation to use central REANA-Commons factory.
- Changes job command strings by removing interpreter when possible and using central REANA-Commons job command serialisation.

Version 0.7.2 (2021-02-03)
--------------------------

- Fixes minor code warnings.
- Changes CI system to include Python flake8 and Dockerfile hadolint checkers.

Version 0.7.1 (2020-11-10)
--------------------------

- Adds support for specifying ``htcondor_max_runtime`` and ``htcondor_accounting_group`` for HTCondor compute backend jobs.
- Fixes restarting of Yadage workflows.

Version 0.7.0 (2020-10-20)
--------------------------

- Adds creation of workflow visualisation graph by default when a workflow runs.
- Adds option to specify unpacked Docker images as workflow step requirement.
- Adds handling of workflow specification load logic that was done before in ``reana-client``.
- Adds support for VOMS proxy as a new authentication method.
- Adds support for ``initfiles`` operational option.
- Adds pinning of all Python dependencies allowing to easily rebuild component images at later times.
- Changes Yadage workflow engine to version 0.20.1.
- Changes base image to use Python 3.8.
- Changes code formatting to respect ``black`` coding style.
- Changes documentation to single-page layout.

Version 0.6.1 (2020-05-25)
--------------------------

- Upgrades REANA-Commons package using latest Kubernetes Python client version.

Version 0.6.0 (2019-12-20)
--------------------------

- Allows to specify compute backend (HTCondor, Kubernetes or Slurm) and
  Kerberos authentication requirement for Yadage workflow jobs.
- Upgrades Python to 3.6.
- Upgrades Yadage to 0.20.0.
- Upgrades Packtivity to 0.14.21.
- Sets default umask 002 for jobs writing to the workflow workspace.
- Allows setting UID for the job container runtime user.
- Moves workflow engine to the same Kubernetes pod with the REANA-Job-Controller
  (sidecar pattern).

Version 0.5.0 (2019-04-23)
--------------------------

- Makes workflow engine independent of Celery so that independent workflow
  instances are created on demand for each user.
- Centralises the initialisation of ``WorkflowStatusPublisher``.
- Introduces CVMFS mounts in job specifications.
- Makes docker image slimmer by using ``python:2.7-slim``.
- Centralises log level and log format configuration.

Version 0.4.0 (2018-11-06)
--------------------------

- Improves AMQP re-connection handling. Switches from ``pika`` to ``kombu``.
- Utilises common openapi client for communication with REANA-Job-Controller.
- Changes license to MIT.

Version 0.3.1 (2018-09-07)
--------------------------

- Pins REANA-Commons and Celery dependencies.

Version 0.3.0 (2018-08-10)
--------------------------

- Tracks workflow progress.

Version 0.2.0 (2018-04-19)
--------------------------

- Upgrades Yadage workflow ecosystem versions (Yadage 0.13, Packtivity 0.10).
- Adds logs to the workflow models in the database.

Version 0.1.0 (2018-01-30)
--------------------------

- Initial public release.

.. admonition:: Please beware

   Please note that REANA is in an early alpha stage of its development. The
   developer preview releases are meant for early adopters and testers. Please
   don't rely on released versions for any production purposes yet.
