"""Ecflow suites."""

from deode.os_utils import deodemakedirs
from deode.suites.base import (
    EcflowSuiteFamily,
    EcflowSuiteTask,
    EcflowSuiteTrigger,
    EcflowSuiteTriggers,
    SuiteDefinition,
)

from ..methods import ConfigHarpaggregate 


class HarpaggregateSuiteDefinition(SuiteDefinition):
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
        self.name = "Harp_point_verif" #config["general.case"]

        unix_group = self.platform.get_platform_value("unix_group")
        deodemakedirs(self.joboutdir, unixgroup=unix_group)

        python_template = self.platform.substitute("@DEODE_HOME@/templates/ecflow/default.py")

        self.config_verif = ConfigHarpaggregate(self.config)
        case = "Aggregate_verifications_by_CSC"

        case_family = EcflowSuiteFamily(
            case,
            self.suite,
            self.ecf_files
        )

        aggregate_scores = EcflowSuiteTask(
            "Aggregate_scores",
            case_family,
            self.config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
        )
        aggreg_archive = EcflowSuiteTask(
            "Aggreg_archive",
            case_family,
            self.config,
            self.task_settings,
            self.ecf_files,
            input_template=python_template,
            trigger=EcflowSuiteTriggers(EcflowSuiteTrigger(aggregate_scores))
        )

