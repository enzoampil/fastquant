#' Backtest a trading strategy
#'
#' @param data Data to be passed on to the Python backtest function
#' @param strat Character string indicating the strategy to backtest
#' @param ... Paramters to be passed on to the Python backtest function
#'
#' @importFrom rlang list2
#'
#' @export
backtest <- function(data, strat, ...) {
  kwargs <- list2(...)

  kwargs$strategy <- strat
  kwargs$data <- data

  kwargs$verbose <- FALSE
  kwargs$plot <- FALSE

  result <- do.call(what = fq$backtest, args = kwargs)
  return(paste0("Returns ", typeof(result)))

}
