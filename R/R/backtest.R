#' Backtest a trading strategy
#'
#' @param data Data to be passed on to the Python backtest function
#' @param strat Character string indicating the strategy to backtest
#' @param ... Paramters to be passed on to the Python backtest function
#'
#' @importFrom rlang list2 warn
#' @importFrom assertthat assert_that
#'
#' @export
backtest <- function(data, strat, verbose = FALSE, plot = FALSE, ...) {
  kwargs <- list2(...)

  if (strat == "custom" & length(kwargs) != 0) {
    assert_that(
      names(kwargs) %in% c("upper_limit", "lower_limit", "custom_column"),
      msg = "args for `custom` strategy must be either upper_limit, lower_limit,
             or custom_column"
    )
    if ("custom_column" %in% names(kwargs)) {
      assert_that(
        is.character(kwargs$custom_column),
        msg = "custom_colum is not a character input"
      )
    }
    if ("upper_limit" %in% names(kwargs)) {
      assert_that(
        is.numeric(kwargs$upper_limit),
        msg = "upper_limit is not numeric"
      )
      kwargs$upper_limit <- as.double(kwargs$upper_limit)
    }
    if ("lower_limit" %in% names(kwargs)) {
      assert_that(
        is.numeric(kwargs$lower_limit),
        msg = "lower_limit is not numeric"
      )
      kwargs$lower_limit <- as.double(kwargs$lower_limit)
    }
  }

  if (strat == "macd") {
    assert_that(
      names(kwargs) %in% c("fast_period", "slow_period", "signal_period", "allowance"),
      msg = "args for `macd` strategy must be either fast_period, slow_period,
             signal_period, or allowance",
      warn("Coercing fast_period, slow_period, and signal_period to integers. `1.2` will become `1L`")
    )
    if ("fast_period" %in% names(kwargs)) {
      assert_that(is.numeric(kwargs$fast_period),
                  msg = "fast_period should be numeric")
      kwargs$fast_period <- as.integer(kwargs$fast_period)
    }
    if ("slow_period" %in% names(kwargs)) {
      assert_that(is.numeric(kwargs$slow_period),
                  msg = "slow_period should be numeric")
      kwargs$slow_period <- as.integer(kwargs$slow_period)
    }
    if ("signal_period" %in% names(kwargs)) {
      assert_that(is.numeric(kwargs$signal_period),
                  msg = "signal_period should be numeric")
      kwargs$signal_period <- as.integer(kwargs$signal_period)
    }
    if ("allowance" %in% names(kwargs)) {
      assert_that(is.numeric(kwargs$allowance),
                  msg = "allowance should be numeric")
      kwargs$allowance <- as.double(kwargs$allowance)
    }
  }

  if (strat == "senti") {
    assert_that(
      names(kwargs) == c("senti"),
      msg = "arg for `senti` strategy should be `senti`"
    )
    assert_that(
      is.numeric(kwargs$senti),
      msg = "senti should be numeric"
    )
    kwargs$senti <- as.double(kwargs$senti)
  }

  if (strat == "ternary") {
    assert_that(
      names(kwargs) %in% c("buy_int", "sell_int", "custom_column"),
      msg = "args for `ternary` must be either buy_int, sell_int or custom_column"
    )
    if ("custom_column" %in% names(kwargs)) {
      assert_that(
        is.character(kwargs$custom_column),
        msg = "custom_column must be character"
      )
    }
    if (c("buy_int", "sell_int") %in% names(kwargs)) {
      warn("Coercing buy_int and sell_int to integers. `1.2` will become `1L`")
      assert_that(
          is.numeric(kwargs$buy_int) &
          is.numeric(kwargs$sell_int),
          msg = "buy_int and sell_int must be numeric"
      )
      kwargs$buy_int <- as.integer(kwargs$buy_int)
      kwargs$sell_int <- as.integer(kwargs$sell_int)
    }
  }

  if (strat == "multi") {
    assert_that(
      names(kwargs) %in% "strats",
      msg = "multi does not contain strats"
    )
    assert_that(
      typeof(kwargs$strats) == "list",
      msg = "multi must be list"
    )
  }

  if (!strat %in% c("custom", "macd", "senti", "ternary")) {
    kwargs <- lapply(kwargs, as.integer)
  }

  kwargs$strategy <- strat
  kwargs$data <- data

  # R defaults to having these values as FALSE, export to methods
  kwargs$verbose <- verbose
  kwargs$plot <- plot

  result <- do.call(what = fq$backtest, args = kwargs)
  return(paste0("Returns ", typeof(result)))

}
