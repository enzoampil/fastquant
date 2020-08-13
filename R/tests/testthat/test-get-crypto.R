context("Get crypto data")

df <- get_crypto_data("BTCUSDT", "2018-01-01", "2018-03-31")

test_that("get_stock_data returns tibble", {
  expect_s3_class(df, "tbl_df")
  expect_s3_class(df, "tbl")
  expect_s3_class(df, "data.frame")
})

test_that("get_crypto_data returns correct data", {
  expect_equal(get_crypto_data("BTCUSDT", "2018-12-01", "2018-12-02")$close,
               4190.02,
               tolerance = 0.01)
  expect_equal(get_crypto_data("BTCUSDT", "2018-12-01", "2018-12-02")$volume,
               44840.07,
               tolerance = 0.01)
})
