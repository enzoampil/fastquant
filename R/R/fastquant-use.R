#' Import fastquant python module
#'
#' Access backtesting functionality in R using the Python package. R does not
#' have native support for backtesting according to the backtrader framework.
#'
#' @return A Python module object
#' @import reticulate import
#'
#' @export
use_fastquant_py <- function() {
  import("fastquant", delay_load = TRUE)
}
