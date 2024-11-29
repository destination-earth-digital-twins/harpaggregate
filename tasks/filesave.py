"""Example Task."""
import os
import subprocess
from ..methods import ConfigHarpverify
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob


class Filesave(Task):
    """List a grib file."""

    def __init__(self, config):
        """Construct object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        Task.__init__(self, config, __name__)

        self.config_verif = ConfigHarpverify(self.config)
        self.binary = "python3"
        self.batch = BatchJob(os.environ)

    def execute(self):

        #Archive only at ecfs for now, all files found in ["verif"]["verif_path"]
        #Next line is unnecessary here, but is needed if everything below is moved to another task
        #Instead of reading yaml file, it generates it again but it doesn't write the output file
        config_yaml_filename,exp_args = self.config_verif.write_config_yml(write=False)
        csc = self.config_verif.csc
        case = self.config_verif.case
        print(exp_args)
        verif_path=exp_args["verif"]["verif_path"][0]
        end_date=self.config_verif.endyyyymmddhh
        harp_scripts=self.config_verif.harpscripts_home
        print(harp_scripts)
        os.chdir(harp_scripts)
        print(verif_path)
        print(case)
        print(self.config_verif.ecfs_archive_relpath)
        print(self.config_verif.huser)
        print(' copying files from' + str(os.path.join(verif_path,case))+ ' to ec:../'+self.config_verif.huser + '/'+str(os.path.join(self.config_verif.ecfs_archive_relpath,csc,case)))
        self.config_verif.replicate_structure_to_ec(os.path.join(verif_path,case),'ec:../'+self.config_verif.huser + '/'+os.path.join(self.config_verif.huser,self.config_verif.ecfs_archive_relpath,csc,case))

