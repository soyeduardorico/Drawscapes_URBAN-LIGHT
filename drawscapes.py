# ----------------------------------------------------------------------------------
# For running flask on pythonanywhere  see: https://www.youtube.com/watch?v=M-QRwEEZ9-8
# For session generation see https://www.youtube.com/watch?v=T1ZVyY1LWOg
# For general tutorials on flask: https://www.youtube.com/watch?v=MwZwr5Tvyxo
# ----------------------------------------------------------------------------------
from flask import Flask, render_template, url_for, request, jsonify, send_from_directory, session, redirect, make_response, flash
import time
import os

from tinydb import TinyDB

from drawing_app_functions import drawscapes_feedback_lines, drawscapes_feedback_massing
from drawing_app_functions import drawscapes_draw_base_from_feedback, drawscapes_draw_base, save_land_uses, drawscapes_draw_base_for_land_use
from feedback import generate_feedback_images
import project_data as pdt
import drawing_app_functions as daf
import database_management as dbm
import feedback as fdb


# ----------------------------------------------------------------------------------
# instantiates app and generates cookie to be passed to client
# ----------------------------------------------------------------------------------
app=Flask(__name__)
app.secret_key = os.urandom(24)
absFilePath = os.path.dirname(__file__)
root_data = os.path.join(absFilePath,  'data')


# ----------------------------------------------------------------------------------
# initiates Redis Queue when running in Ubuntu. Comment when running tests on Windows
# ----------------------------------------------------------------------------------
#import redis
#from rq import Queue
#r=redis.Redis()
#q=Queue(connection=r)


# -----------------------------------------------------------------------------------------
# renders index page
# -----------------------------------------------------------------------------------------
@app.route ('/')
def index():
    millis = int(round(time.time() * 1000))
    variable = str(millis)
    session['user'] = variable
    session_folder=os.path.join(root_data, variable)

    # generates local folder
    os.mkdir(session_folder)

    # generates local database
    user_db =os.path.join(session_folder,variable + '_database.json')
    db = TinyDB(user_db)
    db.close()

    return render_template ('index.html')


# -----------------------------------------------------------------------------------------
# closes session
# -----------------------------------------------------------------------------------------
@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return 'Dropped'

# -----------------------------------------------------------------------------------------
# fabricates a url for non static folder a seen in https://www.youtube.com/watch?v=Y2fMCxLz6wM
# -----------------------------------------------------------------------------------------
@app.route('/data/<filename>')
def data(filename):
    target_directory = 'data/' + session['user']
    return send_from_directory(target_directory, filename)

@app.route('/overall_results/<filename>')
def overall_results(filename):
    target_directory = 'overall_results/'
    return send_from_directory(target_directory, filename)


# -----------------------------------------------------------------------------------------
# Routes to different web pages
# -----------------------------------------------------------------------------------------
@app.route('/drawscapes_intro')
def drawscapes_intro():
    return render_template ('drawscapes_intro.html',
        title = 'network design for session ' + session['user'])

@app.route('/drawscapes')
def drawscapes():
    # defines session number and generates folder for further saving files
    return render_template ('drawscapes.html',
        title = 'network design for session ' + session['user'])

@app.route('/drawscapes_massing/<filename>')
def drawscapes_massing(filename):
    return render_template ('drawscapes_massing.html',
        title = 'massing design for session ' + session['user'],
        imagename=filename)

@app.route('/drawscapes_land_use/<filename>')
def drawscapes_land_use(filename):
    return render_template ('drawscapes_land_use.html',
        title = 'massing design for session ' + session['user'],
        imagename=filename)

@app.route('/drawscapes_feedback/<filename>')
def drawscapes_feedback(filename):
    return render_template ('drawscapes_feedback.html', imagename=filename)

@app.route('/drawscapes_form')
def drawscapes_form():
    return render_template ('drawscapes_form.html')

@app.route('/drawscapes_thanks')
def drawscapes_thanks():
    return render_template ('drawscapes_thanks.html')

