from numpy import (dot, arccos, clip)
from numpy.linalg import norm
import networkx as nx
import math as m
import os
import cv2
import numpy as np
import skimage

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from project_data import link_base_image_large, thickness_lines, link_base_image_large_annotated
from project_data import overall_results_directory, shape_x, shape_y

import project_data as pdt

# ------------------------------------------------------------------------------------
#script so far requires a 1 pixel buffer with no drawing in the edges
#defines a node to node graph by looking at nodes with value =1 and applying a filter
#to the 8 surrounding pixels
# ------------------------------------------------------------------------------------
class path_graph ():
    def __init__(self, array, node_coords, threshold, sketch_name,dir_write, folder_name, link_base_image,shape_x,shape_y):
        self.array=array * self.node_mask()
        self.node_coords=node_coords
        self.threshold=threshold
        self.sketch_name=sketch_name
        self.dir_write=dir_write
        self.folder_name = folder_name
        self.shape_x=shape_x
        self.shape_y=shape_y
        self.link_base_image=link_base_image

        # generates list of nodes as general pixel indexes, which is used in graph extraction
        self.nodes= []
        for i in self.node_coords:
            self.nodes.append(i[0]+self.shape_x*i[1])

        self.nodes_bridge= []
        for i in pdt.node_coords_bridge:
            self.nodes_bridge.append(i[0]+self.shape_x*i[1])

    # ------------------------------------------------------------------------------------
    # returns a mask for nodes at radious =0.75 * threshold to ensure graph stops at nodes
    # ------------------------------------------------------------------------------------
    def node_mask (self):
        node_mask_base = np.zeros((int(pdt.shape_x),int(pdt.shape_y),3), np.uint8)
        node_mask_base.fill(255)
        mask_radius = int(0.75*pdt.threshold_distance)
        for i in pdt.node_coords:
            cv2.circle(node_mask_base,(i[0],i[1]),mask_radius,(0,0,0),-1)
        node_mask_grey=skimage.img_as_ubyte(skimage.color.rgb2grey(node_mask_base))
        node_mask_binary=node_mask_grey > 250
        return node_mask_binary


    # ------------------------------------------------------------------------------------
    # returns direct graph from the pixels where nodes are each pixel
    # It receives a skeleton graph already fabricated
    # ------------------------------------------------------------------------------------
    def pixel_graph (self):
        A=self.array
        graph = nx.Graph()
        for i in range(1,int(A.shape[0]-1)):
            for j in range(1,int(A.shape[1]-1)):
                if A[i][j]==1:
                    #defines booleans around node starting right and moving clockwise
                    d1=A[i][j+1]==1 #right
                    d2=A[i+1][j+1]==1
                    d3=A[i+1][j]==1 #below
                    d4=A[i+1][j-1]==1
                    d5=A[i][j-1]==1 #left
                    d6=A[i-1][j-1]==1
                    d7=A[i-1][j]==1 #top
                    d8=A[i-1][j+1]==1
                    #applies filter to detect connections
                    #begins in cross locations (d1, d3, d5, d7)
                    if d1: graph.add_edge(A.shape[1]*i+j,A.shape[1]*i+j+1)
                    if d3: graph.add_edge(A.shape[1]*i+j,A.shape[1]*(i+1)+j)
                    if d5: graph.add_edge(A.shape[1]*i+j,A.shape[1]*i+j-1)
                    if d7: graph.add_edge(A.shape[1]*i+j,A.shape[1]*(i-1)+j)
                    #it later chacks diagonals if no cross existing
                    #in order to prevent extra edges in diagonals which generate triangles
                    if not d1 and not d7 and d8: graph.add_edge(A.shape[1]*i+j,A.shape[1]*(i-1)+j+1)
                    if not d1 and not d3 and d2: graph.add_edge(A.shape[1]*i+j,A.shape[1]*(i+1)+j+1)
                    if not d3 and not d5 and d4: graph.add_edge(A.shape[1]*i+j,A.shape[1]*(i+1)+j-1)
                    if not d5 and not d7 and d6: graph.add_edge(A.shape[1]*i+j,A.shape[1]*(i-1)+j-1)

        #reruns the graph adding weight = linear distance
        for i in list(graph.edges):
            graph.add_edge(i[0],i[1],weight=self.dist_nodes(i[0],i[1]))

        return(graph)

    # ------------------------------------------------------------------------------------
    # returns the dual graph of the main graph
    # where nodes are lines between pixels and eighs are angular deviation
    # ------------------------------------------------------------------------------------
    def dual_graph (self):
        L = nx.line_graph(self.simplified_graph())
        graph2=nx.Graph()
        for u,v in L.edges():
            graph2.add_edge(u,v,weight=self.vertex_angle(u,v))
        return(graph2)

    # ------------------------------------------------------------------------------------
    # returns the coordinates of a point in x,y given its number
    # ------------------------------------------------------------------------------------
    def coords(self,a):
        y=int(a/self.array.shape[1])
        x=a-int(a/self.array.shape[1])*self.array.shape[1]
        return(x,y)

    # ------------------------------------------------------------------------------------
    # euclidean distance between two points
    # ------------------------------------------------------------------------------------
    def dist_nodes(self,a,b):
        xa=self.coords(a)[0]
        ya=self.coords(a)[1]
        xb=self.coords(b)[0]
        yb=self.coords(b)[1]
        dist=m.sqrt((xa-xb)**2+(ya-yb)**2)
        return(dist)

    # ------------------------------------------------------------------------------------
    # closest point to an origin within a list
    # ------------------------------------------------------------------------------------
    def closest_point (self,a,point_list):
        dist_list=[]
        for i in point_list:
            dist_list.append([i,self.dist_nodes(a,i)])
        dist_list=sorted(dist_list, key=lambda entry: entry[1])
        return(dist_list[0][0])

    # ------------------------------------------------------------------------------------
    # selects the enpoints of the sketched lines which are within a threshold distance from the external self.nodes
    # ------------------------------------------------------------------------------------
    def select_endpoionts (self):
        node_list_drawing=[]
        endpoints=self.key_points()[0]
        for i in self.nodes:
            end= self.closest_point(i,endpoints)
            if self.dist_nodes(i,end) > self.threshold:
                node_list_drawing.append(0)
            else:
                node_list_drawing.append(end)
