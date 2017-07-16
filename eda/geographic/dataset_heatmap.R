#Create heat map grid of the number of datasets in each of DataONEs map grid cells from their online search tool

#ggplot2 instructions here:https://learnr.wordpress.com/2010/01/26/ggplot2-quick-heatmap-plotting/
#Data first taken from DataONE webpage on June 22, 2017
#Developed by Megan Mach with help from Robin Elahi on the GGPLOTing



#set working directory to "heatgrid" in my DataONE graphic folder

#GGPLOT2 HeatMap
setg <- read.csv("dataONE_count_170522.csv", sep=",")
#setg$Name<-with(setg, reorder(Name,LAT))
setg <- setg[order(setg$LAT),]

library(ggplot2)
theme_set(theme_minimal(base_size = 12)) 
library(reshape2)
library(dplyr)
library(RColorBrewer) #calls up the colorbrewer2 color schemes, use "display.brewer.all()" to see color palettes
setg.m<-melt(setg, id.vars="LAT") #dataframe converted from wide to long

setg.m <- setg.m %>% mutate(value2 = ifelse(value == 0, NA, value), value_log = log(value2))

#setg.m$valuelog<-(log(setg.m$value)) #logging same as above but without dplyr

names(setg.m)
summary(setg.m)
str(setg.m)

theme_blank <- theme(axis.line=element_blank(),
      axis.text.x=element_blank(),
      axis.text.y=element_blank(),
      axis.ticks=element_blank(),
      axis.title.x=element_blank(),
      axis.title.y=element_blank(),
      legend.position="none",
      panel.background=element_blank(),
      panel.border=element_blank(),
      panel.grid.major=element_blank(),
      panel.grid.minor=element_blank(),
      plot.background=element_blank())


ggplot(setg.m, aes(variable, -LAT, fill = value_log)) + geom_raster() + theme(panel.grid = element_blank()) + theme(axis.text = element_blank()) + scale_fill_distiller(palette = "Oranges", direction = 1, na.value = "white") + theme(legend.position = "none") + xlab("") + ylab("") + 
	theme(axis.line=element_blank(),
      axis.text.x=element_blank(),
      axis.text.y=element_blank(),
      axis.ticks=element_blank(),
      axis.title.x=element_blank(),
      axis.title.y=element_blank(),
      legend.position="none",
      panel.background=element_blank(),
      panel.border=element_blank(),
      panel.grid.major=element_blank(),
      panel.grid.minor=element_blank(),
      plot.background=element_blank())
     
ggsave("gg_heat_grid.pdf", height = 5, width = 7, dpi = 600)
#ggsave("gg_heat_grid.png", height = 5, width = 7) # saves ggplot as png


##########ATTEMPT TO OVERLAY HEAT GRID ON MAP WITH NO LAT LONG COORDINATES#########
#Pull in the heat map grid and overlay it on the map
#install.packages("magick")
library(magick)

#stack layers
grid<-image_read('set_heatmap.pdf') #call up heat map grid
map<-image_read("WorldMap_Equirectangular.svg")
#heat<-c(grid,map)
#heat<-image_scale(heat,"300x300")
#image_info(heat)

grid_scaled<-image_scale(image_colorize(image_background(grid,"none"),opacity=50, "none"),"200x300")
image_composite(image)



##################ATTEMPTING TO GET DATA DENSIT GRID INFORMATION DIRECTLY FROM SOURCE################


# To pull updatable data from source, from Lauren Walker
# The DataONE catalog can be searched using the DataONE API. There is even a DataONE R client that can perform searches. But the geohash (tile) search that the search.dataone.org site uses is this: `https://search.dataone.org/cn/v2/query/solr/?q=-obsoletedBy:*+formatType:METADATA&rows=0&start=0&facet=true&facet.sort=index&facet.field=geohash_2&facet.mincount=1&facet.limit=-1&wt=json`
#(That returns JSON)
#The tiles on the website are geohash tiles - which is a type of lat,long encoding that converts lat,long bounding boxes to geohash codes like `4t` or `zc`
#There is a `geohash` R library that converts geohashes to lat,long values
#Workflow:
#Get the list of geohashes and the number of datasets in each geohash (via the link above), 
#convert each geohash to lat,long boxes, 
#then map those boxes

require(jsonlite) #bring in JSON file (similar to CSV)
require(geohash)

url <- 'https://search.dataone.org/cn/v2/query/solr/?q=-obsoletedBy:*+formatType:METADATA&rows=0&start=0&facet=true&facet.sort=index&facet.field=geohash_2&facet.mincount=1&facet.limit=-1&wt=json'
geodata <- fromJSON(txt=url)

coord<-gh_decode(geodata$facet_counts$facet_fields$geohash_2)

#You have a list of geohashes, And each geohash is paired with a number of datasets, That is what is in the JSON
#And you just learned how to convert a geohash to a lat, long
#So you need to combine the data frame you have now ("coord") to match the JSON from the DataONE search with your decoded geohashes

x <- jsonlite::fromJSON("https://search.dataone.org/cn/v2/query/solr/?q=-obsoletedBy:*+formatType:METADATA&rows=0&start=0&facet=true&facet.sort=index&facet.field=geohash_2&facet.mincount=1&facet.limit=-1&wt=json", FALSE)

geoms <- lapply(x$data, function(z) {
  dat <- tryCatch(jsonlite::fromJSON(z$geometry, FALSE), error = function(e) e)
  if (!inherits(dat, "error")) {
    list(type = "FeatureCollection",
         features = list(
           list(type = "Feature", properties = list(), geometry = dat)
         ))
  }
})



