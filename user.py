from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
import config
import asyncio
from main import bot, db
import random
from datetime import datetime, timedelta

client = Client('client', config.API_ID, config.API_HASH)

async def try_login():
  global client
  client = Client(":memory:", config.API_ID, config.API_HASH)
  return await client.connect()


client.start()

lst = []
forbidden_ids = []

async def reset_chats():
  forbidden_ids.clear()
  db.setChannels(await get_chats())
  return db.getChannels()


async def get_chats():
  global lst
  lst.clear()
  async for dialog in client.get_dialogs():
    """dialog.chat.type == ChatType.SUPERGROUP or """
    if (dialog.chat.type == ChatType.GROUP or dialog.chat.type
        == ChatType.SUPERGROUP) and not dialog.chat.id in forbidden_ids:
      lst.append({
        'title': dialog.chat.first_name or dialog.chat.title,
        'id': dialog.chat.id
      })
  return lst


async def leave_from_channel(id):
  global lst
  try:
    db.add_additional_text(id, None)
    forbidden_ids.append(int(id))
    lst = [i for i in lst if not (i['id'] == int(id))]
    db.setChannels(lst)
    return True
  except:
    return False


async def spamming(spam_list, settings, task_id):
  while settings[3] == 1 and task_id == db.get_cur_task():  # БЕСКОНЕЧНЫЙ ЦИКЛ
    next_point = db.getNextPoint()
    if next_point != None:
      wait = max(0, next_point.timestamp() - datetime.now().timestamp())
      await asyncio.sleep(wait)
    else:
      break
    if task_id != db.get_cur_task():
      break
    for chat in spam_list:  # ПРОХОДИТ ПО ВСЕМ ЧАТАМ
      if chat['id'] in forbidden_ids:
        continue
      settings = db.settings()
      if settings[3] == 0:
        db.setNextPointNone()
        return False
      try:
        if settings[1] != None:
          await client.send_photo(chat['id'],
                                  photo=settings[1],
                                  caption=f"{settings[2]}\n\n{chat['text']}",
                                  parse_mode=ParseMode.HTML)
          await bot.send_message(
            config.ADMIN,
            f'[LOG] Cообщение в {chat["title"]} было успешно отправленно.')
          print('success_photo')
        else:
          await client.send_message(chat['id'],
                                    f"{settings[2]}\n\n{chat['text']}")
          await bot.send_message(
            config.ADMIN,
            f'[LOG] Cообщение в {chat["title"]} было успешно отправленно.')
          print('success')
      except Exception as e1:
        try:
          await client.send_message(chat['id'],
                                    f"{settings[2]}\n\n{chat['text']}")
          await bot.send_message(
            config.ADMIN,
            f'[LOG] Cообщение в {chat["title"]} было успешно отправленно.')
        except Exception as e:
          print(e)
          try:
            await bot.send_message(
            config.ADMIN,
            f'[LOG] Cообщение в {chat["title"]} не было отправлено из-за ошибки: {e}'
          )
          except:
            pass
      await asyncio.sleep(random.randint(3, 5)
                          )  # ПОСЛЕ КАЖДОГО ЧАТА СПИТ 2 СЕКУНДЫ
    # КОГДА ЦИКЛ ЗАВЕРШАЕТСЯ БОТ ЛОЖИТСЯ СПАТЬ НА УКАЗАННОЕ ТОБОЙ ВРЕМЯ
    now = datetime.now()
    while next_point < now:
      next_point += timedelta(minutes=settings[4])
    db.setNextPoint(next_point)
    await asyncio.sleep(next_point.timestamp() - datetime.now().timestamp())
    settings = db.settings()
    if settings[3] != 1:
      break
    print('----------------')
