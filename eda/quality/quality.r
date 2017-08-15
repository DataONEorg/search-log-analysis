install.packages("car")
install.packages("kSamples")
library(car)
library(kSamples)

# Load the data
csvdata = read.csv('scores10k.csv')
csvdata = data.frame(csvdata)
csvdata$hasData = as.factor(csvdata$hasData)

# Split data into groups
hasData = csvdata[csvdata$hasData!=0,]
noData = csvdata[csvdata$hasData==0,]

# Reduce the number of noData rows by resampling
#noData = noData[sample(nrow(noData), nrow(hasData)), ]
#reduced = rbind(hasData, noData)
#head(reduced)

# Take a look at the data
head(hasData)
head(noData)
summary(hasData$success)
summary(noData$success)


# Test whether data come from different distributions
ks.test(hasData$success, noData$success)
ad.test(hasData$success, noData$success)


# Do the two groups have different variances?
var(hasData$success)
var(noData$success)
leveneTest(success~hasData, data=csvdata)


# What's the common standard deviation?
sqrt(var(csvdata$success))


# Do the two groups have different means?
mean(hasData$success)
mean(noData$success)
wilcox.test(success~hasData, data=csvdata)

