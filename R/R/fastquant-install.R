#' Install fastquant from directory
#'
#' @keywords Internal
install_fastquant_source <- function() {
  handler <- tryCatch(
    {
    system("cd ~/.fastquant/fastquant-master; pip3 install .")
    },
    warning = function(cond) {
      message("pip3 does not exist. Using pip . . .")
      system("cd ~/.fastquant/fastquant-master; pip install .")
    }
  )
  return(handler)
}
