#' Returns pricing data for a specified stock
#'
#' @param symbol A string indicating the symbol of the stock in the PSE and Yahoo
#'   Finance. For more details, you can refer to this
#'   [link](https://www.pesobility.com/stock).
#' @param start_date A string indicating a date in the YYYY-mm-dd format, serves
#'   as the start date of the period to get stock data
#' @param end_date A string indicating a date in the YYYY-mm-dd format, serves
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
#' @examples
#' \donttest{
#'   get_stock_data("JFC", "2019-01-03", "2019-02-01") # PSE data
#'   get_stock_data("MSFT", "2019-01-03", "2019-02-01") # US data
#' }
#'
#' @importFrom lubridate parse_date_time
#' @importFrom assertthat assert_that
#' @importFrom dplyr tibble mutate filter rename_with
#' @importFrom tidyr unnest
#' @importFrom purrr map2
#' @importFrom httr GET content
#' @importFrom magrittr `%>%`
#' @importFrom quantmod loadSymbols
#' @importFrom tibble rownames_to_column
#' @importFrom stringr str_replace
#' @export
get_stock_data <- function(symbol, start_date, end_date) {

  assert_that(is.character(symbol),
              msg = "`symbol` must be character")

  assert_that(length(symbol) == 1,
              msg = "`symbol` must be length 1")

  assert_that(!is.na(parse_date_time(start_date, orders = "ymd")),
              msg = "start_date is not in YYYY-mm-dd format")

  assert_that(!is.na(parse_date_time(end_date, orders = "ymd")),
              msg = "end_date is not in YYYY-mm-dd format")

  # TODO Check /data if the symbol exists as a file
  # TODO Check /data if the symbol exists for the time frame
  # TODO Cut relevant rows from dataset
  # TODO Change start_date and end_date as applicable

  dt <- seq(as.Date(start_date), as.Date(end_date), by = "days")

  data <- NULL

  name <- NULL

  res <- tibble(symbol = symbol,
                dt = dt) %>%
         mutate(data = map2(symbol, dt, get_stock_data_by_date)) %>%
         unnest(data) %>%
         filter(!is.na(name))
  return(res)
}


# Utility function for getting single ticker data for symbol, date
get_stock_data_by_date <- function(symbol, date){
  if (!is.null(paste0("http://1.phisix-api.appspot.com/stocks/",
               symbol, ".", date, ".json") %>%
               GET() %>%
               content(type="application/json"))) {

    req <- paste0("http://1.phisix-api.appspot.com/stocks/",
                  symbol, ".", date, ".json") %>%
      GET() %>%
      content(type="application/json")

    return(as.data.frame(list(name = req$stock[[1]]$name,
                              currency = req$stock[[1]]$price$currency,
                              close = req$stock[[1]]$price$amount,
                              percent_change = ifelse(
                                is.null(req$stock[[1]]$percent_change),
                                NA_real_,
                                req$stock[[1]]$percent_change),
                              volume = req$stock[[1]]$volume)))

  } else if (!is.null(paste0("http://phisix-api.appspot.com/stocks/",
                      symbol, ".", date, ".json") %>%
                      GET() %>%
                      content(type="application/json"))) {

    req <- paste0("http://phisix-api.appspot.com/stocks/",
                  symbol, ".", date, ".json") %>%
      GET() %>%
      content(type="application/json")

    return(as.data.frame(list(name = req$stock[[1]]$name,
                              currency = req$stock[[1]]$price$currency,
                              close = req$stock[[1]]$price$amount,
                              percent_change = ifelse(
                                is.null(req$stock[[1]]$percent_change),
                                NA_real_,
                                req$stock[[1]]$percent_change),
                              volume = req$stock[[1]]$volume)))

  } else if (loadSymbols(symbol, env = NULL, from = date)[1] %>%
             as.data.frame() %>%
             rownames_to_column() %>%
             `$`("rowname") == date) {

    prereq <- loadSymbols(symbol, env = NULL, from = date)[1] %>%
      as.data.frame() %>%
      rownames_to_column() %>%
      rename_with(~str_replace(., "^.*\\.(.*)$", "\\1"))

    return(as.data.frame(list(name = symbol,
                              currency = "FX",
                              close = prereq$Close,
                              percent_change = NA_real_,
                              volume = prereq$Volume)))

  } else {
    return(as.data.frame(list(name = NA_character_,
                              currency = NA_character_,
                              close = NA_real_,
                              percent_change = NA_real_,
                              volume = NA_real_)))
  }
}
