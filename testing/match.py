import face_recognition
import numpy as np
import os
import json
import codecs
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
        "name":"",
        "age": 0,
        "status": 404
    }

    if dists.min() < 0.43:
        connection = MySQLdb.connect(
            host='mysql',
            user='root',
            passwd='password',
            db='employee',
            charset='utf8'
        )
        index_min = np.argmin(dists)
        print(index_min)
        print(files_path)
        print(known_imgs_path[index_min] + "は本人です")
        emp_id = files[index_min].strip(".jpg")

        cur = connection.cursor()
        cur.execute("SELECT * FROM employee WHERE id = %s" % (emp_id,))
        emp_data = cur.fetchone()

        response["status"] = 200
        response["data"] = "match!"
        response["name"] = emp_data[1]
        response["age"] = emp_data[2]
        connection.close()
    else:
        print("本人のデータは存在しません")
        response["data"] = "not match"
    return make_response(jsonify(response))

def is_picture():
    print("ispic")

@app.route("/register",methods=["POST"])
def register_employee():
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
        company_id = int(request.form["company_id"])

        connection = MySQLdb.connect(
            host='mysql',
            user='root',
            passwd='password',
            db='employee',
            charset='utf8'
        )

        cur = connection.cursor()
        sql = "insert into employee values(null,'%s',%s,%s)" % (name,age,company_id)
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

        cur.execute("SELECT * FROM employee")
        rows = cur.fetchall()
        for row in rows:
            print(row)

        cur.close()
        connection.close()
        response["data"] = emp_id
        response["status"] = 200
        return make_response(jsonify(response))

@app.route("/getEmployee",methods=["GET"])
def getEmployee():

    try:
        comp_id = request.args.get("company_id")

        connection = MySQLdb.connect(
            host='mysql',
            user='root',
            passwd='password',
            db='employee',
            charset='utf8'
        )
        cur = connection.cursor()
        cur.execute("SELECT * FROM employee WHERE company_id = %s collate utf8_general_ci" % (comp_id,))
        rows = cur.fetchall()
        cur.close()
        connection.close()

        response = {
            "data":[]
        }

        for row in rows:
            encoded_name = codecs.decode(row[1], 'unicode-escape')
            data = {
                "id": row[0],
                "name": row[1],
                "age": row[2],
                "company_id": row[3]
            }
            response["data"].append(data)

        return make_response(jsonify(response))

    except(ZeroDivisionError, TypeError) as e:
        print(e)
        return make_response(jsonify({"status": 500}))


@app.route("/updateEmployee",methods=["POST"])
def updateEmployee():
    emp_id = int(request.form["id"])
    emp_name =  str(request.form["name"])
    emp_age = int(request.form["age"])
    connection = MySQLdb.connect(
        host='mysql',
        user='root',
        passwd='password',
        db='employee',
        charset='utf8'
    )
    cur = connection.cursor()
    cur.execute("UPDATE employee SET name = '%s',age = %s WHERE id = %s" % (emp_name,emp_age,emp_id))

    connection.commit()
    cur.close()
    connection.close()
    response = {
        "status": 200
    }
    return make_response(jsonify(response))

@app.route("/loginCompany",methods=["POST"])
def loginCompany():
    comp_id = str(request.form["company_id"])
    comp_pass = str(request.form["password"])
    connection = MySQLdb.connect(
        host='mysql',
        user='root',
        passwd='password',
        db='employee',
        charset='utf8'
    )
    cur = connection.cursor()
    cur.execute("SELECT * FROM company WHERE company_id = %s AND company_pass = '%s'" % (comp_id,comp_pass))
    if cursor.rowcount() == 0 :
        return make_response(jsonify({"status":403}))
    comp_data = cur.fetchone()
    cur.close()
    connection.close()
    return make_response(jsonify({"status":200,"company_id":comp_data[0]}))

