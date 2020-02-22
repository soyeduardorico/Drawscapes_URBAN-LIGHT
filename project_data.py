import os
# note or checking
# ------------------------------------------------------------------------------------
# Root Folders
# ------------------------------------------------------------------------------------
root_directory = os.path.dirname(__file__)
root_participation_directory = os.path.join(root_directory, 'data')


# ------------------------------------------------------------------------------------
# Folder references
# ------------------------------------------------------------------------------------
reference_directory=os.path.join(root_directory,'static/reference_directory')
reference_directory_images=os.path.join(root_directory,'static/recommendation_output')
interface_images=os.path.join(root_directory,'static/images')
model_directory=os.path.join(root_directory,'style_transfer_models')
overall_results_directory = os.path.join(root_directory,'overall_results')


# ------------------------------------------------------------------------------------
# Files references
# ------------------------------------------------------------------------------------
link_base_image = os.path.join(interface_images, 'base_image.jpg')
link_base_image_png = os.path.join(interface_images, 'base_image_png.png')
link_base_image_warning = os.path.join(interface_images, 'base_image_warning.jpg')
link_base_image_large = os.path.join(interface_images, 'base_image_large.jpg')
link_base_image_large_annotated = os.path.join(interface_images, 'base_image_large_annotated.jpg')
link_styles_catalogue = os.path.join(interface_images, 'overall_style.jpg')
link_outcome_success = os.path.join(interface_images, 'outcome_success.jpg')
link_outcome_failure = os.path.join(interface_images, 'outcome_failure.jpg')
link_feedback_massing_base = os.path.join(interface_images, 'feedback_massing_base.jpg')
click_on_screen = os.path.join(interface_images, 'cick_on_screen.jpg')
ucl_east_image = os.path.join(interface_images, 'ucl_east_marshgate.jpg')
databse_filepath = os.path.join (overall_results_directory,'database.json')
feedback_barrier_base = os.path.join(interface_images, 'feedback_barrier_base.jpg')
feedback_canal_base = os.path.join(interface_images, 'feedback_canal_base.jpg')
feedback_noise_base = os.path.join(interface_images, 'feedback_noise_base.jpg')
feedback_barrier = os.path.join(interface_images, 'feedback_barrier.jpg')
feedback_canal = os.path.join(interface_images, 'feedback_canal.jpg')
feedback_noise = os.path.join(interface_images, 'feedback_noise.jpg')
draw_no_lines_drawn = os.path.join(interface_images, 'draw_no_lines_drawn.jpg')
base_canal_calculation = os.path.join(interface_images, 'base_canal_calculation.jpg')
base_noise_calculation = os.path.join(interface_images, 'base_noise_calculation.jpg')

# ------------------------------------------------------------------------------------
# Generic data on image size and typical colours
# ------------------------------------------------------------------------------------
website_colour = (29, 41, 82)
threshold_distance=20 # threshold for snapping lines into origin points
n_neighbours=2 # neighborxs for style recommendation

# size of canvas
shape_x=700
shape_y=700

# line colors
color_lines= (0,0,0)
color_lines_cv2= (0,0,0)


# ------------------------------------------------------------------------------------
# Color and line thickness definition. Coordinate with drawscapes_scripts.js
# ------------------------------------------------------------------------------------
# Use color coder in https://www.google.com/search?q=color+picker
# height in storeys of building massing accordign to layers
# heigth is measured from the ground, ie, it is NOT stacked in the calculation
# thickness of linmes measured in pixels. To get actual width multiply *  site_scale_factor
color_canvas_rgb = [[0,0,0],[230, 196, 138],[255, 110, 94],[255, 0, 0],[186, 163, 13], [112, 48, 160],[204, 102, 24], [44, 112, 15]]
thickness_lines = [5,30,22,15, 10, 10, 10, 10]
massing_height = [0,2,5,10, 0, 0, 0, 10] # last two colours do will appear in massing clal but the function will loop over all colors incl land uses


# ------------------------------------------------------------------------------------
# Definition of exercises carried out during the uinterface use and how they are saved in database
# ------------------------------------------------------------------------------------
exercises =  ['lines','massing','land_uses']
	

# ------------------------------------------------------------------------------------
# Site specific geometric data
# ------------------------------------------------------------------------------------
node_coords=[[146,227],
[201,212],
[393,160],
[454,144],
[469,186],
[535,307],
[584,371],
[410,547],
[344,567]]

node_coords_bridge=[[469,186], [535,307], [344,567]] # these are nodes that lead to connections under the DLR bridge

#detailed shape of polygon to draw montage. May incluide more points than coords
node_coords_detailed=[[146,227],
[201,212],
[393,160],
[454,144],
[469,186],
[535,307],
[584,371],
[410,547],
[344,567],
[226,438],
[146,273]]

# Factor that relates pixel size to meters = diagonal_meters / diagonal_pixels
site_scale_factor = 250/461

# data on UCL EAST development
ucl_east_development_area = 134700
ucl_east_student_population = 500
ucl_east_research_area = 5000

# data for conversion of massign m2 to land uses
ratio_accomodation_base = 0
ratio_accomodation_plinth = 0.3
ratio_accomodation_tower = 0.7
m2accomodation_per_student = 15
ratio_research_base = 0.5
ratio_research_plinth = 0.3
ratio_research_tower = 0