# -----------------------------------------------------------------------------------------
# Develops feedback on connectivity of lines and serves it to front end
# -----------------------------------------------------------------------------------------
@app.route('/drawscapes_connectivity_feedback', methods=["GET", "POST"])
def drawscapes_connectivity_feedback():
    millis = int(round(time.time() * 1000))
    session_folder=os.path.join(root_data,  str(session['user'])) # uses same folder as folder session
    file_name = str(session['user']) + '_' +str(millis)
    folder_name=session['user']
    data = request.json

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback into the queue. Activate on Ubuntu
    # ----------------------------------------------------------------------------------
    #job = q.enqueue(drawscapes_feedback_lines, data, file_name, session_folder, folder_name)
    #while job.is_finished != True:
         #time.sleep(0.1)

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback. Activate on Windows
    # ----------------------------------------------------------------------------------
    drawscapes_feedback_lines (data, file_name, session_folder, folder_name)

    # sends name of file back to browswer
    image_feedback=  file_name + '_graph.jpg' # defines name of image for feedbak and passes it to template
    return jsonify(image_feedback)


# -----------------------------------------------------------------------------------------
# Generates a base for massign exercise from front end and saves also to database
# -----------------------------------------------------------------------------------------
@app.route('/drawscapes_massing_base', methods=["GET", "POST"])
def drawscapes_massing_base():
    # defines drawing number within the session
    millis = int(round(time.time() * 1000))
    session_folder=os.path.join(root_data, session['user']) # uses same folder as folder session
    file_name= session['user']+'_'+ str(millis)
    folder_name=session['user']
    exercise = pdt.exercises[0]
    data = request.json

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback into the queue. Activate on Ubuntu
    # ----------------------------------------------------------------------------------
    #job = q.enqueue(drawscapes_draw_base, data, exercise, file_name, session_folder, folder_name)
    #while job.is_finished != True:
        #time.sleep(0.1)

    # ----------------------------------------------------------------------------------
    # brings json data and calls for development of image style input to the canvas. Activate on Windows
    # ----------------------------------------------------------------------------------
    drawscapes_draw_base (data, exercise, file_name, session_folder, folder_name) # Draws paths in the small scale base

    # sends name of file back to browswer
    image_feedback=  file_name + '_base.jpg' # defines name of image for feedbak and passes it to template
    return jsonify(image_feedback)


# -----------------------------------------------------------------------------------------
# Generates a base for massign exercise from latest entry in DATABASE. Unsed to come from Feedback stage
# -----------------------------------------------------------------------------------------
@app.route('/drawscapes_massing_base_databse', methods=["GET", "POST"])
def drawscapes_massing_base_database():
    # defines drawing number within the session
    millis = int(round(time.time() * 1000))
    session_folder=os.path.join(root_data, session['user']) # uses same folder as folder session
    file_name= session['user']+'_'+ str(millis)
    user_id = session['user']
    exercise = 0
    database = pdt.databse_filepath

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback into the queue. Activate on Ubuntu
    # ----------------------------------------------------------------------------------
    #job = q.enqueue(drawscapes_draw_base_from_feedback, database, exercise, file_name, session_folder, user_id)
    #while job.is_finished != True:
        #time.sleep(0.1)

    # ----------------------------------------------------------------------------------
    # Calls for development of image for bases reading last entry in databse. Activate on Windows
    # ----------------------------------------------------------------------------------
    drawscapes_draw_base_from_feedback (database, exercise, file_name, session_folder, user_id) # Draws paths in the small scale base

    # sends name of file back to browswer
    image_feedback=  file_name + '_base.jpg' # defines name of image for feedbak and passes it to template
    return jsonify(image_feedback)


# -----------------------------------------------------------------------------------------
# Develops feedback on massing quantities and serves it to front end
# -----------------------------------------------------------------------------------------
@app.route('/drawscapes_massing_feedback', methods=["GET", "POST"])
def drawscapes_massing_feedback():
    # defines drawing number within the session
    millis = int(round(time.time() * 1000))
    file_name= session['user']+'_'+ str(millis)
    user_id = session['user']
    data = request.json

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback into the queue. Activate on Ubuntu
    # ----------------------------------------------------------------------------------
    #job = q.enqueue(drawscapes_feedback_massing, data, file_name, user_id)
    #while job.is_finished != True:
        #time.sleep(0.1)

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback. Activate on Windows
    # ----------------------------------------------------------------------------------
    drawscapes_feedback_massing (data, file_name, user_id)

    # sends name of file back to browswer
    image_feedback=  file_name + '_massing.jpg' # defines name of image for feedbak and passes it to template
    return jsonify(image_feedback)


