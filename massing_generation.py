from mpl_toolkits import mplot3d
import matplotlib.image as mpimg
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
from PIL import Image
from pylab import *
from matplotlib.cbook import get_sample_data
from matplotlib._png import read_png
import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
import itertools
import project_data as pdt
import database_management as dbm
import basic_drawing_functions as bdf
from matplotlib.pyplot import figure

# ---------------------------------------------------------------------------
# generates a list of points to place bars and generate 3D
# ---------------------------------------------------------------------------
def grid_points(size):
    x_range_1 = np.ones(size)
    x_range_2=[]
    for i in np.linspace(0,size,size).tolist():
        x_range_2.append(x_range_1*i)    
    x_range_2_flat = list(itertools.chain(*x_range_2)) # flattens list    

    y_range_1 = np.linspace(0,size,size).tolist()
    y_range_2=[]
    for i in range(0,size):
        y_range_2.append(y_range_1)
    y_range_2_flat = list(itertools.chain(*y_range_2)) # flattens list

    return x_range_2_flat, y_range_2_flat


# ---------------------------------------------------------------------------
# matplotlib fig to np
# ---------------------------------------------------------------------------
def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = np.fromstring ( fig.canvas.tostring_argb(), dtype=np.uint8 )
    buf.shape = ( w, h,4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = np.roll ( buf, 3, axis = 2 )
    return buf


# ---------------------------------------------------------------------------
# matplotlib fig to PIL
# ---------------------------------------------------------------------------
def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.frombytes( "RGBA", ( w ,h ), buf.tostring( ) )


# ---------------------------------------------------------------------------
# generates the 3D as cropepd matplotlib image and returns it
# ---------------------------------------------------------------------------
def massing_image (polylines_massing, linetype_massing, size):
    #colour thresholds
    threshold1=10
    threshold2=100
    threshold3=160
    
    #generates basing image and resizes
    img= np.zeros((700,700,3), np.uint8)
    img.fill(255)
    img=bdf.draw_paths_base (polylines_massing, linetype_massing, 'any', 'any', img, save='False')
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dim=(size ,size)
    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA) # resizes images
    img=255-img
    
    #segments image in three bands
    img1 = img > threshold1
    img2 = img > threshold2
    img2_neg = img < threshold2
    img3 = img > threshold3
    img3_neg = img < threshold3
    
    level1 = img1*img2_neg*1
    level2 = img2*img3_neg*2
    level3 = img3*3
    
    #groups them in array of values 1,2,3
    total = level1 + level2 + level3
    
    # generates a list
    total_flat = total.flatten()
    img_list = total_flat.tolist()
    
    #generates list of cubes to extrude
    thickness=size/(size-1)
    positions = grid_points(size)
    
    x_pos = []
    y_pos = []
    z_pos = []
    x_size = []
    y_size = []
    z_size = []
    color_list=[]
    
    color1=(230/255, 196/255, 138/255)
    color2=(255/255, 110/255, 94/255)
    color3=(255/255, 0/255, 0/255)
    
    scale_v=3/380*70
    z1=pdt.massing_height[1]
    z2=pdt.massing_height[2]
    z3=pdt.massing_height[3]
    
    for i in range (0, len(img_list)):
        if img_list[i] == 1:
            x_pos.append(positions[0][i])
            y_pos.append(positions[1][i])
            z_pos.append(0)
            x_size.append(thickness)
            y_size.append(thickness)
            z_size.append(z1*scale_v)
            color_list.append(color1)
        if img_list[i] == 2:
            x_pos.append(positions[0][i])
            y_pos.append(positions[1][i])
            z_pos.append(0)
            x_size.append(thickness)
            y_size.append(thickness)
            z_size.append(z2*scale_v)
            color_list.append(color2)
        if img_list[i] == 3:
            x_pos.append(positions[0][i])
            y_pos.append(positions[1][i])
            z_pos.append(0)
            x_size.append(thickness)
            y_size.append(thickness)
            z_size.append(z3*scale_v)      
            color_list.append(color3)        
    
    # generates the massing         
    fig = plt.figure(num=None, figsize=(8, 6), dpi=180, facecolor='w', edgecolor='k')
    ax = plt.axes(projection="3d", aspect = 'equal')
    ax.bar3d(x_pos, y_pos, z_pos, x_size, y_size, z_size , color=color_list)
    ax.set_xlim(0, 70)
    ax.set_ylim(0, 70)
    ax.set_zlim(0, 70)
    ax.set_axis_off()
    massing_image = fig2img( fig )
    
    # brings image as background
    fig = plt.figure(num=None, figsize=(8, 6), dpi=180, facecolor='w', edgecolor='k')
    ax = plt.axes(projection="3d", aspect = 'equal')
    file_to_read = pdt.link_base_image_png
    fn = get_sample_data(file_to_read, asfileobj=False)
    img = read_png(fn)
    xx, yy = ogrid[0:img.shape[0], 0:img.shape[1]]
    X = xx
    Y = yy
    Z1 = np.ones(X.shape)
    ax.plot_surface(X, Y, Z1, rstride=1, cstride=1, facecolors=img, shade=False)
    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.set_zlim(0, size)
    ax.set_axis_off()
    background_image = fig2img ( fig )
    
    # removes white pixels from massing for overlay
    pixdata = massing_image.load()
    width, height = massing_image.size
    for y in range(height):
        for x in range(width):
            if pixdata[x, y] == (255, 255, 255, 255):
                pixdata[x, y] = (255, 255, 255, 0)
    
    # overlays two images
    background_image.paste(massing_image, (0, 0), massing_image)
    
    # crops to adequate size
    left = 400
    top = 520
    right = 1080
    bottom = 900
    background_image = background_image.crop((left, top, right, bottom)) 


    return background_image

    

#%%
# test of generationof cube of data
#user_id='1579731923367'
#databse_root=os.path.join(pdt.root_participation_directory,user_id)
#database_filepath = os.path.join(databse_root, user_id + '_database.json')
#
#exercise = pdt.exercises[1]  #import massing data for this feedback operation
#
#data_import = dbm.line_data_from_database(database_filepath, user_id,exercise)
#polylines_massing = data_import[0]
#linetype_massing = data_import[1]
#size = 70
#
#background_image = massing_image (polylines_massing, linetype_massing, size)
#
#masssing_image_filename= os.path.join(databse_root, user_id + '_massing_image.png')
#background_image.save(masssing_image_filename)
