# Raw Package
import numpy as np
from numpy.core.numeric import NaN
from numpy.lib.type_check import nan_to_num
import pandas as pd
import time
from bs4 import BeautifulSoup as bs

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


    
    


a = VWAPCalculator()
#a.getAllTickers()
#a.getTestValues()
a.getSP500VWAP()