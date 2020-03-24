#' Returns pricing data for a specified stock
#'
#' @param sym A string indicating the symbol of the stock in the PSE. For more
#'   details, you can refer to this [link](https://www.pesobility.com/stock).
#' @param s_date A string indicating a date in the YYYY-mm-dd format, serves
#'   as the start date of the period to get stock data
#' @param e_date A string indicating a date in the YYYY-mm-dd format, serves
#'   as the end date of the period to get stock data
#'
#' @return A tibble, with the following columns:
#' * symbol: The ticker symbol of the stock
#' * dt: The date for the closing price of the stock
#' * name: The name of the company represented by the stock ticker
#' * currency: The currency of the closing price of the stock
#' * close: The closing price of the stock at the given date, dt
#' * percent_change: The percentage day change of the stock
#' * volume: The total value of shares traded of the stock at dt
#' @md
#'
#' @importFrom dplyr tibble mutate
#' @importFrom tidyr unnest
#' @importFrom purrr map2
#' @importFrom httr GET content
#' @importFrom magrittr `%>%`
#' @export
get_pse_data <- function(sym, s_date, e_date) {

  # TODO sym should be a single character vector
  # assert_that

  # TODO Start and end dates must be in YYYY-mm-dd format
  # assert_that

  res <- tibble(symbol = sym,
                dt = seq(as.Date(s_date), as.Date(e_date), by = "days")) %>%
         mutate(data = map2(symbol, dt, get_pse_data_by_date)) %>%
         unnest(data)

  # TODO Add caching

  return(res)
}


# Utility function for getting single ticker data for symbol, date
get_pse_data_by_date <- function(symbol, date){
  req <- paste0("http://phisix-api2.appspot.com/stocks/",
                symbol, ".", date, ".json") %>%
    GET() %>%
    content(type="application/json")

  if (is.null(req)) {
    return(as.data.frame(list(name = NA_character_,
                              currency = NA_character_,
                              close = NA_real_,
                              percent_change = NA_real_,
                              volume = NA_real_)))
  } else {
    return(as.data.frame(list(name = req$stock[[1]]$name,
                              currency = req$stock[[1]]$price$currency,
                              close = req$stock[[1]]$price$amount,
                              percent_change = ifelse(
                                is.null(req$stock[[1]]$percent_change),
                                NA_real_,
                                req$stock[[1]]$percent_change),
                              volume = req$stock[[1]]$volume)))
  }
}
