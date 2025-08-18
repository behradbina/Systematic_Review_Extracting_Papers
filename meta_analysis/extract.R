install.packages("devtools")
install.packages("shiny")
install.packages("usethis")


install.packages('magick')
install.packages('curl')
install.packages("metaDigitise")

library(metaDigitise)

library(devtools)

devtools::install_github("EIvimeyCook/ShinyDigitise")
devtools::install_github("joelpick/metaDigitise")


library(shinyDigitise)
shinyDigitise()