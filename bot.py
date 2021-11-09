from logging import exception
from requests.sessions import PreparedRequest
import telebot
import db
import confi
import pyotp
import qrcode
import json
import requests
import re
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from PIL import Image
from binance.client import Client
client = Client(confi.BApi, confi.BsKey)
bot = telebot.TeleBot(confi.telegramapi, parse_mode="HTML") # You can set parse_mode by default. HTML or MARKDOWN
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Hlo")

#Sign-up and Password
@bot.message_handler(commands=['Signup'])
def signup(message):
    if(db.checkdata(message.chat.id,"chatid","signup")):
        bot.send_message(message.chat.id,"User Already exist")
        bot.send_message(message.chat.id,f"Your username is {db.getfield(message.chat.id,'username','signup')}")
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
    ###############
    msg = bot.send_message(message.chat.id, "Enter 2FA Code: ")
    bot.register_next_step_handler(msg,checkotp)
def checkotp(message):
    totp = pyotp.TOTP(db.getfield(message.chat.id,"totp",'signup'))
    if(totp.verify(message.text)):
        bot.send_message(message.chat.id,"Signup Successful")
        #Fav List (add username)
        name=db.getfield(message.chat.id,'username','signup')
        db.insertdata(name,'username','fav')
        bot.send_message(message.chat.id, "To Login Press /Login")
    else:
        msg = bot.send_message(message.chat.id, "Invalid Otp \nEnter again: ")
        bot.register_next_step_handler(msg,checkotp)
#Login
@bot.message_handler(commands=['Login'])
def login(message):
    if(db.checkdata(message.chat.id,'chatid','login')):
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        else:
            bot.send_message(message.chat.id,'Already Logged in')
            return
    msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
    bot.register_next_step_handler(msg,user)
def user(message):
    if(db.checkdata(message.text,"username","signup")):
        db.insertdata(message.chat.id,"chatid","login")
        db.updatedata(message.chat.id,"username",message.text,"login")
        db.updatedata(message.chat.id,"status","no","login")
        msg = bot.send_message(message.chat.id, "Enter Your Password: ")
        bot.register_next_step_handler(msg,passw)
    else:
        msg = bot.send_message(message.chat.id, "Invalid UserName and Password \nEnter Your UserName again: ")
        bot.register_next_step_handler(msg,user)
def passw(message):
    if(db.checkdata(message.text,"pass",'signup')):
        db.updatedata(message.chat.id,"status","yes","login")
        bot.send_message(message.chat.id,"Login Successful")
    else:
        msg=bot.send_message(message.chat.id,"Incorrect Username and Password \nEnter again: ")
        db.deleterow("chatid",message.chat.id,"login")
        bot.register_next_step_handler(msg,user)