@app.route('/drawscapes_land_use_base', methods=["GET", "POST"])
def drawscapes_land_use_base():
    # defines drawing number within the session
    millis = int(round(time.time() * 1000))
    session_folder=os.path.join(root_data, session['user']) # uses same folder as folder session
    file_name= session['user']+'_'+ str(millis)
    folder_name=session['user']
    data = request.json

    # ----------------------------------------------------------------------------------
    # brings json data and calls for development of land use base drawing usign lines and massing. Activate on Ubuntu
    # ----------------------------------------------------------------------------------
    #job = q.enqueue(drawscapes_draw_base_for_land_use, data, file_name, session_folder, folder_name)
    #while job.is_finished != True:
        #time.sleep(0.1)

    # ----------------------------------------------------------------------------------
    # brings json data and calls for development of land use base drawing usign lines and massing. Activate on Windows
    # ----------------------------------------------------------------------------------
    drawscapes_draw_base_for_land_use (data, file_name, session_folder, folder_name)

    # sends name of file back to browswer
    image_feedback=  file_name + '_landscape_base.jpg' # defines name of image for feedbak and passes it to template
    return jsonify(image_feedback)


# -----------------------------------------------------------------------------------------
# Generates a base for land use exercise from latest entry in DATABASE. Unsed to come from Feedback stage
# -----------------------------------------------------------------------------------------
@app.route('/drawscapes_land_use_base_databse', methods=["GET", "POST"])
def drawscapes_land_use_base_databse():
    # defines drawing number within the session
    millis = int(round(time.time() * 1000))
    session_folder=os.path.join(root_data, session['user']) # uses same folder as folder session
    file_name= session['user']+'_'+ str(millis)
    user_id = session['user']
    exercise = 1
    database = pdt.databse_filepath

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback into the queue. Activate on Ubuntu
    # ----------------------------------------------------------------------------------
    #job = q.enqueue(drawscapes_draw_base_from_feedback, database, exercise, file_name, session_folder, user_id)
    #while job.is_finished != True:
        #time.sleep(0.1)

    # ----------------------------------------------------------------------------------
    # Calls for development of image for bases reading last entry in databse. Activate on Windows
    # ----------------------------------------------------------------------------------
    drawscapes_draw_base_from_feedback (database, exercise, file_name, session_folder, user_id) # Draws paths in the small scale base

    # sends name of file back to browswer
    image_feedback=  file_name + '_landscape_base.jpg' # defines name of image for feedbak and passes it to template
    return jsonify(image_feedback)


@app.route('/drawscapes_save_land_uses', methods=["GET", "POST"]) #complete when generating landscape
def drawscapes_save_land_uses():
    # defines drawing number within the session
    millis = int(round(time.time() * 1000))
    user_id = session['user']
    file_name= user_id +'_'+ str(millis)
    folder_name = session['user'] # Used as base for drawscapes_massing.html canvas base
    data = request.json

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback into the queue. Activate on Ubuntu
    # ----------------------------------------------------------------------------------
    #job = q.enqueue(generate_feedback_images, data, pdt.databse_filepath, user_id, file_name)
    #while job.is_finished != True:
        #time.sleep(0.1)

    # ----------------------------------------------------------------------------------
    # brings json data and calls for development of image style input to the canvas. Activate on Windows
    # ----------------------------------------------------------------------------------
    generate_feedback_images (data, pdt.databse_filepath, user_id, file_name)

    return jsonify(file_name)


@app.route('/drawscapes_save_text', methods=["GET", "POST"])
def drawscapes_save_text():
    session_folder=os.path.join(root_data, session['user']) # uses same folder as folder session
    user_id= session['user']
    file_name= user_id +'_'+ str(millis)
    file_path = os.path.join(session_folder, file_name + '.txt')

    # ----------------------------------------------------------------------------------
    # brings json data and calls drawing feedback.
    # ----------------------------------------------------------------------------------
    data = request.json
    data=str(data) # just in case
    daf.save_survey_results (data, session_folder, file_name, user_id)

    dropsession()

if __name__ == "__main__":
    millis=0
    points = []
    number_iterations  = 1
    # serve(app, host='0.0.0.0', port=80)
    app.run(debug=True, threaded=True)# requires threads to run parallel requests independetly

