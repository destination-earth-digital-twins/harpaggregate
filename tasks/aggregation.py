"""Example Task."""
import os
import subprocess
from ..methods import ConfigHarpaggregate
from deode.tasks.base import Task
from deode.tasks.batch import BatchJob


class Aggregation(Task):
    """List a grib file."""

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
        print('self.config_verif.home es ' + self.config_verif.home)
        #print(f"verif home es {self.config_verif.home} (clase) y {os.environ.get("VERIF_HOME")} (entorno)")
        os.chdir(self.config_verif.home)
        config_yaml_filename,exp_args = self.config_verif.write_config_yml()
        print(config_yaml_filename)
        start_date=self.config_verif.startyyyymmddhh
        end_date=self.config_verif.endyyyymmddhh
        harp_scripts=self.config_verif.harpscripts_home
        print(harp_scripts)
        os.chdir(harp_scripts)
        self.batch.run(f"{harp_scripts}/verification/point_verif.R -config_file {config_yaml_filename} -start_date {start_date} -end_date {end_date} -params_list=T2m,S10m,D10m,Pmsl,Gmax,S,T,RH,D,Pcp,CCtot")
        #self.batch.run(f"{harp_scripts}/verification/point_verif.R -config_file {config_yaml_filename} -start_date {start_date} -end_date {end_date} -params_list=T2m,S10m,D10m,Pmsl,Gmax,Pcp,CCtot")
        #print(f"verif home es {self.config_verif.home} (clase) y {os.environ.get("VERIF_HOME")} (entorno)") 

