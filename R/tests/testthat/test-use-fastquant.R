context("Port functionality from Python")

py_fq <- use_fastquant_py()

test_that("use_fastquant_py returns python module object", {
  expect_s3_class(py_fq, "python.builtin.module")
  expect_s3_class(py_fq, "python.builtin.object")
})
