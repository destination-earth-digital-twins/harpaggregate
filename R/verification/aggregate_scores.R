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

  # Loop through parameters and experiments
  for (param in params) {
    loaded_data <- list()

    for (experiment in deode_runs) {
      experiment_path <- file.path(rds_path, csc, experiment)
      pattern <- paste0("harpPointVerif.harp.", param, ".harp.*")
      matched_files <- list.files(experiment_path, pattern = pattern, full.names = TRUE)

      if (length(matched_files) > 0) {
        for (file_path in matched_files) {
          file_data <- readRDS(file_path)

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
            num_stations = sum(num_stations, na.rm = TRUE),
            .groups = "drop"
          )
      }

      # Combine aggregated data into a single list
      aggregated_data <- list(
        det_summary_scores = aggregated_summary,
        det_threshold_scores = aggregated_threshold
      )

      # Save the combined aggregated data to a single RDS file  harpPointVerif.harp.T2m.harp.20241028-20241028.harp.Global_DT.model.CY48t3_AROME_nwp_ESP_20241028_flood_20241028.rds
      output_file <- file.path(rds_aggregation_path, paste0("harpPointVerif.harp.", param, ".20241028-20241028.harp.Global_DT.model.",csc_string, ".rds"))
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

