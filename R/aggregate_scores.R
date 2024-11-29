#!/usr/bin/env Rscript

# Load required libraries
library(yaml)
library(dplyr)

# Function to load YAML configuration file
read_config <- function(config_file) {
  yaml::read_yaml(config_file)
}

# Main function to process files
process_files <- function(config_file) {
  # Read the configuration file
  config <- read_config(config_file)

  # Extract parameters from config
  params <- config$aggregate$params
  deode_runs <- config$aggregate$deode_runs
  rds_path <- config$aggregate$rds_path
  rds_aggregation_path <- config$aggregate$aggregation_path
  csc  <- config$aggregate$csc
  # CSC related string to substitute long experiment name
  csc_string <- paste0(config$aggregate$csc, "_deode")

  # Loop through parameters and experiments
  for (param in params) {
    # Initialize a list to store loaded variables for the current parameter
    loaded_data <- list()

    for (experiment in deode_runs) {
      # Construct directory path
      experiment_path <- file.path(rds_path, csc, experiment)

      # Construct file search pattern
      pattern <- paste0("harpPointVerif.harp.", param, ".harp.*")

      # Search for files matching the pattern
      matched_files <- list.files(experiment_path, pattern = pattern, full.names = TRUE)

      if (length(matched_files) > 0) {
        # Load each matched file into memory and store in the list
        for (file_path in matched_files) {
          # Load the file
          file_data <- readRDS(file_path)

          # Update fcst_model in det_summary_scores and det_threshold_scores
          for (table_name in names(file_data)) {
            #First, delete where valid_dttm is not All
            filtered_data <- file_data[[table_name]][file_data[[table_name]]$valid_dttm == "All", ]
            file_data[[table_name]] <- filtered_data

            message(sprintf("substituting %s by %s ", csc, csc_string))
            if (!is.null(file_data[[table_name]])) {
              # Extract the fcst_model column
              fcst_models <- file_data[[table_name]]$fcst_model
              # Replace any value containing csc_string with just csc_string
              file_data[[table_name]]$fcst_model <- ifelse(
                grepl(csc, fcst_models),
                csc_string,
                fcst_models
              )
            }
          }

          # Store the updated data in the list using experiment as the key
          loaded_data[[experiment]] <- file_data
          message(sprintf("Loaded and updated file for %s: %s", experiment, file_path))
        }
      } else {
        message(sprintf("No files found for %s with pattern %s in %s",
                        experiment, pattern, experiment_path))
      }
    }

    # Aggregate the data for the current parameter
    if (length(loaded_data) > 0) {
      message(sprintf("Aggregating data for parameter '%s'...", param))

      # Combine det_summary_scores across experiments
      combined_data <- do.call(rbind, lapply(loaded_data, function(x) x$det_summary_scores))
      # Remove rows with NA values in critical columns
      combined_data <- combined_data %>%
        filter(!is.na(bias) & !is.na(num_cases)) %>%
        mutate(across(c(bias, rmse, mae, stde, num_cases), as.double))

      # Compute aggregated scores
      aggregated_scores <- combined_data %>%
        group_by(fcst_model, lead_time, station_group, valid_hour,valid_dttm) %>%
        summarize(
          bias = sum(bias * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
          rmse = sum(rmse * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
          mae = sum(mae * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
          stde = sum(stde * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
	  num_cases=sum(num_cases,na.rm=TRUE),
	  num_stations=sum(num_stations,na.rm=TRUE),
          .groups = "drop"
        )

      print("aggregated scores is")
      print(aggregated_scores,n = Inf, width = Inf)
      # Save the results to an RDS file
      output_file <- file.path(rds_aggregation_path, paste0("harpPointVerif.harp.", param, "_", csc, "aggregated.rds"))
      saveRDS(aggregated_scores, output_file)
      message(sprintf("Saved aggregated data for '%s' to %s", param, output_file))
    } else {
      message(sprintf("No data loaded for parameter '%s'.", param))
    }
  }
}

# Get command-line arguments
args <- commandArgs(trailingOnly = TRUE)

# Parse the command-line arguments
config_file_path <- NULL
for (i in seq_along(args)) {
  if (args[i] == "-config_file" && (i + 1) <= length(args)) {
    config_file_path <- args[i + 1]
  }
}

# Validate the config file path
if (is.null(config_file_path)) {
  stop("Usage: script.R -config_file {path_to_yaml_file}")
}

# Process the configuration file
process_files(config_file_path)

