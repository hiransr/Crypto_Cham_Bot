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
yt_channels=['BitBoy Crypto','Coin Bureau','Alt Coins Daily','Data Dash','Sheldon Evans','Ivan on Tech','Benjamin Cowen','Andreas Antonopoulos','Anthony Pompliano','EllioTrades Crypto','Digital Asset News','Altcoin Buzz','Box Mining','Crypto Lark','Crypto Zombie','The Modern Investor','TheChartGuys','Hashoshi']
yt_channel_link=['UCjemQfjaXAzA-95RKoy9n_g','UCqK_GSMbpiV8spgD3ZGloSw','UCjemQfjaXAzA-95RKoy9n_g','UCbLhGKVY-bJPcawebgtNfbw','UCCatR7nWbYrkVXdxXb4cGXw/featured','UCZ3fejCy_P5xhv9QF-V6-YA','UCrYmtJBtLdtm2ov84ulV-yg','UCRvqjQPSeaWn-uEx-w0XOIg','UCJWCJCWOxBYSi5DhCieLOLQ','UCevXpeL8cNyAnww-NqJ4m2w','UCMtJYS0PrtiUwlk6zjGDEMA','UCJgHxpqfhWEEjYH9cLXqhIQ','UCGyqEtcGQQtXyUwvcy7Gmyg','UCxODjeUwZHk3p-7TU-IsDOA','UCl2oCaw8hdR_kbqyqd2klIA','UCiUnrCUGCJTCC7KjuW493Ww','UC-5HLi3buMzdxjdTdic3Aig','UCnqZ2hx679DqRi6khRUNw2g','UCQNHKsYDGlWefzv9MAaOJGA']
bot = telebot.TeleBot(confi.telegramapi, parse_mode="HTML") # You can set parse_mode by default. HTML or MARKDOWN
############################### MAIN MENU #################################
@bot.message_handler(commands=['mainmenu'])
def mm(message):
    bot.send_message(message.chat.id,"******** MAIN MENU ********\n1)/signup\n2)/login\n3)/coins\n4)/official_sites\n5)/g_search\n6)/fav_coin\n7)/youtube\n8)/help\n9)/logout ")
#Sign-up and Password
@bot.message_handler(commands=['signup'])
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
@bot.message_handler(commands=['login'])
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
@bot.message_handler(commands=['coins'])
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
        bot.send_message(message.chat.id,"\nGet Price - /price \nRecent Trade - /recent_trade \nBid & Ask - /bid_ask")
    else:
        bot.send_message(message.chat.id,'No Such Coin Available')
        msg=bot.send_message(message.chat.id,"Enter The Symbol Again : ")
        bot.register_next_step_handler(msg,PrintPair)
@bot.message_handler(commands=['price'])
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
@bot.message_handler(commands=['recent_trade'])
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
@bot.message_handler(commands=['bid_ask'])
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
######################## Coinmarketcap api ################################
@bot.message_handler(commands=['official_sites'])
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
############################## Google Search API #######################################
@bot.message_handler(commands=['g_search'])
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
################################ FAV ####################################

@bot.message_handler(commands=['fav_coin'])
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
        msg=bot.send_message(message.chat.id,"Invalid Choice!!\nEnter again: ")
        bot.register_next_step_handler(msg,Edit_Fav_Choice)
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
@bot.message_handler(commands=['see_my_fav_list'])
def Show_Fav_Coin(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        bot.send_message(message.chat.id,"Your List:")
        user_name=db.getfield(message.chat.id,'username','login')
        if(db.checkdata(user_name,'username','fav')):
            coin_list=db.getfav(user_name)
            coin_list=coin_list.split(",")
            for coin in coin_list:
                info = client.get_symbol_ticker(symbol=coin.upper())
                bot.send_message(message.chat.id,f"Coin Name: {coin.upper()}      Price: {info['price']}\n")
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        bot.send_message(message.chat.id,'Not logged-in')
        msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
        bot.register_next_step_handler(msg,user)
############################ YOUTUBE #######################################
@bot.message_handler(commands=['youtube'])
def yt_menu(message):
    bot.send_message(message.chat.id,f"1)/channel_list\n2)/yt_search")
@bot.message_handler(commands=['channel_list'])
def Channel_List(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        bot.send_message(message.chat.id,"Top 20 channels:\n ")
        for i in range(0,len(yt_channels)):
            bot.send_message(message.chat.id,f"{yt_channels[i]} - https://www.youtube.com/channel/{yt_channel_link[i]}")
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        bot.send_message(message.chat.id,'Not logged-in')
        msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
        bot.register_next_step_handler(msg,user)
@bot.message_handler(commands=['yt_search'])
def YT_Search(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        msg=bot.send_message(message.chat.id,"Enter a keyword to Search: ")
        bot.register_next_step_handler(msg,ytsearch)
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
        bot.send_message(message.chat.id,'Not logged-in')
        msg = bot.send_message(message.chat.id, "Enter Your UserName:  ")
        bot.register_next_step_handler(msg,user)   
def ytsearch(message):
    url = f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=40&q={message.text}&key={confi.youtubeapi}' #channel result count
    res = requests.get(url)
    text = res.text
    data = json.loads(text)
    for result in data['items']:
        if(result["snippet"]['channelTitle'] in yt_channels):
            bot.send_message(message.chat.id,f"https://www.youtube.com/watch?v={result['id']['videoId']}")
@bot.message_handler(commands=['Help'])
def help(message):
    bot.send_message(message.chat.id,"Hlo all I am here to make users friendly crypto service..................")
@bot.message_handler(commands=['logout'])
def logout(message):
    if(db.getfield(message.chat.id,'status','login')=='yes'):
        db.deleterow('chatid',message.chat.id,'login')
        bot.send_message(message.chat.id,"Successfully Logged out!!")
    else:
        if(db.getfield(message.chat.id,'status','login')=='no'):
            db.deleterow("chatid",message.chat.id,"login")
bot.polling()
# url = f'https://customsearch.googleapis.com/customsearch/v1?cx=3233e5aefb1f10742&q=bitcoin&key={confi.GsearchApi}'
# res = requests.get(url)
# text = res.text
# data = json.loads(text)
# for i in data['items']:
    