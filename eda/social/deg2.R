install.packages("igraph")
library(igraph)

# Set up the data for the graph plot
# http://kateto.net/networks-r-igraph
#nodes = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/eda/social/nodesByIpDeg2NodesNOCN.csv", header=TRUE, as.is=TRUE)
#links = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/eda/social/nodesByIpDeg2EdgesNOCN.csv", header=TRUE, as.is=TRUE)
nodes = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/eda/social/deg2nodesNOCN.csv", header=TRUE, as.is=TRUE)
links = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/eda/social/deg2edgesNOCN.csv", header=TRUE, as.is=TRUE)
#nrow(nodes); length(unique(nodes$id))
#nrow(links); nrow(unique(links[,c("from", "to")]))

#links <- aggregate(links[,3], links[,-3], sum)
links <- links[order(links$from, links$to),]
colnames(links)[3] <- "weight"
rownames(links) <- NULL


# This code moves the vertex labels outside the circle
# https://stackoverflow.com/questions/23209802/placing-vertex-label-outside-a-circular-layout-in-igraph
radian.rescale <- function(x, start=0, direction=1) {
  c.rotate <- function(x) (x + start) %% (2 * pi) * direction
  c.rotate(scales::rescale(x, c(0, 2 * pi), range(x)))
}
la <- layout.circle(net)
lab.locs <- radian.rescale(x=1:nrow(nodes), direction=-1, start=0)

nodes=sample(nodes$id, replace=FALSE)

# Plot the graph -- randomize node order and re-run to get better output
nodes=sample(nodes, replace=FALSE)
net <- graph_from_data_frame(d=links, vertices=nodes, directed=F)
#net
plot(net, layout=layout_in_circle, 
     vertex.label=V(net)$id, vertex.size=10, 
     edge.width=E(net)$weight, edge.color="black",
     rescale=FALSE, vertex.label.dist=1, vertex.label.degree=lab.locs)








# Set up the data for the graph plot
# http://kateto.net/networks-r-igraph
nodes = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/eda/social/nodesByIpDeg2Nodes.csv", header=TRUE, as.is=TRUE)
links = read.csv("/home/flathers/Desktop/workspace/search-log-analysis/eda/social/nodesByIpDeg2Edges.csv", header=TRUE, as.is=TRUE)
#nrow(nodes); length(unique(nodes$id))
#nrow(links); nrow(unique(links[,c("from", "to")]))

#links <- aggregate(links[,3], links[,-3], sum)
links <- links[order(links$from, links$to),]
colnames(links)[3] <- "weight"
rownames(links) <- NULL


# This code moves the vertex labels outside the circle
# https://stackoverflow.com/questions/23209802/placing-vertex-label-outside-a-circular-layout-in-igraph
radian.rescale <- function(x, start=0, direction=1) {
  c.rotate <- function(x) (x + start) %% (2 * pi) * direction
  c.rotate(scales::rescale(x, c(0, 2 * pi), range(x)))
}
la <- layout.circle(net)
lab.locs <- radian.rescale(x=1:nrow(nodes), direction=-1, start=0)

nodes=sample(nodes$id, replace=FALSE)

# Plot the graph -- randomize node order and re-run to get better output
nodes=sample(nodes, replace=FALSE)
net <- graph_from_data_frame(d=links, vertices=nodes, directed=F)
#net
plot(net, layout=layout_in_circle, 
     vertex.label=V(net)$id, vertex.size=10, 
     edge.width=E(net)$weight/10, edge.color="black",
     rescale=FALSE, vertex.label.dist=1, vertex.label.degree=lab.locs)

E(net)$weight[18]=200
E(net)$weight[19]=100
