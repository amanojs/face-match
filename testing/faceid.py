##!/usr/bin/env python
# -*- coding: UTF-8 -*-
from flask import Flask,jsonify,abort,make_response
import cv2
import os

api = Flask(__name__)

@api.route("/test",methods=["GET"])
def testFunction():
    TARGET_FILE = 'target.png'
    IMG_DIR = os.path.abspath(os.path.dirname(__file__)) + '/images/'
    IMG_SIZE = (200, 200)
    file_cnt = 0
    sumall = 0
    target_img_path = IMG_DIR + TARGET_FILE
    print(target_img_path)
    target_img = cv2.imread(target_img_path, cv2.IMREAD_GRAYSCALE)
    target_img = cv2.resize(target_img, IMG_SIZE)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)

    # ORBとAKAZEは特徴点や特徴量を抽出するアルゴリズム
    # コメントアウトを調節することによりどちらでも行える

    detector = cv2.ORB_create()
    # detector = cv2.AKAZE_create()

    # ターゲットの写真の特徴点を取得する
    (target_kp, target_des) = detector.detectAndCompute(target_img, None)

    print('TARGET_FILE: %s' % (TARGET_FILE))

    files = os.listdir(IMG_DIR)
    for file in files:
        comparing_img_path = IMG_DIR + file
        try:
            comparing_img = cv2.imread(comparing_img_path, cv2.IMREAD_GRAYSCALE)
            comparing_img = cv2.resize(comparing_img, IMG_SIZE)
            # 比較する写真の特徴点を取得する
            (comparing_kp, comparing_des) = detector.detectAndCompute(comparing_img, None)
            # BFMatcherで総当たりマッチングを行う
            matches = bf.match(target_des, comparing_des)
            #特徴量の距離を出し、平均を取る
            dist = [m.distance for m in matches]
            ret = sum(dist) / len(dist)
            if file != TARGET_FILE:
                print('ターゲットファイルはないよね',file)
                file_cnt = file_cnt + 1
                sumall = sumall + ret
        except cv2.error:
        # cv2がエラーを吐いた場合の処理
            ret = 100000

        print(file, ret)

    print(sumall)
    print(file_cnt)
    averagee = sumall / file_cnt
    print(averagee)
    result = {
        "data": averagee
    }
    return make_response(jsonify(result))

if __name__ == "__main__":
    api.run(host="0.0.0.0",port=3000)