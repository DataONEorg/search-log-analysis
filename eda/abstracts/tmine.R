# the tokens file should be one word per line
tokens <- scan("/home/flathers/Desktop/workspace/search-log-analysis/eda/abstracts/tokens.txt", what="string", sep="\n")
t <- as.data.frame(tolower(tokens))
#summary(t)
#head(table(t), 100)

# load the default stop words from the text mining package
library(tm)
stopWords <- stopwords("en")
# and add some new stop words for this dataset
stopWords <- c(stopWords, "00", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "50", "5061", "6085")
stopWords <- c(stopWords, "aa", "doi", "dx", "using")

# convert tokens to lowercase, remove white space, remove stop words
t2 <- tolower(tokens)
t2 <- trimws(t2)
t2 <- t2[! t2 %in% stopWords]
t2 <- as.data.frame(t2)
#head(sort(table(t2), decreasing=TRUE))

# create the word cloud
library(wordcloud)
df <- as.data.frame(sort(table(t2), decreasing=TRUE))
set.seed(12345)
wordcloud(words = df$t2, freq = df$Freq, min.freq = 1,
          max.words=200, random.order=FALSE, rot.per=0.35, 
          colors=brewer.pal(8, "Dark2"))

#head(df, 20)
