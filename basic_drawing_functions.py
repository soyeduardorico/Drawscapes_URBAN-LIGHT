import numpy as np
import cv2
import os
import skimage
import matplotlib
matplotlib.use('Agg')
from skimage import morphology
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt #used for debuggin purposes

# ------------------------------------------------------------------------------------
# Imports project variables
# ------------------------------------------------------------------------------------
from project_data import link_base_image, link_base_image_large_annotated, link_base_image_warning, ucl_east_image
from project_data import shape_y, shape_x, thickness_lines, root_participation_directory
from project_data import reference_directory_images, reference_directory, overall_results_directory
from project_data import link_outcome_failure, link_outcome_success, node_coords, threshold_distance
from project_data import color_canvas_rgb, node_coords_detailed
from project_data import site_scale_factor, massing_height
from project_data import ucl_east_development_area, ucl_east_student_population, ucl_east_research_area
from project_data import ratio_accomodation_base, ratio_accomodation_plinth, ratio_accomodation_tower, m2accomodation_per_student
from project_data import ratio_research_base, ratio_research_plinth, ratio_research_tower

# ------------------------------------------------------------------------------------
# Imports locally defined functions
# ------------------------------------------------------------------------------------
from graph_form_image import path_graph




# ------------------------------------------------------------------------------------
# Draws polygon of site from nodes in edges for area estimates
# ------------------------------------------------------------------------------------
def site_area():
    # white canvas
    img= np.zeros((700,700,3), np.uint8)
    img.fill(255)
    # draws an outline with detailed nodes
    pts=np.array(node_coords_detailed, np.int32)
    pts=pts.reshape((-1,1,2))
    # fills site with black
    cv2.fillPoly(img,[pts],(0,0,0))
    img=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # calculates pixels
    sought = [0,0,0]
    result = np.count_nonzero(np.all(img==sought,axis=2))
    # rescles to m2
    area = result * site_scale_factor * site_scale_factor
    return area


# ------------------------------------------------------------------------------------
# Generates a list of polylines given a list of points
# ------------------------------------------------------------------------------------
def pts_to_polylines (points, line_type):
    polylines=[]
    line=[]
    linetypes = [] # lsit of type of line for thickness and color definition
    #generates lines of polylines
    for i in range (0, int(len(points[0])-1)):
        if points[2][i+1] > 1:
            pt=[points[0][i],shape_y-points[1][i]]
            line.append(pt)
        else:
            pt=[points[0][i],shape_y-points[1][i]]
            line.append(pt)
            polylines.append(line)
            linetypes.append(line_type[i])
            line=[]
    polylines.append(line)
    linetypes.append(line_type[len(line_type)-1])
    return polylines, linetypes


# ------------------------------------------------------------------------------------
# line drawing over blank canvas
# ------------------------------------------------------------------------------------
def draw_paths (polylines, linetype, folder,file_name):
    img = np.zeros((int(shape_x),int(shape_y),3), np.uint8)
    img.fill(255)
    for i in range(0, len(polylines)):
        thickness = thickness_lines[linetype[i]]
        color = color_canvas_rgb[linetype[i]]
        for j in range(0, int(len(polylines[i])-1)):
            cv2.line(img,(int(polylines[i][j][0]),int(shape_y-polylines[i][j][1])),(int(polylines[i][j+1][0]),int(shape_y-polylines[i][j+1][1])),color,thickness)
    b=os.path.join(folder, file_name + '.jpg')
    img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    cv2.imwrite(b,img2)
    return img2


# ------------------------------------------------------------------------------------
# line drawing over base
# ------------------------------------------------------------------------------------
def draw_paths_base (polylines, linetype, folder,file_name, img, save='True'):
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) # needs to invert colors first for the case of multiple line drawing. Does not affect individual ones which come greyscale
    for i in range(0, len(polylines)):
        thickness = thickness_lines[linetype[i]]
        color = color_canvas_rgb[linetype[i]]
        for j in range(0, int(len(polylines[i])-1)):
            cv2.line(img,(int(polylines[i][j][0]),int(shape_y-polylines[i][j][1])),(int(polylines[i][j+1][0]),int(shape_y-polylines[i][j+1][1])),color,thickness)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    if save == 'True':
        b2=os.path.join(folder, file_name + '_base.jpg')
        cv2.imwrite(b2,img)
    return img






