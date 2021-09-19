import telebot
import db
import confi
bot = telebot.TeleBot(confi.telegramapi, parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hi, how are you doing?")

#Sign-up and Password
@bot.message_handler(commands=['Signup'])
def signup(message):
    db.insertdata(message.chat.id,"chatid","signup")
    msg = bot.send_message(message.chat.id, "Enter User Name: ")
    bot.register_next_step_handler(msg, username) #spass= sign password
def username(message):
    db.updatedata(message.chat.id,"username",message.text,"signup")
    bot.send_message(message.chat.id,f"Your Username is {message.text}")
    msg = bot.send_message(message.chat.id, "Enter Password: ")
    bot.register_next_step_handler(msg, password) 
def password(message):
    db.updatedata(message.chat.id,"pass",message.text,"signup")
    bot.send_message(message.chat.id,"Signup Successful")

bot.polling()