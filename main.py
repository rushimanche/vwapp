# Raw Package
import numpy as np
from numpy.core.numeric import NaN
from numpy.lib.type_check import nan_to_num
import pandas as pd
import time
from bs4 import BeautifulSoup as bs
import numpy as np
from requests.models import default_hooks
#Data Source
import yfinance as yf
import requests
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from twilio.rest import Client 

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_MESSAGING_SERVICE_SID = os.environ.get("TWILIO_MESSAGING_SERVICE_SID")

class VWAPCalculator:

    def __init__(self):
        pass

    def listToString(self, s): 
        str1 = " " 
        
        return (str1.join(s))

    def isValue(self, value):
        if not pd.isna(value) and value != 0.0:
            return True
        else:
            return False

    def getAllTickers(self):
        headers = {
            'authority': 'api.nasdaq.com',
            'accept': 'application/json, text/plain, */*',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
            'origin': 'https://www.nasdaq.com',
            'sec-fetch-site': 'same-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.nasdaq.com/',
            'accept-language': 'en-US,en;q=0.9',
        }

        params = (
            ('tableonly', 'true'),
            ('limit', '25'),
            ('offset', '0'),
            ('download', 'true'),
        )

        r = requests.get('https://api.nasdaq.com/api/screener/stocks', headers=headers, params=params)
        data = r.json()['data']
        df = pd.DataFrame(data['rows'], columns=data['headers'])
        return(self.listToString(df['symbol'].values))

    def getDJIATickers(self):
        url = 'https://www.dogsofthedow.com/dow-jones-industrial-average-companies.htm'
        request = requests.get(url,headers={'User-Agent': 'Mozilla/5.0'})
        soup = bs(request.text, "lxml")
        stats = soup.find('table',class_='tablepress tablepress-id-42 tablepress-responsive')
        pulled_df =pd.read_html(str(stats))[0]

        return(self.listToString(pulled_df['Symbol'].values))

    def getSP500Tickers(self):
        url = 'https://www.slickcharts.com/sp500'
        request = requests.get(url,headers={'User-Agent': 'Mozilla/5.0'})
        soup = bs(request.text, "lxml")
        stats = soup.find('table',class_='table table-hover table-borderless table-sm')
        df =pd.read_html(str(stats))[0]
        df['% Chg'] = df['% Chg'].str.strip('()-%')
        df['% Chg'] = pd.to_numeric(df['% Chg'])
        df['Chg'] = pd.to_numeric(df['Chg'])

        return(self.listToString(df['Symbol'].values))


    def getAllStockPricesAndVolumes(self):
        output = []
        tickers = self.getAllTickers()
        data = yf.download(tickers=tickers, period='1d', interval='1m')
        i = 0
        while i < len(data.tail(1)['Close'].columns):
            tail_value = 1
            while self.isValue(data.tail(tail_value)['Close'].values[0][i], data.tail(tail_value)['Volume'].values[0][i]) == False:
                tail_value += 1
            output.append({"Ticker": data.tail(tail_value)['Close'].columns[i], "Price": data.tail(tail_value)['Close'].values[0][i], "Volume": data.tail(tail_value)['Volume'].values[0][i]})
            i += 1
        return(output)

    def getDJIAVWAP(self):
        output = []
        tickers = self.getDJIATickers()
        data = yf.download(tickers=tickers, period='1w', interval='1d')
        prices = data["Close"].apply(lambda col: col[col.notna()].iat[-1] if col.notna().any() else np.nan )
        volumes = data["Volume"].apply(lambda col: col[col.notna()].iat[-1] if col.notna().any() else np.nan )
        i = 0 
        while i < len(data.tail(1)['Close'].columns):
            output.append({"Ticker": data.tail(1)['Close'].columns[i], "Price": prices[data.tail(1)['Close'].columns[i]], "Volume": volumes[data.tail(1)['Volume'].columns[i]]})
            i = i + 1
        df = pd.DataFrame(output)
        df = df.assign(
            vwap=df.eval(
                'wgtd = Price * Volume', inplace=False
            ).cumsum().eval('wgtd / Volume')
        )
        return(df)

    def getSP500VWAP(self):
        output = []
        tickers = self.getSP500Tickers()
        data = yf.download(tickers=tickers, period='10m', interval='1m')
        prices = data["Close"].apply(lambda col: col[col.notna()].iat[-1] if col.notna().any() else np.nan )
        volumes = data["Volume"].apply(lambda col: col[col.notna()].iat[-1] if col.notna().any() else np.nan )
        i = 0 
        while i < len(data.tail(1)['Close'].columns):
            output.append({"Ticker": data.tail(1)['Close'].columns[i], "Price": prices[data.tail(1)['Close'].columns[i]], "Volume": volumes[data.tail(1)['Volume'].columns[i]]})
            i = i + 1
        df = pd.DataFrame(output)
        df = df.assign(
            vwap=df.eval(
                'wgtd = Price * Volume', inplace=False
            ).cumsum().eval('wgtd / Volume')
        )
        return(df)

    def getSingleVWAP(self, ticker):
        output = []
        data = yf.download(tickers=ticker, period='10m', interval='1m')
        df = data.assign(
            vwap=data.eval(
                'wgtd = Close * Volume', inplace=False
            ).cumsum().eval('wgtd / Volume')
        )
        return(df)
    
    def getHighestVWAPPositiveDifferential(self, df):
        differential = df['vwap'] / df['Price'] - 1
        ticker_data = df.loc[df['Ticker'] == df.loc[differential.idxmax(), 'Ticker']]
        return([ticker_data.iloc[0]['Ticker'], ticker_data.iloc[0]['Price']])

    def getLowestVWAPPositiveDifferential(self, df):
        differential = df['vwap'] / df['Price'] - 1
        ticker_data = df.loc[df['Ticker'] == df.loc[differential.idxmin(), 'Ticker']]
        return([ticker_data.iloc[0]['Ticker'], ticker_data.iloc[0]['Price']])

    def getLatestVWAPReading(self, df):
        counter = 1
        while (self.isValue(df['vwap'].tail(counter).values[0]) == False or self.isValue(df['Close'].tail(counter).values[0]) == False):
            counter += 1
        price = df['Close'].tail(counter).values[0]
        vwap = df['vwap'].tail(counter).values[0] 
        return(price / vwap)

    def textUserSingleUpdates(self, ticker, number):
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) 
        
        stock_status = self.getLatestVWAPReading(self.getSingleVWAP(ticker))

        if(stock_status < 1):
            body = 'BUY ' + ticker + '! ' + 'The current price is ' + str(stock_status * 100) + '% below the VWAP.'
        else:
            body = 'SELL ' + ticker + '! ' + 'The current price is ' + str(stock_status * 100) + '% above the VWAP.'

        message = client.messages.create(  
                                    messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID, 
                                    body=body,      
                                    to=number
                                )

    def textUserDJIAUpdates(self, number):
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) 
        
        djia_data = self.getDJIAVWAP()
        winner_stock = self.getHighestVWAPPositiveDifferential(djia_data)
        loser_stock = self.getLowestVWAPPositiveDifferential(djia_data)

        body = 'BUY ' + winner_stock[0] + ' AT $' + str(winner_stock[1]) + '. ' + 'SELL ' + loser_stock[0] + ' AT $' + str(loser_stock[1]) + '.'

        message = client.messages.create(  
                                    messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID, 
                                    body=body,      
                                    to=number
                                )

    def textUserSP500Updates(self, number):
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) 
        
        sp500_data = self.getSP500VWAP()
        winner_stock = self.getHighestVWAPPositiveDifferential(sp500_data)
        loser_stock = self.getLowestVWAPPositiveDifferential(sp500_data)

        body = 'BUY ' + winner_stock[0] + ' AT $' + str(winner_stock[1]) + '. ' + 'SELL ' + loser_stock[0] + ' AT $' + str(loser_stock[1]) + '.'

        message = client.messages.create(  
                                    messaging_service_sid=TWILIO_MESSAGING_SERVICE_SID, 
                                    body=body,      
                                    to=number
                                )
                                
    def scheduleNotifications(self, number, type, ticker=None):
        scheduler = BackgroundScheduler()

        if type == 'single':
            scheduler.add_job(self.textUserSingleUpdates, 'interval', [ticker, number], hours=3) #modify hours variable for scheduling
            scheduler.start()
        
        if type == 'djia':
            scheduler.add_job(self.textUserDJIAUpdates, 'interval', [number], hours=3) #modify hours variable for scheduling
            scheduler.start()

        if type == 'sp500':
            scheduler.add_job(self.textUserSP500Updates, 'interval', [number], hours=3) #modify hours variable for scheduling
            scheduler.start()

        print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

        try:
            # This is here to simulate application activity (which keeps the main thread alive).
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            # Not strictly necessary if daemonic mode is enabled but should be done if possible
            scheduler.shutdown()
        
a = VWAPCalculator()
#a.getDJIAVWAP()
a.scheduleNotifications('+15023410940', 'djia')