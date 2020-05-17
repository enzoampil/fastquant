context("Get PSE data")

df <- get_pse_data("JFC", "2018-01-01", "2018-03-31")

test_that("get_pse_data returns tibble", {
  expect_s3_class(df, "tbl_df")
  expect_s3_class(df, "tbl")
  expect_s3_class(df, "data.frame")
})