#        # to prevent error for sketches that do not include anynodes it makes up the simplest path 0-1
#        if len(node_list_drawing)<2:
#            node_list_drawing=[0,1]
        return (node_list_drawing)

    # ------------------------------------------------------------------------------------
    # gives angle of a vertex defined by two lines edges u,v
    # ------------------------------------------------------------------------------------
    def vertex_angle (self,u,v):
        #defines the vertex as defined by 3 points with p1 in the middle
        if u[0] == v[1]:
            p0=u[1]
            p1=u[0]
            p2=v[0]
        if u[1] == v[0]:
            p0=u[0]
            p1=u[1]
            p2=v[1]
        if u[0] == v[0]:
            p0=u[1]
            p1=u[0]
            p2=v[1]
        if u[1] == v[1]:
            p0=u[0]
            p1=u[1]
            p2=v[0]
        #generates the angular cost from the vertex
        v1=[self.coords(p1)[0]-self.coords(p0)[0],self.coords(p1)[1]-self.coords(p0)[1]]
        v2=[self.coords(p1)[0]-self.coords(p2)[0],self.coords(p1)[1]-self.coords(p2)[1]]
        c = dot(v1,v2)/norm(v1)/norm(v2) # cosine of the angle
        angle = 180 - m.degrees(arccos(clip(c, -1, 1)))
        return(angle)

    # ------------------------------------------------------------------------------------
    # finds the edge of a dual graph that contains a certain vertex
    # returns "False" in case the node is not on the drawign
    # ------------------------------------------------------------------------------------
    def find_dual_edge (self,n):
        node=False
        for i in self.dual_graph().nodes:
            if i[0]==n: node=i
            if i[1]==n: node=i
        return (node)

    # ------------------------------------------------------------------------------------
    # returns closest node to a point if within threshold distance, otherwise leaves the points as it is
    # ------------------------------------------------------------------------------------
    def snap(self, a):
        closest = self.closest_point(a,self.nodes)
        distance = self.dist_nodes(a, closest)
        if distance < self.threshold:
            snap_point = closest
        else:
            snap_point = a
        return snap_point

    # ------------------------------------------------------------------------------------
    # finds end points (end_point_list, degree 1) as well as jucntions  (junction_list, degree 3)
    # using the stright node to node graph
    # ------------------------------------------------------------------------------------
    def key_points(self):
        end_point_list=[]
        junction_list=[]
        for i in self.pixel_graph().degree:
            if i[1]==1:
                end_point_list.append(i[0])
            if i[1]>2:
                junction_list.append(i[0])
        return(end_point_list,junction_list)

    # ------------------------------------------------------------------------------------
    # returns costs of traversing the network nodes to nodes (angular cost) sorted min to max
    # ------------------------------------------------------------------------------------
    def path_cost_angular(self):
        iterate_nodes=self.select_endpoionts()
        cost_list=[]
        for i in  range(0,len(iterate_nodes)):
            if iterate_nodes[i] !=0:
                for j in range (i+1, len(iterate_nodes)):
                    if iterate_nodes[j] !=0:
                        d=nx.shortest_path_length(self.dual_graph(),source=self.find_dual_edge (iterate_nodes[i]),target=self.find_dual_edge (iterate_nodes[j]),weight='weight')
                        cost_list.append([i,j,d])

        cost_list = sorted(cost_list, key=lambda entry: entry[2])
        return(cost_list)

    # ------------------------------------------------------------------------------------
    # returns costs of traversing the network nodes to nodes (angular cost) sorted min to max
    # ------------------------------------------------------------------------------------
    def path_cost_metric(self):
        graph=self.pixel_graph()
        iterate_nodes=self.select_endpoionts()
        cost_list=[]
        for i in  range(0,len(iterate_nodes)):
            if iterate_nodes[i] !=0:
                list_reach=nx.algorithms.descendants(graph, iterate_nodes[i])
                for j in range (i+1, len(iterate_nodes)):
                    if iterate_nodes[j] !=0:
                        if iterate_nodes[j] in list_reach:
                            d1=nx.shortest_path_length(graph,source=iterate_nodes[i],target=iterate_nodes[j],weight='weight')
                            d2=self.dist_nodes(iterate_nodes[i],iterate_nodes[j])
                            d=d1/d2
                            cost_list.append([i,j,d])

        cost_list = sorted(cost_list, key=lambda entry: entry[2])
        return(cost_list)

    # ------------------------------------------------------------------------------------
    # returns a simplified graph of straight lines between endopoints and intesections
    # ------------------------------------------------------------------------------------
    def simplified_graph (self):
        H=self.pixel_graph()
        G=H.copy()
        pts_junctions=self.key_points()[1]
        pts_ends=self.key_points()[0]

        #removes the junctions to generate subgraphs or sets of connected components coincidign with lines
        for i in pts_junctions:
            G.remove_node(i)

        simplified_lines=[]
        #goes over long lines between junctions and end points and generates segments end to end
        for i in nx.connected_components(G):
            end_points=[]
            #begins with lines longer than one spur-pixel
            if len(i) > 1:
                for j in i:
                    if j in pts_ends:
                        end_points.append(j)
                    else:
                        if list(H.neighbors(j))[0] in pts_junctions:
                            end_points.append(list(H.neighbors(j))[0])
                        if list(H.neighbors(j))[1] in pts_junctions:
                            end_points.append(list(H.neighbors(j))[1])
            else:
                #follows with spurs (pixels on end)
                if list(i)[0] in pts_ends:
                    end_points.append(list(i)[0])
                    end_points.append(list(H.neighbors(list(i)[0]))[0])
                else:
                    #follows with islands (pixels between two junctions)
                    end_points.append(list(H.neighbors(list(i)[0]))[0])
                    end_points.append(list(H.neighbors(list(i)[0]))[1])
            simplified_lines.append(end_points)
        #finishes by adding edges in pairs of junctions that are adjacent and do not leave island when removed
        #checks length of line junction-junctin and selects those <2 meaning sideweays or diagonal
        end_points2=[]
        for i in range (0, len(pts_junctions)-1):
            for j in range (i+1,len(pts_junctions)-1):
                if self.dist_nodes(pts_junctions[i],pts_junctions[j]) < 2:
                    end_points2.append(pts_junctions[i])
                    end_points2.append(pts_junctions[j])
                    simplified_lines.append(end_points2)
        GS = nx.Graph()
        for i in simplified_lines:
            GS.add_edge(i[0],i[1])

        return (GS)

    # ------------------------------------------------------------------------------------
    # makes a drawign of graph (simplifies lines and edges)
    # ------------------------------------------------------------------------------------
    def draw_graph (self):
        img=cv2.imread(self.link_base_image)
        node_coords=[]
        for i in self.nodes:
            node_coords.append(self.coords(i))

        #generate lines from simplified graph and draws them
        lines=[]
        for i in self.simplified_graph().edges:
            pt0 = self.snap(i[0])
            pt1 = self.snap(i[1])
            lines.append([self.coords(pt0),self.coords(pt1)])
        for i in lines:
            cv2.line(img,i[0],i[1],(0,0,0),3)

        #finds intersection points and draws them
        intersection_nodes=[]
        for i in self.key_points()[1]:
            pt=self.snap(i)
            intersection_nodes.append(self.coords(pt))
        for i in intersection_nodes:
            cv2.circle(img,i,3,(0,255,0),-1)

        #writes node number in all potential end_points
        for i in range (0,len(node_coords)):
            cv2.putText(img,' '+str(i), node_coords[i],cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), lineType=cv2.LINE_AA)

        number_connections = 0
        #for the end_points used (snapped) it adds a circle
        for i in self.key_points()[0]:
            pt = self.snap(i)
            # checks whether the point is actually in an entrance or a spur elsewhere
            closest = self.closest_point(pt,self.nodes)
            distance = self.dist_nodes(pt, closest)
            if distance < 1:
                number_connections = number_connections+1
                cv2.circle(img,self.coords(pt),8,(0,0,255),-1)

        # Writes text on image
        # Instantiates class for text
        font1 = ImageFont.truetype(".fonts/arial.ttf", 35)

        # write text on connection number
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        im_source_pil = Image.fromarray(img)
        canvas =Image.new('RGB',(shape_y,shape_y), color = 'white')
        canvas.paste(im_source_pil,(0,0))
        draw = ImageDraw.Draw(canvas)
        draw.text((15, 560 + 32 + 32 + 10),"You connected a total of " + str(int(number_connections)) + " nodes",(29, 41, 82),font=font1)
        b1=os.path.join(self.dir_write, self.sketch_name + '_graph.jpg') # saves image corresponding to drawing stage
        canvas.save(b1)

    # ------------------------------------------------------------------------------------
    # Evaluates number of paths that cross under the beridge have been drawn
    # ------------------------------------------------------------------------------------
    def connections_under_bridge (self):
        number_connections_under_bridge = 0
        #for the end_points used (snapped) it adds a circle
        for i in self.key_points()[0]:
            pt = self.snap(i)
            # checks whether the point is actually in an entrance or a spur elsewhere
            closest = self.closest_point(pt,self.nodes_bridge)
            distance = self.dist_nodes(pt, closest)
            if distance < 1:
                number_connections_under_bridge = number_connections_under_bridge+1
        return number_connections_under_bridge

    # ------------------------------------------------------------------------------------
    # makes a drawign of single lines going to main nodes identified in path_cost_metric
    # ------------------------------------------------------------------------------------
    def draw_basic_connections (self):
        #imports base images for both small and large scale images
        img=cv2.imread(self.link_base_image)
        img2=cv2.imread(link_base_image_large)
        node_coords=[]
        for i in self.nodes:
            node_coords.append(self.coords(i))

        #calls cost function and represents best lines
        costs = self.path_cost_metric()
        basic_connections=[]
        for i in range (0,len(costs)): # Brings 4 best lines into small scale drawing
            if i<4:
                cv2.line(img,node_coords[costs[i][0]],node_coords[costs[i][1]],(29, 41, 82),(10-i*i))
                basic_connections.append([costs[i][0],costs[i][1]])

        #adds points into plots
        for i in range (0,len(node_coords)):
            cv2.circle(img,node_coords[i],5,(0,0,255),-1)
            cv2.putText(img,' '+str(i), node_coords[i],cv2.FONT_HERSHEY_SIMPLEX, 0.4, (29, 41, 82), lineType=cv2.LINE_AA)
        for i in range (0,len(node_coords_large)):
            cv2.circle(img2,(node_coords_large[i][0],node_coords_large[i][1]),3,(0,0,255),-1)

        # Writes text on image
        # Instantiates class for text
        font2 = ImageFont.truetype(".fonts/arial.ttf", 25)

        # generate new canvas
        im_source_pil = Image.fromarray(img)
        canvas =Image.new('RGB',(shape_y,shape_y), color = 'white')
        canvas.paste(im_source_pil,(0,0))
        draw = ImageDraw.Draw(canvas)
        draw.text((15, 560 + 32 + 32 + 10),"You connected a total of " + str(len(costs)) + " node couples",(29, 41, 82),font=font2)
        b1=os.path.join(self.dir_write, self.sketch_name + '_ln.jpg') # saves image corresponding to drawing stage
        canvas.save(b1)

        # saves connections as integers np
        b2=os.path.join(self.dir_write, self.sketch_name + "_ln")   # copy with file name
        b3=os.path.join(self.dir_write, self.folder_name + "_ln")   # copy as generic last version
        b4=os.path.join(overall_results_directory, self.folder_name + "_ln") # copy in overall results dir
        connections_export=np.array(basic_connections).astype(int) # saves connections as integers np
        np.save (b2, connections_export)
        np.save (b3, connections_export)
        np.save (b4, connections_export)

        # develops drawing at the large scale fordrawing feedback
        # generates a list of large scale paths whic are connected to two main simplified lines
        connections_large=[]
        valid_connections_internal = []
        if len(costs)>1:
            for i in range (0,2): # only picks first two ones
                # check if main simplified line starts / ends in one of the nodes with large scale connections
                if large_scale_paths[str(costs[i][0])] != 0:
                    if large_scale_paths[str(costs[i][1])] != 0:
                        connections_large.append(large_scale_paths[str(costs[i][0])])
                        connections_large.append(large_scale_paths[str(costs[i][1])])
                        valid_connections_internal.append([node_coords_large[costs[i][0]],node_coords_large[costs[i][1]]])

        #draws real paths on the city corresponding to paths sketched
        #loads base image and makes a copy to overlay with trasparency
        b1=os.path.join(self.dir_write,self.sketch_name + '_large_overall.jpg')
        img_large=cv2.imread(b1)
        img2=img_large.copy()
        alpha=0.6 # degree of transparency, 0=totally transparent

        # draws large scale paths over the plan
        polylines = connections_large
        for i in range(0, len(polylines)):
            for j in range(0, int(len(polylines[i])-1)):
                cv2.line(img2,(int(polylines[i][j][0]),int(polylines[i][j][1])),(int(polylines[i][j+1][0]),int(polylines[i][j+1][1])),(0,0,255),thickness_lines[0]*2)

        # draws large scale paths over the plan
        polylines = valid_connections_internal
        for i in range(0, len(polylines)):
            for j in range(0, int(len(polylines[i])-1)):
                cv2.line(img2,(int(polylines[i][j][0]),int(polylines[i][j][1])),(int(polylines[i][j+1][0]),int(polylines[i][j+1][1])),(0,0,255),thickness_lines[0]*2)

        #overlays img_large (base) and img2 (with lines) and saves
        cv2.addWeighted(img2, alpha, img_large, (1-alpha), 0, img_large)
        cv2.imwrite(b1,img_large)

        return basic_connections


#%%
