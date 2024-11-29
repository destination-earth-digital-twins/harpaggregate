"""Example Task."""
import os

from ..methods import ConfigSpaveripy
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob


class LinkObs(Task):
    """List a grib file."""

    def __init__(self, config):
        """Construct object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        Task.__init__(self, config, __name__)

        self.config_verif = ConfigSpaveripy(self.config)
        self.binary = "python3"
        self.batch = BatchJob(os.environ)

    def execute(self):
        """List the content of the first found GRIB file."""
        os.chdir(self.config_verif.home)
        case = self.config_verif.write_config_case()
        exp = self.config_verif.write_config_exp()
        self.batch.run(f"{self.binary} main.py --case {case} --exp {exp} --link_obs")
