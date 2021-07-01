# Raw Package
import numpy as np
from numpy.core.numeric import NaN
from numpy.lib.type_check import nan_to_num
import pandas as pd
import time
from bs4 import BeautifulSoup as bs
import numpy as np
#Data Source
import yfinance as yf
import requests

#Data viz
import plotly.graph_objs as go


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
        data = yf.download(tickers=tickers, period='1h', interval='1m')
        i = 0 
        while i < len(data.tail(1)['Close'].columns):
            price_tail_value = 1
            volume_tail_value = 1
            while self.isValue(data.tail(price_tail_value)['Close'].values[0][i]) == False:
                price_tail_value += 1
            while self.isValue(data.tail(volume_tail_value)['Volume'].values[0][i]) == False:
                volume_tail_value += 1
            output.append({"Ticker": data.tail(1)['Close'].columns[i], "Price": data.tail(price_tail_value)['Close'].values[0][i], "Volume": data.tail(volume_tail_value)['Volume'].values[0][i]})
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
        data = yf.download(tickers=tickers, period='100m', interval='1m')
        i = 0
        while i < len(data.tail(1)['Close'].columns):
            price_tail_value = 1
            volume_tail_value = 1
            output.append({"Ticker": data.tail(1)['Close'].columns[i], "Price": data.tail(price_tail_value)['Close'].values[0][i], "Volume": data.tail(volume_tail_value)['Volume'].values[0][i]})
            i = i + 1
        df = pd.DataFrame(output)
        df = df.assign(
            vwap=df.eval(
                'wgtd = Price * Volume', inplace=False
            ).cumsum().eval('wgtd / Volume')
        )
        return(df)
    
    


a = VWAPCalculator()
#a.getAllTickers()
#a.getTestValues()
a.getSP500VWAP()