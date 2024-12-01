"""Example Task."""
import os
import glob
from ..methods import ConfigHarpaggregate
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob
import subprocess

class Aggreg_archive(Task):
    """Saves files in ecfs"""

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

        #Archive only at ecfs for now, all files found in ["verif"]["verif_path"]
        #Next line is unnecessary here, but is needed if everything below is moved to another task
        #Instead of reading yaml file, it generates it again but it doesn't write the output file

        print('harpscripts_home es')
        print(self.config_verif.harpscripts_home)
        harp_scripts=self.config_verif.harpscripts_home
        for csc in self.config_verif.cscs:
            print('csc es')
            print(csc)
            config_yaml_filename,exp_args = self.config_verif.write_config_yml(csc,write=False)
            print('Generated config file for score aggregation of ' + csc + 'model')
            print(config_yaml_filename)

            print(exp_args)
            aggregate_path=exp_args["aggregate"]["aggregation_path"]
            harp_scripts=self.config_verif.harpscripts_home
            print('origin and dest paths for saving')
            print(aggregate_path)
            print(self.config_verif.ecfs_archive_relpath)
            print(self.config_verif.huser)
            print(' copying files from ' + str(os.path.join(aggregate_path))+ ' to ec:../'+self.config_verif.huser + '/'+str(os.path.join(self.config_verif.ecfs_archive_relpath,csc)))
            self.config_verif.replicate_structure_to_ec(os.path.join(aggregate_path),'ec:../'+self.config_verif.huser + '/'+os.path.join(self.config_verif.huser,self.config_verif.ecfs_archive_relpath,csc))

