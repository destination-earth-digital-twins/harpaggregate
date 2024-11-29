"""Example Task."""	
import os
import glob
from ..methods import ConfigHarpaggregate
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob
import subprocess

class Aggregate_config_files(Task):
    """links OBSTABLES, FCTABLES from REF and EXPS to path directory"""

    def __init__(self, config):
        """Construct object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        Task.__init__(self, config, __name__)

        self.config_verif = ConfigHarpaggregate(self.config)
        self.binary = "python3"
        self.batch = BatchJob(os.environ)


    def execute(self):
        harp_scripts=self.config_verif.harpscripts_home
        for csc in self.config_verif.cscs:
            print('csc es')
            print(csc)
            config_yaml_filename,exp_args = self.config_verif.write_config_yml(csc)
            print('Wrote config file for score aggregation of ' + csc + 'model')
            print(config_yaml_filename)
            self.batch.run(f"{harp_scripts}/verification/aggregate_scores.R -config_file {config_yaml_filename}")




