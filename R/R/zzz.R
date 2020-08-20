# Global references to Python modules
pd <- NULL
plt <- NULL

# Load python dependencies
.onLoad <- function(libname, pkgname) {
  use_env()
  download_fastquant_repo()
  install_fastquant_source()
  pd <<- reticulate::import("pandas",
                           as = "pd",
                           convert = TRUE,
                           delay_load = TRUE)
  plt <<- reticulate::import("matplotlib.pyplot",
                            as = "plt",
                            convert = TRUE,
                            delay_load = TRUE)
  invisible()
}
