"""Ecflow suites."""

from deode.os_utils import deodemakedirs
from deode.suites.base import (
    EcflowSuiteFamily,
    EcflowSuiteTask,
    EcflowSuiteTrigger,
    EcflowSuiteTriggers,
    SuiteDefinition,
)


class DWAISuiteDefinition(SuiteDefinition):
    """Definition of suite."""

    def __init__(
        self,
        config,
        dry_run=False,
    ):
        """Construct the definition.

        Args:
            config (deode.ParsedConfig): Configuration file
            dry_run (bool, optional): Dry run not using ecflow. Defaults to False.

        """
        SuiteDefinition.__init__(self, config, dry_run=dry_run)

        self.config = config
        self.suite_name = config["general.case"]

        unix_group = self.platform.get_platform_value("unix_group")
        deodemakedirs(self.joboutdir, unixgroup=unix_group)

        python_template = self.platform.substitute(
            "@DEODE_HOME@/templates/ecflow/default.py"
        )

        initial_cleaning = EcflowSuiteTask(
            "PreCleaning",
            self.suite,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            ecf_files_remotely=self.ecf_files_remotely,
        )

        date_family = EcflowSuiteFamily(
            "YYYYMMDD",
            self.suite,
            self.ecf_files,
            ecf_files_remotely=self.ecf_files_remotely,
        )
        hour_family = EcflowSuiteFamily(
            "HHMM",
            date_family,
            self.ecf_files,
            ecf_files_remotely=self.ecf_files_remotely,
        )

        inputdata = EcflowSuiteFamily(
            "InputData",
            hour_family,
            self.ecf_files,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(initial_cleaning)),
            ecf_files_remotely=self.ecf_files_remotely,
        )
        inputdata_done = EcflowSuiteTriggers(EcflowSuiteTrigger(inputdata))
        prepare_cycle = EcflowSuiteTask(
            "PrepareCycle",
            inputdata,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            variables=None,
        )
        triggers = [EcflowSuiteTrigger(prepare_cycle)]

        ready_for_marsprep = EcflowSuiteTriggers(triggers)
        EcflowSuiteTask(
            "Marsprep",
            inputdata,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            variables=None,
            trigger=ready_for_marsprep,
            ecf_files_remotely=self.ecf_files_remotely,
        )

        int_fam = EcflowSuiteTask(
            name=f'{"Interpolation"}',
            parent=hour_family,
            config=config,
            task_settings=self.task_settings,
            ecf_files=self.ecf_files,
            trigger=inputdata_done,
            variables=None,
            ecf_files_remotely=self.ecf_files_remotely,
            input_template=python_template,
        )

        fa_to_zarr_task = EcflowSuiteTask(
            name="FAtoZarr",
            parent=hour_family,
            config=config,
            task_settings=self.task_settings,
            ecf_files=self.ecf_files,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(int_fam)),
            input_template=python_template,
        )

        run_model = EcflowSuiteTask(
            name="RunAIModel",
            parent=hour_family,
            config=config,
            task_settings=self.task_settings,
            ecf_files=self.ecf_files,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(fa_to_zarr_task)),
            input_template=python_template,
        )

        EcflowSuiteTask(
            "PostMortem",
            self.suite,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(run_model)),
            ecf_files_remotely=self.ecf_files_remotely,
        )
