library(httr)

get_pse_data_by_date <- function(symbol, date){
  # Gets data for a specific stock for a specific date and returns as a list
  url <- paste0("http://phisix-api2.appspot.com/stocks/", symbol, ".", date, ".json")
  url %>% httr::GET() %>% content(type="application/json") -> res
  stock <- res$stock[[1]]
  data <- list(dt = res$as_of, name = stock$name, currency = stock$price$currency,
               close = stock$price$amount, percent_change = stock$percent_change,
               volume = stock$volume, symbol = stock$symbol)
  
  return(data)
}
