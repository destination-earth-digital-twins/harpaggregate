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
  csc_string <- paste0(config$aggregate$csc, "_deode")
  ref_model <- config$aggregate$ref_model
  # Loop through parameters and experiments
  for (param in params) {
    loaded_data <- list()
    combined_stations <- vector()
    combined_dttm <- vector()
    file_attributes <- list()

    for (experiment in deode_runs) {
      experiment_path <- file.path(rds_path, csc, experiment)
      pattern <- paste0("harpPointVerif.harp.", param, ".harp.*")
      matched_files <- list.files(experiment_path, pattern = pattern, full.names = TRUE)

      if (length(matched_files) > 0) {
        for (file_path in matched_files) {
          file_data <- readRDS(file_path)

          # Collect attributes
          if (is.null(file_attributes$class)) {
            file_attributes$class <- attr(file_data, "class")
          }
          if (is.null(file_attributes$parameter)) {
            file_attributes$parameter <- attr(file_data, "parameter")
          }
          if (is.null(file_attributes$group_vars)) {
            file_attributes$group_vars <- attr(file_data, "group_vars")
          }
          if (is.null(file_attributes$par_unit)) {
            file_attributes$par_unit <- attr(file_data, "par_unit")
          }

          # Aggregate stations and dttm
          combined_stations <- unique(c(combined_stations, attr(file_data, "stations")))
          combined_dttm <- unique(c(combined_dttm, attr(file_data, "dttm")))

          # Process det_summary_scores and det_threshold_scores
          for (table_name in names(file_data)) {
            filtered_data <- file_data[[table_name]][file_data[[table_name]]$valid_dttm == "All", ]
            file_data[[table_name]] <- filtered_data

            if (!is.null(file_data[[table_name]])) {
              fcst_models <- file_data[[table_name]]$fcst_model
              file_data[[table_name]]$fcst_model <- ifelse(
                grepl(csc, fcst_models),
                csc_string,
                fcst_models
              )
            }
          }

          loaded_data[[experiment]] <- file_data
          message(sprintf("Loaded and updated file for %s: %s", experiment, file_path))
        }
      } else {
        message(sprintf("No files found for %s with pattern %s in %s", experiment, pattern, experiment_path))
      }
    }

    if (length(loaded_data) > 0) {
      # Aggregate det_summary_scores
      combined_summary <- do.call(rbind, lapply(loaded_data, function(x) x$det_summary_scores))
      combined_summary <- combined_summary %>%
        filter(!is.na(bias) & !is.na(num_cases)) %>%
        mutate(across(c(bias, rmse, mae, stde, num_cases), as.double))

      aggregated_summary <- combined_summary %>%
        group_by(fcst_model, lead_time, station_group, valid_hour, valid_dttm) %>%
        summarize(
          bias = sum(bias * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
          rmse = sum(rmse * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
          mae = sum(mae * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
          stde = sum(stde * num_cases, na.rm = TRUE) / sum(num_cases, na.rm = TRUE),
          num_cases = sum(num_cases, na.rm = TRUE),
          num_stations = sum(num_stations, na.rm = TRUE),
          .groups = "drop"
        )

      # Aggregate det_threshold_scores
      combined_threshold <- do.call(rbind, lapply(loaded_data, function(x) {
        if (!is.null(x$det_threshold_scores)) {
          x$det_threshold_scores
        } else {
          NULL
        }
      }))

      aggregated_threshold <- NULL
      if (!is.null(combined_threshold) && nrow(combined_threshold) > 0) {
        combined_threshold <- combined_threshold %>%
          mutate(across(where(is.numeric), as.double)) %>%
          select(-cont_tab) %>%
          filter(!is.na(num_cases_for_threshold_total))

        aggregated_threshold <- combined_threshold %>%
          group_by(fcst_model, lead_time, station_group, threshold) %>%
          summarize(
            across(where(is.numeric), ~ sum(. * num_cases_for_threshold_total, na.rm = TRUE) / sum(num_cases_for_threshold_total, na.rm = TRUE)),
            num_cases_for_threshold_total = sum(num_cases_for_threshold_total, na.rm = TRUE),
	    num_cases_for_threshold_observed = sum(num_cases_for_threshold_observed, na.rm = TRUE),
            num_cases_for_threshold_forecasted = sum(num_cases_for_threshold_forecast, na.rm = TRUE),
            num_stations = sum(num_stations, na.rm = TRUE),
            .groups = "drop"
          )
      }

      # Combine aggregated data into a single list
      aggregated_data <- list(
        det_summary_scores = aggregated_summary,
        det_threshold_scores = aggregated_threshold
      )

      # Assign attributes to the aggregated data
      attr(aggregated_data, "class") <- file_attributes$class
      attr(aggregated_data, "parameter") <- file_attributes$parameter
      attr(aggregated_data, "group_vars") <- file_attributes$group_vars
      attr(aggregated_data, "par_unit") <- file_attributes$par_unit
      attr(aggregated_data, "stations") <- combined_stations
      attr(aggregated_data, "dttm") <- combined_dttm

      # Save the combined aggregated data to a single RDS file
      # Access the 'dttm' attribute to find the max and min values to use in the filename
      dttm_values <- attr(aggregated_data, "dttm")
      # Find  the minimum and maximum values
      min_dttm <- min(dttm_values)
      max_dttm <- max(dttm_values)
      output_file <- file.path(rds_aggregation_path, paste0("harpPointVerif.harp.", param, ".harp.",as.character(min_dttm),"-",as.character(max_dttm),".harp.", ref_model, ".model.", csc_string, ".rds"))
      #Delete det_threshold_scores table until debugging
      aggregated_data$det_threshold_scores  <- NULL
      saveRDS(aggregated_data, output_file)
      message(sprintf("Saved aggregated data for '%s' to %s", param, output_file))
    } else {
      message(sprintf("No data loaded for parameter '%s'.", param))
    }
  }
}

# Get command-line arguments
args <- commandArgs(trailingOnly = TRUE)
config_file_path <- NULL
for (i in seq_along(args)) {
  if (args[i] == "-config_file" && (i + 1) <= length(args)) {
    config_file_path <- args[i + 1]
  }
}

if (is.null(config_file_path)) {
  stop("Usage: script.R -config_file {path_to_yaml_file}")
}

process_files(config_file_path)

