# the tokens file should be one word per line
tokens <- scan("/home/flathers/Desktop/workspace/search-log-analysis/eda/abstracts/tokens.txt", what="string", sep="\n")
#t <- as.data.frame(tolower(tokens))
t <- tolower(tokens)
t <- trimws(t)
#summary(t)
#head(table(t), 100)

# load the default stop words from the text mining package
library(tm)
stopWords <- stopwords("en")
# and add some new stop words for this dataset
stopWords <- c(stopWords, ">","0","00","000","001","01","1","04","05","10",
               "11","12","13","13030","14","014","15","015","15","16","17",
               "18","19","1999","2","02","20","2000","2001","2002","2003",
               "2004","2005","2006","2007","2008","2009","2010","2011",
               "2012","2013","2014","2015","2016","2017","21","22","23",
               "24","25","26","27","28","29","3","03","003","30","31","37",
               "4","40","5","5","50","5061","6","06","006","6067","6073",
               "6085","7","07","8","08","9","09","aa","access",
               "accessibility","across","activities","adaptive","aekos",
               "aggregated","al","algorithm","along","also","although",
               "among","analyses","analysis","application","apply",
               "approximately","architecture","archive","areas","ariel",
               "ark","ars","assessment","assessments","associated","atlas",
               "au","automatic","available","aware","b","based","basic",
               "beginning","bolted","bottom","c","cadwsap","can","center",
               "central","change","cloud","collaboration","collected",
               "collection","compared","compilation","composition",
               "computer","conditions","conducted","consists","contains",
               "contamination","continuation","contributing","control","corp",
               "corrected","cover","created","cruz","ctd","current","d",
               "data","dataset","datasets","date","debra","density",
               "department","describes","develop","developed","development",
               "differences","different","digital","distribution","doi","dr",
               "drinking","dryad","due","dx","dynamics","e","early",
               "ecotrends","edu","effect","either","eml","enables","enhanced",
               "environmental","eros","established","et","evidence",
               "evolutionary","exploratory","fa","facilitate","falls",
               "federally","file","files","first","flight","focused",
               "following","format","found","four","fs","full","funded","g",
               "generate","generated","gov","ground","group","growth","high",
               "higher","history","host","however","html","http","https",
               "identified","identifies","image","important","improving",
               "include","included","includes","including","increase",
               "increased","individual","individuals","info","information",
               "instrument","instruments","intended","interactive","interval",
               "intervals","j","jornada","knb","known","large","ledaps",
               "less","level","levels","located","locations","long","low",
               "lower","lpgs","lter","lternet","lugo","luquillo","m","made",
               "major","manual","many","map","mapper","may","mean","measured",
               "measurements","meta","metadata","meter","meters","method",
               "methods","mid","mimbres","minute","minutes","mix","module",
               "msl","multiple","n","natural","near","necessary","network",
               "new","noaa","nodc","non","north","nsw","number","numbers",
               "numerous","observed","obtained","office","one","ongoing",
               "onset","org","originally","overall","p","package",
               "parameters","part","participating","pasta","path","patterns",
               "per","percent","period","peters","physical","pisco","please",
               "plot","plots","plus","point","portal","potential","present",
               "pressure","processed","processes","processing","produce",
               "producing","product","production","profile","profiles",
               "program","project","protect","provide","provided","quality",
               "r","raster","rate","rates","record","recorded","reference",
               "reflectance","regions","related","relative","remote","report",
               "reported","research","resolution","response","results","row",
               "s","sample","samples","sampling","santa","scale","science",
               "see","selection","sensing","series","service","set","several",
               "show","significant","single","sioux","site","sites","size",
               "small","software","source","south","space","specific",
               "standard","station","stowaway","structure","studies","study",
               "suggest","supply","support","surveys","synthesis","system",
               "systems","t","tagged","taken","tbi32","tbic32","term",
               "thematic","three","tidbit","time","timescale","tm","top",
               "total","tracking","traits","two","type","typical","u",
               "understanding","units","universities","university","updated",
               "us","usda","use","used","users","usgs","using","v","values",
               "variation","various","ver","vis","vulnerability","w","web",
               "well","will","wire","within","www","xbt","xml","xti","xti32",
               "year","yearly","years","zone")

# convert tokens to lowercase, remove white space, remove stop words
t2 <- t[! t %in% stopWords]
t2 <- as.data.frame(t2)
#head(sort(table(t2), decreasing=TRUE), 500)

# create the word cloud
library(wordcloud)
df <- as.data.frame(sort(table(t2), decreasing=TRUE))
set.seed(12345)
wordcloud(words = df$t2, freq = df$Freq, min.freq = 1,
          max.words=106, random.order=FALSE, rot.per=0.35, 
          colors=brewer.pal(8, "Dark2"))

#head(df, 20)
t2[!t2 %in% c("10")]

