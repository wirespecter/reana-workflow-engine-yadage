Changes
=======

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
