#import MySQLdb as mdb
import pymongo
import sys
import os
import pprint
import unicodedata
from pymongo import MongoClient
from flask import jsonify
from flask import Flask, render_template, request,redirect, url_for ,session,escape,json
import cv2, os
import numpy as np
from PIL import Image
import algorithm
from algorithm import predict_confidence


# Connection with MongoDB database :
client = MongoClient('mongodb://akhilesh_123:cmpe273@ds123361.mlab.com:23361/cmpe273')
db = client['cmpe273']
collection = db['photorecog']

filename = '';
originalImage = ''
tobeCompared = ''

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
print "app path : " + APP_ROOT

app = Flask(__name__,static_url_path='/static', template_folder="templates")


#secret key
app.secret_key = 'dsjksdh88989djj'


@app.route("/",methods=["GET"])
def defaultPage():
    print "Arrived in index - ROOT"
    return render_template("Index.html")

@app.route("/home",methods=["GET"])
def homePage():
    print "Arrived in index - home"
    return render_template("Home.html")

@app.route("/compare",methods=["GET"])
def comparePage():
    print "Arrived in index - Compare"
    if 'userId' in session:
        print "found"
        return render_template("compare.html")
    else:
        print "not found"
        return redirect(url_for('loginPage'))

@app.route("/login",methods=["GET"])

def loginPage():
    print "Arrived in index - Login"
    return render_template("login.html")

@app.route("/signUp",methods=["GET"])
def signUpPage():
    print "Arrived in index - signUp"
    return render_template("signUp.html")

@app.route("/upload",methods=["GET"])
def uploadPage():
    print "Arrived in index - upload"
    if 'userId' in session:
        return render_template("upload.html")
    else:
        return redirect(url_for('loginPage'))

@app.route("/logout",methods=["GET"])
def logout():
    print "Arrived in index - Logout"
    if 'userId' in session:
         # remove the userId from the session if it is there
        print "clearing sesssion"
        session.clear()
        print "session cleared"
        return redirect(url_for('homePage'))
    else:
        print 'error'

@app.route("/login",methods=["POST"])
def index():
    studentId = request.get_json()
    print studentId
    count = collection.count({"_id" : studentId})
    print count
    response = {'status' : '','msg' : ''}
    if count == 0:
        print "NO record found"
        response['status'] = "404"
        response['msg'] = "student Id not found"
        print response
    else:
        print "found user...."
        response['status'] = "200"
        response['msg'] = "existing"
        session['userId']= studentId;
        print studentId;
        print session['userId']
        print response
    return jsonify(response)

@app.route("/signUp",methods=["POST"])
def signUp():
    message = request.data
    dataDict = json.loads(message)

    print dataDict['studentId']
    print dataDict['firstName']
    print dataDict['lastName']
    response = {'status' : '','msg' : ''}
    result = db.photorecog.insert_one({
                "_id" : dataDict['studentId'],
                "firstName" : dataDict['firstName'],
                "lastName" : dataDict['lastName'],
                "path" : {
                "originalImage" : "",
                "tobeComparedImage" : ""
                }
        })
    print result
    response['status'] = 200
    response['msg'] = "successfully registered"
    session['userId']= dataDict['studentId']
    print session['userId']
    return jsonify(response)



@app.route("/uploadfile/<studentId>", methods=['POST'])
def upload(studentId):
    print "in Upload file"
    print request.files;
    target = os.path.join(APP_ROOT, 'static')

    if not os.path.isdir(target):
        os.mkdir(target)
    target = os.path.join(APP_ROOT, 'static/images')

    if not os.path.isdir(target):
        os.mkdir(target)
    target = os.path.join(APP_ROOT, 'static/images/' + studentId)
    print(target)

    if not os.path.isdir(target):
        os.mkdir(target)

    for file in request.files.getlist("file"):
        # print "filename : "
        print(file)
        filename =  studentId + '-1'
        # print type(filename)
        destination = "/".join([target, filename])
        file.save(destination)
        # print destination
        destination = unicodedata.normalize('NFKD', destination).encode('ascii','ignore')
        result = db.photorecog.update_one({"_id" : studentId},{"$set" : {"path.originalImage" : destination}})
        # print result
    return render_template("complete.html")

@app.route("/index1/<studentId>")
def index1(studentId):
    return render_template("upload.html",studentId=studentId)


# The file location will stored across the Student Id, so while fetching the file from database, he needs to query wrt to StudentId
# and get the image and compare with the new image.
#
#

@app.route("/compare/<studentId>", methods=['POST'])
def compare(studentId):
    print "in Compare file"
    print request.files;
    target = os.path.join(APP_ROOT, 'static')

    if not os.path.isdir(target):
        os.mkdir(target)
    target = os.path.join(APP_ROOT, 'static/images')

    if not os.path.isdir(target):
        os.mkdir(target)
    target = os.path.join(APP_ROOT, 'static/images/' + studentId)
    print(target)

    if not os.path.isdir(target):
        os.mkdir(target)

    for file in request.files.getlist("file"):
        # print "filename : "
        print(file)
        filename =  studentId + '-2'
        # print type(filename)
        destination = "/".join([target, filename])
        file.save(destination)
        # print destination
        destination = unicodedata.normalize('NFKD', destination).encode('ascii','ignore')
        result = db.photorecog.update_one({"_id" : studentId},{"$set" : {"path.tobeComparedImage" : destination}})
        # print result
    result = db.photorecog.find({"_id" : studentId},{"path" : "1"});

    print "result is : "
    for r in result:
        originalImagePath = r["path"]["originalImage"]
        tobeComparedImagePath = r["path"]["tobeComparedImage"]

    confidences = predict_confidence(originalImagePath,tobeComparedImagePath,studentId)

    for confidence in confidences:
        print confidence

    return render_template("complete.html")


if __name__ == "__main__":
    # print "in main : creating connection"
    # curr = collection.find();
    # for document in curr:
    #     print(document);

    app.run(port=5000, debug=True)