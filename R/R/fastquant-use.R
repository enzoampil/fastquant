#' Use fastquant python repo
#' @keywords internal
use_fastquant_py <- function() {
  use_env()
  install_python_deps()
  install_fastquant_source()
  reticulate::import("fastquant")
}
