#' Install fastquant from directory
#' @keywords Internal
install_fastquant_source <- function() {
  system("cd ~/.fastquant/fastquant-master; pip3 install .")
}
