import face_recognition
import numpy as np
import os
from flask import Flask, jsonify, request,make_response
from flask_cors import CORS
# MySQLdbのインポート
import MySQLdb
# import matplotlib.pyplot as pyplot

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
 
# データベースへの接続とカーソルの生成

""" cur.close
connection.close """

@app.route("/faceId",methods=["POST"])
def faceId():

    file = request.files['image']

    if file and file.filename:
        print(file)
    
    # 画像読み込み
    target_dir_name = "./images"
    target_file_name = "haruma_target.jpg"
    target_path = target_dir_name + "/" + target_file_name
    dir_name = "./images"
    files = os.listdir(dir_name)
    files_path = []
    for filename in files:
        if filename == ".DS_Store" or filename == target_file_name:
            continue
        files_path.append(dir_name + "/" + filename)
    print(files_path)

    known_imgs_path = files_path

    known_face_imgs = []
    for path in known_imgs_path:
        img = face_recognition.load_image_file(path)
        known_face_imgs.append(img)

    face_img_to_check = face_recognition.load_image_file(file)

    known_face_locs = []
    for img in known_face_imgs:
        # print("エンコード中")
        loc = face_recognition.face_locations(img,model="hog")
        known_face_locs.append(loc)
        # print("エンコード終了")

    face_loc_to_check = face_recognition.face_locations(face_img_to_check,model="hog")
    print("顔の領域(素材):",known_face_locs)
    print("顔の領域(タゲ)",face_loc_to_check)

    known_face_encodings = []
    for img, loc in zip(known_face_imgs, known_face_locs):
        (encoding,) = face_recognition.face_encodings(img, loc)
        known_face_encodings.append(encoding)

    (face_encoding_to_check,) = face_recognition.face_encodings(
        face_img_to_check, face_loc_to_check
    )

    # print("特徴点:",known_face_encodings)
    # print("特徴点:",face_encoding_to_check)

    """ matches = face_recognition.compare_faces(known_face_encodings, face_encoding_to_check)
    print(matches) """


    dists = face_recognition.face_distance(known_face_encodings, face_encoding_to_check)
    print(dists)

    response = {
        "data":"",
        "status": 404
    }

    if dists.min() < 0.43:
        index_min = np.argmin(dists)
        print(index_min)
        print(files_path)
        print(known_imgs_path[index_min] + "は本人です")
        response["status"] = 200
        response["data"] = known_imgs_path[index_min]
    else:
        print("本人のデータは存在しません")
        response["data"] = "not match"
    return make_response(jsonify(response))

def is_picture():
    print("ispic")

@app.route("/register",methods=["POST"])
def register_employee():

    connection = MySQLdb.connect(
        host='mysql',
        user='root',
        passwd='password',
        db='employee',
        charset='utf8'
    )

    file = request.files['image']
    print(file)
    face_img_to_check = face_recognition.load_image_file(file)
    face_loc_to_check = face_recognition.face_locations(face_img_to_check,model="hog")
    response = {
        "data":"not face",
        "status":500
    }
    if(len(face_loc_to_check) == 0):
        return make_response(jsonify(response))
    else:
        name = str(request.form["name"])
        age = int(request.form["age"])

        cur = connection.cursor()
        sql = "insert into employee values(null,'%s',%s)" % (name,age)
        print(sql)
        cur.execute(sql)
        connection.insert_id()
        cur.lastrowid

        cur.execute('SELECT last_insert_id()')
        # print(cur.fetchone()[0])

        emp_id = str(cur.fetchone()[0])
        
        savefile = request.files['image']

        # ???解決したがなんだこれ
        savefile.stream.seek(0)
        savefile_name = emp_id + ".jpg"
        savefile.save(os.path.join("./images",savefile_name))

        connection.commit()
        cur.close()
        connection.close()
        response["data"] = emp_id
        response["status"] = 200
        return make_response(jsonify(response))




if __name__ == "__main__":
    print("Starting by generating encodings for found images...")
    # Start app
    print("Starting WebServer...")
    app.run(host='0.0.0.0', port=23450, debug=True)