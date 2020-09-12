#' Backtest a trading strategy
#'
#' @param data Data to be passed on to the Python backtest function
#' @param strat Character string indicating the strategy to backtest
#' @param ... Paramters to be passed on to the Python backtest function
#'
#' @importFrom rlang list2
#' @importFrom assertthat assert_that
#'
#' @export
backtest <- function(data, strat, ...) {
  kwargs <- list2(...)

  if (strat == "custom") {
    assert_that(
      names(kwargs) == c("upper_limit", "lower_limit", "custom_column"),
      msg = "args for `custom` strategy must be upper_limit, lower_limit, and custom_column"
    )
    assert_that(
      is.numeric(kwargs$upper_limit) & is.numeric(kwargs$lower_limit),
      msg = "upper_limit and or lower_limit are not numeric inputs"
    )
    assert_that(
      is.character(kwargs$custom_column),
      msg = "custom_colum is not a character input"
    )
    kwargs$upper_limit <- as.double(kwargs$upper_limit)
    kwargs$lower_limit <- as.double(kwargs$lower_limit)
  }
  # TODO Exceptions for senti, multi, macd
  # TODO Coerce the rest of the arguments to integer types

  kwargs$strategy <- strat
  kwargs$data <- data

  kwargs$verbose <- FALSE
  kwargs$plot <- FALSE

  result <- do.call(what = fq$backtest, args = kwargs)
  return(paste0("Returns ", typeof(result)))

}
