#' Declare custom python version
#'
#' @param python Path to Python binary
#' @param required 	Is this version of Python required? If TRUE then an error
#'   occurs if it's not located. Otherwise, the version is taken as a hint only
#'   and scanning for other versions will still proceed.
#'
#' @export
use_python <- reticulate::use_python
