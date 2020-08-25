#' Backtest a trading strategy
#'
#' @param data Data to be passed on to the Python backtest function
#' @param strat Character string indicating the strategy to backtest
#' @param ... Paramters to be passed on to the Python backtest function
#'
#' @export
backtest <- function(data, strat, ...) {

  result <- fq$backtest(strat, data, ...)
  return(paste0("Returns ", typeof(result)))

}
