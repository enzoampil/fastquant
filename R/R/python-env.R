#' Load fastquant-env python environment, create if nonexistent
#' @keywords internal
use_env <- function() {
  if (!env_exists()) {
    reticulate::virtualenv_create("fastquant-env")
  } else {
    reticulate::use_virtualenv("fastquant-env")
  }
  invisible()
}

env_exists <- function() {
  "fastquant-env" %in% reticulate::virtualenv_list()
}
