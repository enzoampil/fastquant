#' Install fastquant from directory
#'
#' @keywords Internal
install_fastquant_source <- function() {
  fq_env <- reticulate::virtualenv_python("fastquant-env")
  pkgs <- system2(fq_env, c("-m", "pip", "list"), stdout = TRUE)
  if (!any(grepl("^fastquant", pkgs))) {
    system2(fq_env,
            c("-m", "pip", "install", "~/.fastquant/fastquant-master"))
  }
  invisible(pkgs)
}
