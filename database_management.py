import os
import numpy as np
import cv2
import re
import time
from tinydb import TinyDB, Query
from PIL import Image, ImageDraw
from matplotlib import pyplot as plt #used for debuggin purposes

# ------------------------------------------------------------------------------------
# Imports project variables
# ------------------------------------------------------------------------------------  
from project_data import link_base_image, link_base_image_large_annotated, link_base_image_warning, ucl_east_image
from project_data import shape_y, shape_x, thickness_lines, root_participation_directory
from project_data import reference_directory_images, reference_directory, overall_results_directory
from project_data import link_outcome_failure, link_outcome_success, node_coords, threshold_distance
from project_data import color_canvas_rgb, node_coords_detailed
from project_data import site_scale_factor, massing_height, databse_filepath
from project_data import ucl_east_development_area, ucl_east_student_population, ucl_east_research_area
import project_data as pdt

# ------------------------------------------------------------------------------------
# Imports locally defined functions
# ------------------------------------------------------------------------------------  
from basic_drawing_functions import draw_paths_base, pts_to_polylines


#%%



#%%
#----------------------------------------------------------------------------------------
# Generate lists of np data of sketches in directory
#----------------------------------------------------------------------------------------
def list_files_dir():
    list_files = [] # file names
    sketches = os.listdir(overall_results_directory)
    #generates list of files
    for i in sketches:
        if not i == 'Thumbs.db':
            if re.findall('_lines.npy',i) :
                list_files.append(i.replace('_lines.npy', ''))
    return list_files



#----------------------------------------------------------------------------------------
# Reads image from np saved and type of exervice (massing or line), generates all fields and updates database (upsert method)
#----------------------------------------------------------------------------------------
def test_and_file (db, sketch, exercise, extract_features = 'True'):
    file_name = sketch
    filepath_np = os.path.join(overall_results_directory, file_name + '_' + exercise + '.npy')
    filepath_np_type = os.path.join(overall_results_directory, file_name + '_' + exercise + '_type.npy')
    if os.path.exists(filepath_np):
        ptexport=np.load(filepath_np).astype(int)
        points=ptexport.tolist()
        line_type=np.load(filepath_np_type).astype(int)
        pts_to_polylines_list =  pts_to_polylines(points, line_type)
        polylines  = pts_to_polylines_list [0]
        linetype = pts_to_polylines_list [1]
        if len(polylines[0])>1:
            field_polylines = exercise + '_polylines'
            field_linetype = exercise + '_linetype'
            field_features = exercise + '_features'
            print('processing data for ' + file_name)

            feature_values = []

            #brings data into database
            #turns data from 'int' to 'float' otherwise json will not like it
            linetype = [float(i) for i in linetype]
            polylines[0]= np.array(polylines[0]).astype(float).tolist()
            sketch_query=Query()
            #update / instert (upsert)
            db.upsert( {'id': file_name, field_polylines : polylines, field_linetype : linetype, field_features : feature_values}, sketch_query.id == file_name) # inserts or udates




#----------------------------------------------------------------------------------------
# Sends polylines and line types to various databases
#----------------------------------------------------------------------------------------

def export_data (data, folder_name, file_name, session_folder, exercise):
    # prepares data
    line_type = data[4]
    data.pop(4) # removes linetype array
    data.pop(0) # removes style array (one element) from list
    ptexport=np.array(data).astype(int)  # turn into integer since mobile devices will produce fractions and pythonanywhere saves as float
    points=ptexport.tolist()
    pts_to_polylines_list  = pts_to_polylines(points, line_type)
    polylines  = pts_to_polylines_list [0]
    linetype = pts_to_polylines_list [1]

    # saves data in general database 
    id_name=folder_name
    database = pdt.databse_filepath
    data_to_database (database, polylines, linetype, id_name, exercise, extract_features = 'False')

    # saves data in user database 
    id_name=file_name # saves each of the steps
    database = os.path.join(session_folder, folder_name + '_database.json')
    data_to_database (database, polylines, linetype, id_name, exercise, extract_features = 'False')
    id_name=folder_name  # saves final step with root name 
    data_to_database (database, polylines, linetype, id_name, exercise, extract_features = 'False')    


#----------------------------------------------------------------------------------------
# Sends polylines and line types to one databsae
#----------------------------------------------------------------------------------------
def data_to_database (databse, polylines, linetype, id_name, exercise, extract_features = 'True'):
    field_polylines = exercise + '_polylines'
    field_linetype = exercise + '_linetype'
    field_features = exercise + '_features'
    millis2 = int(round(time.time() * 1000))


    feature_values = []
    linetype = [float(i) for i in linetype]
    polylines[0]= np.array(polylines[0]).astype(float).tolist()
    db = TinyDB(databse)
    sketch_query=Query()
    #update / instert (upsert)
    db.upsert( {'id': id_name, field_polylines : polylines, field_linetype : linetype, field_features : feature_values}, sketch_query.id == id_name) # inserts or udates
    db.close()


#----------------------------------------------------------------------------------------
# Reads line data from database
#----------------------------------------------------------------------------------------
def line_data_from_database (databse_filepath, user_id, exercise):
    db = TinyDB(databse_filepath)
    sketch_item=Query()
    field_polylines = exercise + '_polylines'
    field_linetype = exercise + '_linetype'
    data_polylines_dict = db.search(sketch_item.id==user_id)[0] # it brings a list of the dictinaries with that name, which in this case will be 1  long only
    if field_polylines in data_polylines_dict: # checks whether the field exists or the user skipped use
        data_polylines_float = data_polylines_dict.get(field_polylines)
        data_polylines = []
        for i in data_polylines_float:
            data_polylines.append(np.array(i).astype(int).tolist()) # needs reconverting to integer from float in database
        data_linetype = db.search(sketch_item.id==user_id)[0].get(field_linetype)
        data_linetype =  np.array(data_linetype).astype(int).tolist() # needs reconverting to integer from float in database
    else:
        data_polylines = [[[]]]
        data_linetype  =[]
    return data_polylines, data_linetype








#%%

#exercise = 1 # 0: lines, 1: massing
#

#db.purge()
#for sketch in list_files_dir():
#    file_name = sketch
#    test_and_file (db, sketch, 'lines')
#    test_and_file (db, sketch, 'massing')


#%%


#%%
#file_name = '1574548541279'
#id_name = '1574548541279_test'
#
#exercise_number = 0
#exercise_list=['lines','massing']
#exercise = exercise_list[exercise_number]
#
#filepath_np = os.path.join(overall_results_directory, file_name + '_' + exercise + '.npy')
#filepath_np_type = os.path.join(overall_results_directory, file_name + '_' + exercise + '_type.npy')
#ptexport=np.load(filepath_np).astype(int)
#points=ptexport.tolist()
#line_type=np.load(filepath_np_type).astype(int)
#pts_to_polylines_list =  pts_to_polylines(points, line_type)
#polylines  = pts_to_polylines_list [0]
#linetype = pts_to_polylines_list [1]
#
#data_to_database (polylines, linetype, id_name, exercise, extract_features = 'True')
#
#print(len(db))
#tsne_embedding (db, exercise_number, id_name)

#%%
#sketch_item=Query()
#id_name = '1575016808957'
#for item in db:
#    features = item.get('lines_features')
#    print (len(features))
#
#
#db2 = db.search(sketch_item.lines_features != [])    
#for item in db2:
#    features = item.get('lines_features')
#    print (len(features))  
#    
    
    
    
#%%
# db = TinyDB(databse_filepath)
# id_name = '1575681037493'
# tsne_embedding (db, 0, id_name)
