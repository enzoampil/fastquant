context("Get PSE data")

df <- get_stock_data("JFC", "2018-01-01", "2018-03-31")

test_that("get_stock_data returns tibble", {
  expect_s3_class(df, "tbl_df")
  expect_s3_class(df, "tbl")
  expect_s3_class(df, "data.frame")
})

test_that("get_stock_data returns correct data", {
  expect_equal(get_stock_data("JFC", "2019-01-03", "2019-01-03")$close, 292)
  expect_equal(get_stock_data("JFC", "2019-01-03", "2019-01-03")$volume, 1665440)
})
