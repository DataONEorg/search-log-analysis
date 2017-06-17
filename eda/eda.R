# Load the data
sessions = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/data/sessions.csv")
dls = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/data/dlEventsBySession.csv")
sxs = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/data/sEventsBySession.csv")
mns = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/data/multiNodeSessions.csv")

# Merge the search and download event counts into the sessions dataframe
sessions$sCount = sxs$count.logData.id.
ses = data.frame(sessions)
dls = data.frame(dls)
sessions = merge(ses, dls, by.x="id", by.y="sessionId", all.x = TRUE)
colnames(sessions)[which(names(sessions) == "count.downloadLog2.id.")] <- "dCount"
sessions[is.na(sessions)] <- 0
sessions$eCount = sessions$sCount + sessions$dCount


# Basic stats for session duration in minutes
durationS = strtoi(as.difftime(as.character(sessions$duration), format = "%H:%M:%S", units = "secs"))
durationM = durationS / 60
summary(durationM)
durations = durationM[durationM<60]
hist(durations,
     xlab="Session Length (minutes)",
     ylab="Session Count",
     main="Session Duration in Minutes"
)
axis(side=1, at=seq(15,60, 5), labels=seq(15,60,5))


# Basic stats for session download events
events = sessions$dCount[sessions$dCount>0]
table(events)
as.numeric(table(events))
sum(as.numeric(table(events)))
sum(as.numeric(table(events)))*.5
439+192+83+45+35+23+13+15
summary(events)

events = sessions$dCount[sessions$dCount>0 & sessions$dCount<21]
plot(table(events),
     xlab="Number of Downloads",
     ylab="Session Count",
     main="Downloads Per Session"
     )


# Basic stats for session search events
events = sessions$sCount[sessions$sCount>0]
table(events)
summary(events)

events = sessions$sCount[sessions$sCount>0 & sessions$sCount<101]
plot(table(events),
     xlab="Number of Search Events",
     ylab="Session Count",
     main="Search Events Per Session"
     )


# Basic stats for session total events
events = sessions$eCount[sessions$eCount>0]
table(events)
summary(events)

events = sessions$eCount[sessions$eCount>0 & sessions$eCount<101]
plot(table(events),
     xlab="Number of Total Events",
     ylab="Session Count",
     main="Total Events Per Session"
)


# Stats about sessions involving more than one member node
head(mns)
nodes = as.numeric(table(mns$sessionId))
summary(nodes)
table(nodes)
plot(table(nodes),
     xlab="Number of Member Nodes Accessed",
     ylab="Session Count",
     main="Member Nodes Accessed Per Session"
)


mns$count = rep(0,length(mns$sessionId))
for (n in names(table(mns$sessionId))) {
  count = as.numeric(table(mns$sessionId)[n])
  mns$count[mns$sessionId==n]=count
}
head(mns)
sort(table(mns$nodeId[mns$count>1]))
mns[mns$count==2,]
mns[mns$count==3,]
mns[mns$count==4,]
mns[mns$count==5,]
