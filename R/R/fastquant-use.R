#' Import fastquant python module
#'
#' Access backtesting functionality in R using the Python package. R does not
#' have native support for backtesting according to the backtrader framework.
#'
#' @return A Python module object
#'
#' @export
use_fastquant_py <- function() {
  use_env()
  download_fastquant_repo()
  install_python_deps()
  install_fastquant_source()
  reticulate::import("fastquant")
}