@app.route("/start_time",methods=["POST"])
def work_start():
        """ emp_id = int(request.form["id"])
        now_time = str(request.form["now_time"])
        end = str(request.form["end"])
        date = str(request.form["date"])
        date_next = str(request.form["date_next"]) """
        emp_id = 6
        start = "2020-10-10 09:00:00"
        date = "2020-10-10"

        connection = MySQLdb.connect(
                host='mysql',
                user='root',
                passwd='password',
                db='employee',
                charset='utf8'
        )
        cur = connection.cursor()
        sql = "select id,start from time_table where id = %s and date = '%s' " % (emp_id,date)
        cur.execute(sql)
        result = cur.fetchall()
        print("adfafadsf",result)

        # 既にデータがあるので500番エラー

        response = {
            "status": 200
        }
        if(len(result) != 0):
                response["status"] = 500
                cur.close()
                connection.close()
                return make_response(jsonify(response))

        sql = "select ADDTIME('%s 01:00:00','24:00:00')" % (date,)
        cur.execute(sql)
        result = cur.fetchone()[0]

        sql = "insert into time_table values(%s,'%s','%s','%s','%s')" % (emp_id,start,start,date,result)
        cur.execute(sql)
        connection.commit()

        sql = "select id from time_table where %s = id and '%s' = date" % (emp_id,date)
        cur.execute(sql)
        result = cur.fetchall()

        # インサート成功してデータが確認出来たら200ステータスを返す
        if len(result) != 0:
                response["status"] = 200
                cur.close()
                connection.close()
                return make_response(jsonify(response))

        response["status"] = 500
        cur.close()
        connection.close()
        return make_response(jsonify(response))


@app.route("/end_time",methods=["POST"])
def work_end():
        """ emp_id = int(request.form["id"])
        time = str(request.form["now_time"])
        date = str(request.form["date"])
        company = str(request.form["company_id"]) """
        emp_id = 6
        time = "2020-10-10 18:00:00"
        date = "2020-10-10"
        company = 1
        connection = MySQLdb.connect(
                host='mysql',
                user='root',
                passwd='password',
                db='employee',
                charset='utf8'
        )
        cur = connection.cursor()
        sql = "select start from time_table where %s = id and (date = '%s' or date_next = '%s')"% (emp_id,date,date)
        cur.execute(sql)
        result = cur.fetchall()

        response = {
            "status": 200
        }
        
        if len(result) != 0:
            # 今日か明日の出勤データが存在している
            sql = "select start from time_table where %s = id and (date = '%s' or date_next = '%s') and start = end" % (emp_id,date,date)
            cur.execute(sql)
            result = cur.fetchone()

            if len(result) != 0:
                # 出勤時間と退勤時間が同じ→まだ退勤していないデータがある
                print("result0",result[0])
                sql = "select hour(timediff('%s', '%s'))" % (time,result[0])
                cur.execute(sql)
                result = cur.fetchone()[0]
                print("hour",result)
    
                if(result >= 15):
                    # 410→勤務限界時間をオーバー
                    response["status"] = 410
                    cur.close()
                    connection.close()
                    return make_response(jsonify(response))
                    
                else:
                    sql = "update time_table set end = '%s' where id = %s and date = '%s' or date_next = '%s'" % (time,emp_id,date,date)
                    cur.execute(sql)
                    connection.commit()
                    response["status"] = 200
                    cur.close()
                    connection.close()
                    return make_response(jsonify(response))

            else:
                # 出勤時間と退勤時間が違うデータがある
                # 411→今日はもう退勤済みです
                response["status"] = 411
                cur.close()
                connection.close()
                return make_response(jsonify(response))
            
        else:
            # 今日か明日の出勤データが存在しない
            # 412→今日はまだ出勤していません
            response["status"] = 412
            cur.close()
            connection.close()
            return make_response(jsonify(response))

        # 413→不明なエラーです
        response["status"] = 413
        cur.close()
        connection.close()
        return make_response(jsonify(response))



if __name__ == "__main__":
    print("Starting by generating encodings for found images...")
    # Start app
    print("Starting WebServer...")
    app.run(host='0.0.0.0', port=23450, debug=True)