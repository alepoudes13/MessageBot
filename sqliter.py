import sqlite3
import config
from replit import db
from datetime import datetime
# 
class DBConnection(object):
    def incr_cur_task(self):
        db['current_task'] += 1
    #
    def get_cur_task(self):
        return db['current_task']
    #
    def add_additional_text(self, id , text):
        db[str(id)] = text
    # 
    def get_additional_text(self, id):
        return db.get(str(id))
    # 
    def change_text(self, text):
        db['settings'][2] = str(text)
    # 
    def change_photo(self, name, id):
        db['settings'][1] = name
        db['photo'] = id
    # 
    def get_photo_id(self):
        return db.get('photo')
    #
    def settings(self, ):
        return db.get('settings')
    # 
    def setSpam(self, spam):
        db['settings'][3] = spam
    #
    def setTimeOut(self, time):
        db['settings'][4] = int(time)
    #
    def setChannels(self, list):
        db['channels'] = list
    #
    def getChannels(self):
        return db['channels']
    #
    def setNextPoint(self, next_point):
        db['next_point'] = next_point.strftime("%d/%m/%Y, %H:%M")
    #
    def setNextPointNone(self):
        db['next_point'] = None
    #
    def getNextPoint(self):
        next_point = db.get('next_point')
        if next_point != None:
          next_point = datetime.strptime(next_point, "%d/%m/%Y, %H:%M")
        return next_point
    #