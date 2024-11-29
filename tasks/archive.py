"""Example Task."""
import os
import subprocess
from ..methods import ConfigHarpverify
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob


class Archive(Task):
    """List a grib file."""

    def __init__(self, config):
        """Construct object.

        Args:
            config (deode.ParsedConfig): Configuration
        """
        Task.__init__(self, config, __name__)

        self.config_verif = ConfigHarpverify(self.config)
        self.binary = "R"
        self.batch = BatchJob(os.environ)

    def execute(self):
        print('self.config_verif.home es ' + self.config_verif.home)
        os.chdir(self.config_verif.home)
        config_yaml_filename,exp_args = self.config_verif.write_config_yml()
        print(config_yaml_filename)
        start_date=self.config_verif.startyyyymmddhh
        end_date=self.config_verif.endyyyymmddhh
        harp_scripts=self.config_verif.harpscripts_home
        print(harp_scripts)
        os.chdir(harp_scripts)
        #self.batch.run(f"{harp_scripts}/verification/point_verif.R -config_file {config_yaml_filename} -start_date {start_date} -end_date {end_date} -params_list=T2m,S10m,D10m,CCtot,Pmsl,Gmax,S,T,RH,D,Pcp")
        self.batch.run(f"{harp_scripts}/verification/point_verif.R -config_file {config_yaml_filename} -start_date {start_date} -end_date {end_date} -params_list=T2m")

        #Archive only at ecfs for now, all files found in ["verif"]["verif_path"]
        #Next line is unnecessary here, but is needed if everything below is moved to another task
        #Instead of reading yaml file, it generates it again but it doesn't write the output file
        config_yaml_filename,exp_args = self.config_verif.write_config_yml(write=False)
        print(exp_args)
        verif_path=exp_args["verif"]["verif_path"]
        end_date=self.config_verif.endyyyymmddhh
        harp_scripts=self.config_verif.harpscripts_home
        print(harp_scripts)
        os.chdir(harp_scripts)
        print(' copying files from' + str(verif_path) + ' to ' + self.config_verif.ecfs_archive)
        self.config_verif.replicate_structure_to_ec(verif_path[0],self.config_verif.ecfs_archive)