### Binance API
@bot.message_handler(commands=['Coins'])
def CoinDetails(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        msg=bot.send_message(message.chat.id,"Enter The Coin Symbol: ")
        bot.register_next_step_handler(msg,PrintPair)
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        bot.send_message(message.chat.id,'Not logged-in')
        msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
        bot.register_next_step_handler(msg,user)
def PrintPair(message):
    flag=0
    prices = client.get_all_tickers()
    pairlist=''
    for i in prices:
        if(re.search(f"^{message.text.upper()}",i['symbol'])): #regex
            pairlist+=f"\n-> <code>{i['symbol']}</code>"
            flag=1
    if(flag==1):
        bot.send_message(message.chat.id,f'Available Pairs are ..... {pairlist}')
        bot.send_message(message.chat.id,"\nGet Price - /Price \nRecent Trade - /Recent_Trade \nBid & Ask - /Bid_Ask")
    else:
        bot.send_message(message.chat.id,'No Such Coin Available')
        msg=bot.send_message(message.chat.id,"Enter The Symbol Again : ")
        bot.register_next_step_handler(msg,PrintPair)
@bot.message_handler(commands=['Price'])
def Get_Price(message):    
    msg=bot.send_message(message.chat.id,"Enter the Pair(Ex- BTCUSDT): ")
    bot.register_next_step_handler(msg,PrintPrice)                                                                                                                
def PrintPrice(message):
    try:
        info = client.get_symbol_ticker(symbol=message.text.upper())
        bot.send_message(message.chat.id,f"Price {message.text.upper()} is {info['price']}")
    except:
        bot.send_message(message.chat.id,"Invalid Pair")
        msg=bot.send_message(message.chat.id,"Enter the Pair Again(Ex- BTCUSDT): ")
        bot.register_next_step_handler(msg,PrintPrice)
@bot.message_handler(commands=['Recent_Trade'])
def Get_RTrade(message): 
    msg=bot.send_message(message.chat.id,"Enter the Pair(Ex- BTCUSDT): ")
    bot.register_next_step_handler(msg,RTrade)
def RTrade(message):
    try:
        trades = client.get_recent_trades(symbol=message.text.upper())
        bot.send_message(message.chat.id,"Recent Trades are ")
        flag2=1
        for i in trades:
             if(flag2<=5): 
                bot.send_message(message.chat.id,f"{flag2}) ID -> {i['id']} \n Price -> {i['price']}\n Quantity -> {i['qty']} ")
                flag2+=1
    except:
        bot.send_message(message.chat.id,"Invalid Pair")
        msg=bot.send_message(message.chat.id,"Enter the Pair Again(Ex- BTCUSDT): ")
        bot.register_next_step_handler(msg,RTrade)
@bot.message_handler(commands=['Bid_Ask'])
def get_BidAsk(message):
    msg=bot.send_message(message.chat.id,"Enter the Pair(Ex- BTCUSDT): ")
    bot.register_next_step_handler(msg,BidAsk)
def BidAsk(message):
    try:
        depth = client.get_order_book(symbol=message.text.upper())
        bot.send_message(message.chat.id,"Top 5 Bid and Ask :")
        flag3=1
        str1='BIDs'
        str2='ASKs'
        for i in depth['bids']:
             if(flag3<=5):
                str1+=f"\n{flag3}) Price- {i[0]}\t Qty- {i[1]}"
                flag3+=1
        bot.send_message(message.chat.id,str1)
        flag3=1 
        for i in depth['asks']:
             if(flag3<=5):
                str2+=f"\n{flag3}) Price- {i[0]}\t Qty- {i[1]}"
                flag3+=1
        bot.send_message(message.chat.id,str2)
    except:
        bot.send_message(message.chat.id,"Invalid Pair")
        msg=bot.send_message(message.chat.id,"Enter the Pair Again(Ex- BTCUSDT): ")
        bot.register_next_step_handler(msg,BidAsk)
#Coinmarketcap api
@bot.message_handler(commands=['Sites'])
def Off_Site(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        msg=bot.send_message(message.chat.id,"Enter The Coin Symbol: ")
        bot.register_next_step_handler(msg,CoinSites)
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        bot.send_message(message.chat.id,'Not logged-in')
        msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
        bot.register_next_step_handler(msg,user)
def CoinSites(message):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info'
    parameters = {
    'symbol':message.text.upper()
    }
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY':confi.CoinMarketCap,
    }
    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        for i in data['data'][message.text.upper()]['urls']['website']:
            bot.send_message(message.chat.id,f"Official Site : {i}")
        for i in data['data'][message.text.upper()]['urls']['reddit']:
            bot.send_message(message.chat.id,f"Reddit : {i}")
        for i in data['data'][message.text.upper()]['urls']['technical_doc']:
            bot.send_message(message.chat.id,f"Technical Documentation : {i}")
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
#Search API
@bot.message_handler(commands=['G_Search'])
def Gsearch(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        msg=bot.send_message(message.chat.id,"Enter the Coin to be Searched: ")
        bot.register_next_step_handler(msg,CryptoSearch)
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        bot.send_message(message.chat.id,'Not logged-in')
        msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
        bot.register_next_step_handler(msg,user)
def CryptoSearch(message):
    if(not db.checkdata(message.chat.id,'chatid','ShowMore')):
      db.insertdata(message.chat.id,'chatid','ShowMore')
    db.updatedata(message.chat.id,'coinname',message.text,'ShowMore')
    url = f'https://customsearch.googleapis.com/customsearch/v1?cx=3233e5aefb1f10742&q={message.text}&key={confi.GsearchApi}'
    res = requests.get(url)
    text = res.text
    data = json.loads(text)
    count=1
    if(data["searchInformation"]["totalResults"]=='0'):
        bot.send_message(message.chat.id,"No Such Coin Exists")
        return
    for i in data['items']:
        if(count<=5):
            bot.send_message(message.chat.id,i['link'])
            count+=1
        else:
            break
    msg = bot.send_message(message.chat.id, "Show More Results (y/n): ")
    bot.register_next_step_handler(msg,Get_More)
def Get_More(message):
    if(message.text=='y' or message.text=='Y'):   
        text=db.getfield(message.chat.id,'coinname','ShowMore')
        url = f'https://customsearch.googleapis.com/customsearch/v1?cx=3233e5aefb1f10742&q={text}&start=6&key={confi.GsearchApi}'
        res = requests.get(url)
        text = res.text
        data = json.loads(text)
        count=1
        if(data["searchInformation"]["totalResults"]=='0'):
            bot.send_message(message.chat.id,"No Such Coin Exists")
            return
        for i in data['items']:
            if(count<=5):
                bot.send_message(message.chat.id,i['link'])
                count+=1
            else:
                break
@bot.message_handler(commands=['Fav_Coin'])
def Edit_Fav(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        msg=bot.send_message(message.chat.id,"1) Add to List\n2) Remove from List")
        bot.register_next_step_handler(msg,Edit_Fav_Choice)
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        bot.send_message(message.chat.id,'Not logged-in')
        msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
        bot.register_next_step_handler(msg,user)
def Edit_Fav_Choice(message):
    if(message.text=='1'):
        msg=bot.send_message(message.chat.id,"Enter The Coin Symbol: ")
        bot.register_next_step_handler(msg,PrintFavPair)
    elif(message.text=='2'):
        user_name=db.getfield(message.chat.id,'username','login')
        if(db.checkdata(user_name,'username','fav')):
          coin_list=db.getfav(user_name)
          coin_list=coin_list.split(",")
          print_list="\n".join(coin_list)  
          msg=bot.send_message(message.chat.id,f"Your Favourite List:\n{print_list}\nEnter the Pair to Remove:")
          bot.register_next_step_handler(msg,removefavpair)
    else:
        pass #invlid choice
def PrintFavPair(message):
    flag=0
    prices = client.get_all_tickers()
    pairlist=''
    for i in prices:
        if(re.search(f"^{message.text.upper()}",i['symbol'])): #regex
            pairlist+=f"\n-> <code>{i['symbol']}</code>"
            flag=1
    if(flag==1):
        msg=bot.send_message(message.chat.id,f'Available Pairs are ..... {pairlist}\n Enter pairs like "BTCUSDT BTCBUSD": ')
        bot.register_next_step_handler(msg,AddFavList)
    else:
        bot.send_message(message.chat.id,'No Such Coin Available')
        msg=bot.send_message(message.chat.id,"Enter The Symbol Again : ")
        bot.register_next_step_handler(msg,PrintPair)
def AddFavList(message):
    try:
        info = client.get_symbol_ticker(symbol=message.text.upper())
        bot.send_message(message.chat.id,f"Price {message.text.upper()} is {info['price']}")
        user_name=db.getfield(message.chat.id,'username','login')
        if(db.checkdata(user_name,'username','fav')):
            coin_list=db.getfav(user_name)
            coin_list=coin_list.split(",")
            if(message.text in coin_list):
                bot.send_message(message.chat.id,"Pair Already Exist")
                msg=bot.send_message(message.chat.id,"Enter the Pair Again(Ex- BTCUSDT): ")
                bot.register_next_step_handler(msg,PrintFavPair)
            else:
                coin_list.append(message.text)
                new_list=",".join(coin_list)
                db.updatefav(new_list,user_name)
                bot.send_message(message.chat.id,"Successfully Added to your favourite list")
        else:
            db.insertdata(user_name,'username','fav')
            coin=message.text
            db.updatefav(coin,user_name)
            bot.send_message(message.chat.id,"Successfully Added to your favorite list")
    except: 
        bot.send_message(message.chat.id,"Invalid Pair")
        msg=bot.send_message(message.chat.id,"Enter the Pair Again(Ex- BTCUSDT): ")
        bot.register_next_step_handler(msg,PrintFavPair)
def removefavpair(message):
    try:
        user_name=db.getfield(message.chat.id,'username','login')
        coin_list=db.getfav(user_name)
        coin_list=coin_list.split(",")
        coin_list.remove(message.text)
        if(len(coin_list)==0):
            db.deleterow("username",user_name,"fav")
        else:
            new_list=",".join(coin_list)
            db.updatefav(new_list,user_name)
        bot.send_message(message.chat.id,"Successfully Removed from your favorite list")
    except: 
        bot.send_message(message.chat.id,"Invalid Pair")
        msg=bot.send_message(message.chat.id,"Enter the Pair Again(Ex- BTCUSDT): ")
        bot.register_next_step_handler(msg,removefavpair)
bot.polling()
# url = f'https://customsearch.googleapis.com/customsearch/v1?cx=3233e5aefb1f10742&q=bitcoin&key={confi.GsearchApi}'
# res = requests.get(url)
# text = res.text
# data = json.loads(text)
# for i in data['items']:
    