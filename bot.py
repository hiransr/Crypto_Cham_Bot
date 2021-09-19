import telebot
import db
import confi
bot = telebot.TeleBot(confi.telegramapi, parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hi, how are you doing?")


bot.polling()