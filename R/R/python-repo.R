#' Download python repository
#'
#' @importFrom utils download.file unzip
#' @keywords internal
download_fastquant_repo <- function() {
  download.file("https://github.com/enzoampil/fastquant/archive/master.zip",
                destfile = "~/.fastquant/fastquant.zip",
                method = "curl")
  unzip(zipfile = "~/.fastquant/fastquant.zip",
        exdir = "~/.fastquant/fastquant")
}
