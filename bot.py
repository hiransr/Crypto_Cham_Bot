import telebot
import db
import confi
import pyotp
import qrcode
from PIL import Image
bot = telebot.TeleBot(confi.telegramapi, parse_mode="HTML") # You can set parse_mode by default. HTML or MARKDOWN
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hlo")

#Sign-up and Password
@bot.message_handler(commands=['Signup'])
def signup(message):
    if(db.checkdata(message.chat.id,"chatid")):
        bot.send_message(message.chat.id,"User Already exist")
        bot.send_message(message.chat.id,f"Your username is {db.getfield(message.chat.id,'username')}")
        bot.send_message(message.chat.id, "Login")
        msg = bot.send_message(message.chat.id, "Enter Your UserName: ")
        bot.register_next_step_handler(msg,login)
        return
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
    key=pyotp.random_base32()    #TOTP
    db.updatedata(message.chat.id,"totp",key,"signup")
    bot.send_message(message.chat.id,f"Totp for 2Factor Authentication is <code>{key}</code>") #<code> to select
    ######## QR code
    tt = pyotp.totp.TOTP(key).provisioning_uri(name="Hiran", issuer_name='Crypto Cham')
    img = qrcode.make(key)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=5, border=4,)
    qr.add_data(tt)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    bot.send_photo(message.chat.id, img, f"<code>{key}</code>")
    #################
    msg = bot.send_message(message.chat.id, "Enter 2FA Code: ")
    bot.register_next_step_handler(msg,checkotp)
def checkotp(message):
    totp = pyotp.TOTP(db.getfield(message.chat.id,"totp"))
    if(totp.verify(message.text)):
        bot.send_message(message.chat.id,"Signup Successful")
        bot.send_message(message.chat.id, "Login")
        msg = bot.send_message(message.chat.id, "Enter Your UserName: ")
        bot.register_next_step_handler(msg,login)
    else:
        msg = bot.send_message(message.chat.id, "Invalid Otp \nEnter again: ")
        bot.register_next_step_handler(msg,checkotp)
def login(message):
    if(db.checkdata(message.text,"username")):
        msg = bot.send_message(message.chat.id, "Enter Your Password: ")
        bot.register_next_step_handler(msg,passw)
    else:
        msg = bot.send_message(message.chat.id, "Invalid UserName and Password \nEnter Your UserName again: ")
        bot.register_next_step_handler(msg,login)
def passw(message):
    if(db.checkdata(message.text,"pass")):
        db.insertdata(message.chat.id,"chatid","signup")
        bot.send_message(message.chat.id,"Login Successful")
    else:
        msg=bot.send_message(message.chat.id,"Incorrect Username and Password \nEnter again: ")
        bot.register_next_step_handler(msg,login)
bot.polling()