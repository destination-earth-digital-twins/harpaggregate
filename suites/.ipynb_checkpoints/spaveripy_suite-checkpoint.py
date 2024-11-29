"""Ecflow suites."""

from deode.os_utils import deodemakedirs
from deode.suites.base import (
    EcflowSuiteFamily,
    EcflowSuiteTask,
    EcflowSuiteTrigger,
    EcflowSuiteTriggers,
    SuiteDefinition,
)

from ..methods import ConfigSpaveripy 


class SpaveripySuiteDefinition(SuiteDefinition):
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
        self.suite_name = "spaveripy"#config["general.case"]

        unix_group = self.platform.get_platform_value("unix_group")
        deodemakedirs(self.joboutdir, unixgroup=unix_group)

        python_template = self.platform.substitute("@DEODE_HOME@/templates/ecflow/default.py")

        self.config_verif = ConfigSpaveripy(self.config)
        case = self.config_verif.case
        exp = self.config_verif.exp

        case_family = EcflowSuiteFamily(
            case,
            self.suite,
            self.ecf_files
        )

        exp_family = EcflowSuiteFamily(
            exp,
            case_family,
            self.ecf_files
        )

        linkobs = EcflowSuiteTask(
            "LinkObs",
            exp_family,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
        )

        regrid = EcflowSuiteTask(
            "Regrid",
            exp_family,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(linkobs))
        )

        plot_regrid = EcflowSuiteTask(
            "PlotRegrid",
            exp_family,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(regrid))
        )

        verif = EcflowSuiteTask(
            "Verification",
            exp_family,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(regrid))
        )

        panels = EcflowSuiteTask(
            "Panels",
            exp_family,
            config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(verif))
        )
