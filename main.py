#import pip
#pip.main(['install', 'tgcrypto'])
#pip.main(['install', 'pyrogram'])
#pip.main(['install', 'aiogram'])

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware

import init_db
import asyncio
import config, user
from sqliter import DBConnection
from background import keep_alive
from datetime import datetime, timedelta

loop = asyncio.get_event_loop()
bot = Bot(token=config.TOKEN, loop=loop, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
db = DBConnection()


def welcome_keyboard():
  keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
  keyboard.add(*[
    types.KeyboardButton(name)
    for name in ['❓ Available channels', '🔢 Cooldown']
  ])
  keyboard.add(
    *[types.KeyboardButton(name) for name in ['📑 Post', '➡️ START']])
  keyboard.add(
    *[types.KeyboardButton(name) for name in ['🔄 Reset channels list']])
  return keyboard


@dp.message_handler(commands=['start'])
async def process_start_command(m: types.Message):
  if m.chat.id == config.ADMIN:
    await bot.send_message(m.chat.id,
                           "💾 Sending messages to groups:\n\n",
                           reply_markup=welcome_keyboard())
  else:
    await bot.send_message(m.chat.id,
                           "❌ You can't use this bot.")


class addition(StatesGroup):
  id = State()


class post(StatesGroup):
  text = State()


class time(StatesGroup):
  timeout = State()


@dp.message_handler(state=addition.id)
async def input_report(m: types.Message, state: FSMContext):
  if m.chat.id == config.ADMIN:
    try:
      async with state.proxy() as data:
        channel_id = data['channel_id']
        db.add_additional_text(channel_id, m.text)
        await bot.send_message(
          m.chat.id, f'☑️ Text for channel {channel_id} was succesfully updated.')
        await state.finish()
    except:
      await bot.send_message(m.chat.id,
                             f"❌ Text for {channel_id} wasn't updated.")
  else:
    await bot.send_message(m.chat.id,
                           "❌ You can't use this bot.")


@dp.message_handler(state=post.text)
async def input_report(m: types.Message, state: FSMContext):
  if m.chat.id == config.ADMIN:
    db.change_text(m.text)
    await bot.send_message(m.chat.id, f'☑️ Post text was successfully updated.')
    await state.finish()
  else:
    await bot.send_message(m.chat.id,
                           "❌ You can't use this bot.")


@dp.message_handler(state=time.timeout)
async def input_report(m: types.Message, state: FSMContext):
  if m.chat.id == config.ADMIN:
    try:
      if int(m.text) >= 1:
        db.setTimeOut(m.text)
        await bot.send_message(m.chat.id,
                               f'☑️ Cooldown was successfully updated.')
      else:
        await bot.send_message(m.chat.id, f'❌ Enter a number bigger than 1.')
    except:
      await bot.send_message(m.chat.id, f'❌ Enter a number.')
    await state.finish()
  else:
    await bot.send_message(m.chat.id,
                           "❌ You can't use this bot.")


@dp.message_handler(content_types='text', state="*")
async def echo_message(m: types.Message):
  if m.chat.id == config.ADMIN:
    keyboard = types.InlineKeyboardMarkup()
    if m.text == '❓ Available channels':
      chats = db.getChannels()
      for _ in chats:
        keyboard.add(*[
          types.InlineKeyboardButton(text=name, callback_data=cb)
          for name, cb in {
            f'{_["title"]}': f'EDIT_ID:{_["id"]}'
          }.items()
        ])
      await bot.send_message(m.chat.id,
                             'All available channels:',
                             reply_markup=keyboard)
    elif m.text == '➡️ START':
      db.setSpam(1)
      keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
      keyboard.add(
        *[types.KeyboardButton(name) for name in ['🛑 Stop sending']])
      await bot.send_message(m.chat.id,
                             '😊 Sending has begun.',
                             reply_markup=keyboard)
      db.setNextPoint(datetime.now())
      await start_spam("text")
    elif m.text == '🔄 Reset channels list':
      chats = await user.reset_chats()
      for _ in chats:
        keyboard.add(*[
          types.InlineKeyboardButton(text=name, callback_data=cb)
          for name, cb in {
            f'{_["title"]}': f'EDIT_ID:{_["id"]}'
          }.items()
        ])
      await bot.send_message(m.chat.id,
                             'All available channels:',
                             reply_markup=keyboard)
    elif m.text == '🛑 Остановить спам':
      db.setSpam(0)
      db.setNextPointNone()
      await bot.send_message(m.chat.id,
                             '😊 Sending last messages and stopping',
                             reply_markup=welcome_keyboard())
    elif m.text == '🔢 Cooldown':
      settings = db.settings()
      keyboard.add(*[
        types.InlineKeyboardButton(text=name, callback_data=cb)
        for name, cb in {
          '🕘 Change cooldown': 'INTERVAL'
        }.items()
      ])
      await bot.send_message(m.chat.id,
                             f'🔃 Current cooldown {settings[4]} minutes',
                             reply_markup=keyboard)

    elif m.text == '📑 Post':
      settings = db.settings()
      try:
        with open(f'{config.DIR}{settings[1]}', 'rb') as photo:
          await bot.send_photo(m.chat.id, photo, caption=settings[2])

      except:
        await bot.send_message(m.chat.id, settings[2])

      keyboard.add(*[
        types.InlineKeyboardButton(text=name, callback_data=cb)
        for name, cb in {
          '🌆 Change photo': 'EDIT_PHOTO'
        }.items()
      ])
      keyboard.add(*[
        types.InlineKeyboardButton(text=name, callback_data=cb)
        for name, cb in {
          '📜 Change text': 'EDIT_TEXT'
        }.items()
      ])
      keyboard.add(*[
        types.InlineKeyboardButton(text=name, callback_data=cb)
        for name, cb in {
          'Delete photo': 'DEL_PHOTO'
        }.items()
      ])
      await bot.send_message(m.chat.id,
                             '🔼 Your post looks like that 🔼',
                             reply_markup=keyboard)
  else:
    await bot.send_message(m.chat.id,
                           "❌ You can't use this bot.")


@dp.callback_query_handler(lambda c: c.data, state="*")
async def poc_callback_but(c: types.CallbackQuery, state: FSMContext):
  m = c.message
  keyboard = types.InlineKeyboardMarkup()
  if 'EDIT_ID:' in c.data:
    channel_id = c.data.split(':')[1]
    try:
      addit_text = db.get_additional_text(channel_id)
    except:
      addit_text = None
    keyboard = types.InlineKeyboardMarkup(row_widht=2)
    keyboard.add(*[
      types.InlineKeyboardButton(text=name, callback_data=cb) for name, cb in {
        '❌ Remove chat': f'LFC:{channel_id}'
      }.items()
    ])

    if addit_text != None:
      keyboard.add(*[
        types.InlineKeyboardButton(text=name, callback_data=cb)
        for name, cb in {
          '🗃 Change additional text': f'ADD_ADDITIONAL:{channel_id}'
        }.items()
      ])
      await bot.send_message(
        m.chat.id,
        f'Current additional text for channel {channel_id}: {addit_text}',
        reply_markup=keyboard)
    else:
      keyboard.add(*[
        types.InlineKeyboardButton(text=name, callback_data=cb)
        for name, cb in {
          '🗃 Add text': f'ADD_ADDITIONAL:{channel_id}'
        }.items()
      ])
      await bot.send_message(
        m.chat.id,
        f'Additional text for {channel_id} was not found.',
        reply_markup=keyboard)
  elif 'ADD_ADDITIONAL:' in c.data:
    channel_id = c.data.split(':')[1]
    async with state.proxy() as data:
      data['channel_id'] = channel_id
    await bot.send_message(
      m.chat.id,
      f'💬 Enter additional text for channel [{channel_id}]:',
      reply_markup=keyboard)
    await addition.first()
  elif 'LFC:' in c.data:
    log = await user.leave_from_channel(c.data.split(':')[1])
    if log:
      text = f'☑️ You removed the channel from the list.'
    else:
      text = '❌ An error has occured.'
    await bot.send_message(m.chat.id, text)
  elif 'EDIT_TEXT' == c.data:
    await bot.send_message(m.chat.id, '📄 Enter post text:')
    await post.first()
  elif 'EDIT_PHOTO' == c.data:
    await bot.send_message(m.chat.id, '📄 Send a new photo:')
  elif 'INTERVAL' == c.data:
    await bot.send_message(
      m.chat.id, '📄 Send me the cooldown(in minutes):')
    await time.first()
  elif 'DEL_PHOTO' == c.data:
    db.change_photo(None, None)
    await bot.send_message(m.chat.id, 'Photo was deleted.')


@dp.message_handler(content_types=["photo"])
async def download_photo(m: types.Message):
  result = await m.photo[-1].download()
  db.change_photo(result.name, m.photo[-1].file_id)
  await bot.send_message(m.chat.id, '🖼 Photo was updated.')

async def start_spam(x):
  if db.settings()[3] == 1:
    spam_list = []
    for i in db.getChannels():
      try:
        addit_text = db.get_additional_text(i['id'])
        if addit_text == None:
          addit_text = ''
      except:
        addit_text = ''
      i['text'] = addit_text
      spam_list.append(i)
    settings = db.settings()
    db.incr_cur_task()
    tksNumber = asyncio.create_task(user.spamming(spam_list, settings, db.get_cur_task()))

async def wave_a_hand(x: int):
  while True:
    try:
      me = await bot.get_me()
    except:
      continue
    next_point = db.getNextPoint()
    if next_point != None:
      next_point = (next_point + timedelta(hours=3)).strftime("%d/%m/%Y, %H:%M")
    while True:
      try:
        await bot.send_message(config.DUMP_ID, str(bot.id) + ' ' + str(me.full_name) + ' - ' + str(x) + ' - ' + str(next_point))
      except:
        continue
      break
    x+=1
    await asyncio.sleep(10 * 60)

async def on_start(x):
  try:
    settings = db.settings()
    if settings[1] != None:
      file = await bot.get_file(db.get_photo_id())
      await file.download()
  except Exception as e:
    print(e)
  x = await user.client.get_me()
  config.ADMIN = x.id
  if(db.getChannels() == None):
    db.setChannels(await user.get_chats())
  asyncio.create_task(wave_a_hand(0))
  await start_spam("text")

async def sign_dead(x):
  me = await bot.get_me()
  await bot.send_message(config.DUMP_ID, str(bot.id) + ' ' + str(me.full_name) + ' ' + 'DEAD')

if __name__ == '__main__':
  keep_alive()
  while True:
    try:
      print('started')
      executor.start_polling(dp, skip_updates=True, on_startup=on_start, on_shutdown=sign_dead)
    except Exception as e:
      print(e)
