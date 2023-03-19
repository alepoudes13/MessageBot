from replit import db
#db.clear()
db['current_task'] = 0

if db.get('settings') == None:
  
  db['settings'] = [1, None, 'text', 0, 1]
  db['channels'] = None
  db['next_point'] = None

  print("db inited")