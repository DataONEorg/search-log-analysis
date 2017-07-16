
tokens <- scan("/home/flathers/Desktop/workspace/search-log-analysis/data/tokens2.txt", what="string", sep="\n")
t = as.data.frame(tolower(tokens))
summary(t)
head(table(t), 100)

library(tm)
stopWords <- stopwords("en")

t2 = tolower(tokens)
t2 = t2[! t2 %in% stopWords]
t2 = as.data.frame(t2)
head(sort(table(t2), decreasing=TRUE))

library(wordcloud)
df = as.data.frame(sort(table(t2), decreasing=TRUE))
set.seed(12345)
wordcloud(words = df$t2, freq = df$Freq, min.freq = 1,
          max.words=200, random.order=FALSE, rot.per=0.35, 
          colors=brewer.pal(8, "Dark2"))

head(df, 20)