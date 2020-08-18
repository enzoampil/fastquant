#' Install fastquant from directory
#'
#' @keywords Internal
install_fastquant_source <- function() {
  handler <- tryCatch(
    {
      system("cd ~/.fastquant/fastquant-master; sudo pip install .")
    },
    warning = function(cond) {
      message("pip does not exist. Using pip3 . . .")
      system("cd ~/.fastquant/fastquant-master; sudo pip3 install .")
    }
  )
  return(handler)
}
