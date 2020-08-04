#' Returns price data for cypto symbol through Binance API
#'
#' @param symbol A string indicating the ticker symbol of the cryptocurrency in
#'   the Binance exchange
#' @param start_date A string indicating a date in the YYYY-mm-dd format, serves
#'   as the start date of the period to get crypto data
#' @param end_date A string indicating a date in the YYYY-mm-dd format, serves
#'   as the end date of the period to get crypto data
#'
#' @return A tibble
#'
#' @importFrom httr GET content
#' @importFrom stringr str_c
#' @importFrom magrittr str_c
#'
#' @export
get_crypto_data <- function(symbol, start_date, end_date) {
  endpoint <- "https://api.binance.com/api/v3/klines?"
  start_date <- format(as.numeric(as.POSIXct(start_date)) * 1e3, scientific = FALSE)
  end_date <- format(as.numeric(as.POSIXct(end_date)) * 1e3, scientific = FALSE)

  params <- paste(stringr::str_c("symbol=", symbol),
                  "interval=1d",
                  stringr::str_c("startTime=", start_date),
                  stringr::str_c("endTime=", end_date),
                  sep = "&")
  res <- httr::GET(stringr::str_c(endpoint, params)) %>%
    httr::content("parsed")

  res
}
