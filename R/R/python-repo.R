#' Download python repository
#'
#' @importFrom utils download.file unzip
#' @keywords internal
download_fastquant_repo <- function() {
  if (!dir.exists("~/.fastquant/")) {
    dir.create("~/.fastquant/")
    download.file("https://github.com/enzoampil/fastquant/archive/master.zip",
                  destfile = "~/.fastquant/master.zip",
                  method = "auto")
    unzip(zipfile = "~/.fastquant/master.zip",
          exdir = "~/.fastquant")
    unlink("~/.fastquant/master.zip")
  }
}
