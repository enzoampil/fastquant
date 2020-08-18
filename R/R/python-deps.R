#' Check and install python dependencies
#' @keywords internal
install_python_deps <- function() {
  deps <- readr::read_lines("~/.fastquant/fastquant-master/python/requirements.txt")
  reticulate::virtualenv_install("fastquant-env", deps, ignore_installed = TRUE)
}
