context("Backtest")

df <- get_crypto_data("BTCUSDT", "2018-01-01", "2019-01-01")

bt <- backtest(df, "smac", fast_period = 15L, slow_period = 40L)

test_that("backtest accesses Python correctly", {
  expect_type(bt, "character")
})
