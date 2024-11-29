"""ExampleMethod."""
import os
from datetime import datetime, timedelta
from dateutil import parser
import pandas as pd
import yaml
import pyproj
import glob
import subprocess
from deode.toolbox import Platform


class ConfigHarpaggregate(object):
    """description"""

    def __init__(self, config):
        """Construct base task.

        Args:
            config (deode.ParsedConfig): Configuration

        """
        self.config = config
        self.home = os.environ.get("VERIF_HOME")
        self.huser = os.environ.get("HUSER")
        self.duser= os.environ.get("DUSER")
        self.harpscripts_home=os.environ.get("HARPSCRIPTS_HOME")
        self.platform = Platform(config)      
        self.cnmexp = self.config["general.cnmexp"]
        self.csc = self.config["general.csc"]
        self.cscs = self.config["general.cscs"]
        self.cycle = self.config["general.cycle"]
        self.domain_name = self.config["domain.name"]
        self.start = self.platform.get_value("general.times.start")
        self.end = self.platform.get_value("general.times.end")
        self.startyyyymmddhh=datetime.strptime(self.start, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d%H")
        self.startyyyy=datetime.strptime(self.start, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y")
        self.startmm=datetime.strptime(self.start, "%Y-%m-%dT%H:%M:%SZ").strftime("%m")
        self.endyyyymmddhh=datetime.strptime(self.end, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d%H")
        self.cycle_length = self.platform.get_value("general.times.cycle_length")
        self.forecast_range = self.platform.get_value("general.times.forecast_range")
        self.exp = self._set_exp()
        self.case = self.platform.get_value("general.case")
        self.sqlites_exp_path=self.platform.get_value("extractsqlite.sqlite_path")
        self.sqlites_ref_path=os.environ.get("REF_SQLITES")
        self.rds_path=os.environ.get("RDS_PATH")
        self.sqlites_obs_path=os.environ.get("OBSTABLES_PATH")
        self.ref_name=os.environ.get("REF_NAME")
        self.harp_aggregation_plugin=os.environ.get("HARP_AGGREGATION_PLUGIN")
        self._case_args = None
        self._exp_args = None
        self.config_yaml = None
        self.config_yaml_filename = None
        self.ecfs_archive_relpath = os.environ.get("ECFS_ARCHIVE_RELPATH")

    def write_config_yml(self,csc,write=True):
        """descrp.

        Args:
            csc (str): Context string used to locate and name configuration files.
            write (bool): Whether to write the configuration to a file (default is True).
        """
        rds_path = os.path.join(self.rds_path,csc)
        config_template = os.path.join(self.home, "config_files/aggregate_conf.yml")
        self.config_yaml_filename = os.path.join(self.home, f"config_files/aggregate_conf_{csc}.yml")
        
        if os.path.isfile(config_template):
            # Load the template YAML configuration
            self._exp_args = ConfigHarpaggregate.load_yaml(config_template)
            # Populate fields in the aggregate section
            self._exp_args["aggregate"]["csc"] = csc
            self._exp_args["aggregate"]["ref_model"] = "Global_DT"
            self._exp_args["aggregate"]["rds_path"] = os.path.join(self.rds_path)
            
            # Read folders in rds_path and set to deode_runs
            try:
                deode_runs = [folder for folder in os.listdir(rds_path) if os.path.isdir(os.path.join(rds_path, folder))]
                self._exp_args["aggregate"]["deode_runs"] = deode_runs
            except FileNotFoundError:
                print(f"The directory {rds_path} does not exist.")
                self._exp_args["aggregate"]["deode_runs"] = []
        
            # Set aggregation path
            self._exp_args["aggregate"]["aggregation_path"] = os.path.join(self.rds_path,'AGGREGATED_SCORES', csc)
        
            # Write to the YAML file if specified
            if write:
                ConfigHarpaggregate.save_yaml(self.config_yaml_filename, self._exp_args)
                print("Wrote YAML file at " + self.config_yaml_filename)
        else:
            print("Template config file not found")
    
        return self.config_yaml_filename, self._exp_args


    def _set_exp(self):
        """

        """
        return "_".join([self.cnmexp, self.csc, self.cycle, self.domain_name])

    @staticmethod
    def link_files(source_dir, destination_dir):
        # Get all files in the source directory
        files = glob.glob(os.path.join(source_dir, "*"))
        # Ensure the destination directory exists
        if not os.path.exists(destination_dir):
           os.makedirs(destination_dir) 
	   # Link each file individually

        for file in files:
               # Get the basename of the file (i.e., the file name without the path)
               filename = os.path.basename(file)
               destination_file = os.path.join(destination_dir, filename)
               # Create a hard link for the file
               # Check if the file already exists in the destination directory
               if not os.path.exists(destination_file):
                  # Create a hard link for the file if it doesn't already exist
                  os.symlink(file, destination_file)
               else:
                  print(f"File {destination_file} already exists, skipping.")
    @staticmethod
    def load_yaml(config_file):
        with open(config_file, 'r') as stream:
             data_loaded = yaml.load(stream, Loader=yaml.SafeLoader)
        return data_loaded
    @staticmethod
    def save_yaml(config_file, data):												
        with open(config_file, "w") as stream:
             yaml.dump(data, stream, default_flow_style=False, sort_keys=False)
    @staticmethod
    def replicate_structure_to_ec(origin_path, ec_base_path):
        print('start replicate function')
        print(origin_path)
        print(ec_base_path)
        # Walk through all directories and files in the origin path
        for dirpath, dirnames, filenames in os.walk(origin_path):
            print(dirpath)
            print(dirnames)
            print(filenames)

            # Compute relative path from the origin path
            rel_dir = os.path.relpath(dirpath, origin_path)
            print('rel_dir')
            print(rel_dir)
            # Construct the target directory path on the HPC (ec:../username/)
            ec_target_dir = os.path.join(ec_base_path, rel_dir)

            # Replace local file path separators with '/' for the HPC system (if necessary)
            ec_target_dir = ec_target_dir.replace("\\", "/")  # Ensure proper path format
            print('ec_target_dir')
            print(ec_target_dir)
            # Check if the target directory already exists on the HPC
            if ( subprocess.run(["els", ec_target_dir], capture_output=True, text=True).returncode == 1 ): #check_ec_directory_exists(ec_target_dir):
                # Create the target directory on the HPC using 'emkdir'
                try:
                    subprocess.run(["emkdir", ec_target_dir], check=True)
                    print(f"Created directory: {ec_target_dir}")
                except subprocess.CalledProcessError as e:
                    print(f"Error creating directory {ec_target_dir}: {e}")
            else:
                print(f"Directory {ec_target_dir} already exists, skipping creation.")

            # Copy each file in the current directory
            for filename in filenames:
                local_file = os.path.join(dirpath, filename)
                ec_target_file = os.path.join(ec_target_dir, filename)
    
                # Use 'ecp' to copy files to the HPC
                try:
                    subprocess.run(["ecp", local_file, ec_target_file], check=True)
                    print(f"Copied file: {local_file} to {ec_target_file}")
                except subprocess.CalledProcessError as e:
                    print(f"Error copying file {local_file} to {ec_target_file}: {e}")
