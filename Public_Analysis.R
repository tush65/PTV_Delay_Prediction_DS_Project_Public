library(lubridate)
library(dplyr)

setwd("/Users/tusharkambangudi/Desktop/Data Science PTV Delays Summer Project")

getwd()

file = read.csv('test.csv', header = TRUE)

str(file)

file$scheduled_departure_utc = ymd_hms(file$scheduled_departure_utc)

file$estimated_departure_utc = ymd_hms(file$estimated_departure_utc)

file$scheduled_departure_utc = as.numeric(file$scheduled_departure_utc)

file$estimated_departure_utc = as.numeric(file$estimated_departure_utc)

file <-file %>%
  mutate(
    delay_in_seconds = as.numeric(hms(sub(".*days ", "", delay))) + 
      as.numeric(sub(" days.*", "", delay)) * 86400)
  
# Remove columns by name
file <- file[ , !(names(file) %in% c("Public.Holidays", "delay")) ]

str(file)

fit <- lm(delay_in_seconds ~ estimated., data = file)

# See predictors included
summary(fit)


