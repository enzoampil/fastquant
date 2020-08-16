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
#' @importFrom magrittr `%>%`
#' @importFrom dplyr mutate select
#' @importFrom purrr map_dbl map_chr
#'
#' @export
get_crypto_data <- function(symbol, start_date, end_date) {
  endpoint <- "https://api.binance.com/api/v3/klines?"
  s_date <- format(as.numeric(as.POSIXct(start_date)) * 1e3, scientific = FALSE)
  e_date <- format(as.numeric(as.POSIXct(end_date)) * 1e3, scientific = FALSE)

  params <- paste(stringr::str_c("symbol=", symbol),
                  "interval=1d",
                  stringr::str_c("startTime=", s_date),
                  stringr::str_c("endTime=", e_date),
                  sep = "&")
  res <- httr::GET(stringr::str_c(endpoint, params)) %>%
    httr::content("parsed")

  x <- NULL

  tibble(x = res) %>%
    mutate(dt = map_chr(x, function(x) as.character(as.Date(as.POSIXct(as.numeric(x[[1]]) / 1e3,
                                                                       origin="1970-01-01")))),
           open = map_dbl(x, function(x) as.numeric(x[[2]])),
           high = map_dbl(x, function(x) as.numeric(x[[3]])),
           low = map_dbl(x, function(x) as.numeric(x[[4]])),
           close = map_dbl(x, function(x) as.numeric(x[[5]])),
           volume = map_dbl(x, function(x) as.numeric(x[[6]]))) %>%
    select(-x)
}
