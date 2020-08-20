#' Download python repository
#'
#' @importFrom utils download.file unzip
#' @keywords internal
download_fastquant_repo <- function() {
  if (!dir.exists("~/.fastquant/") |
      !dir.exists("~/.fastquant/fastquant-master")) {
    repo_download()
  } else if (all(list.files("~/.fastquant/") == 0) |
             all(list.files("~/.fastquant/fastquant-master") == 0)) {
    repo_download()
  } else if (!"setup.py" %in% list.files("~/.fastquant/fastquant-master")) {
    repo_download()
  }

}

repo_download <- function() {
  dir.create("~/.fastquant/")
  download.file("https://github.com/enzoampil/fastquant/archive/master.zip",
                destfile = "~/.fastquant/master.zip",
                method = "auto")
  unzip(zipfile = "~/.fastquant/master.zip",
        exdir = "~/.fastquant")
  unlink("~/.fastquant/master.zip")
}
