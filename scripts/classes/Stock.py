# -*- coding: utf-8 -*-

# ---------- MODULES ----------
# standard modules
import sys, os
import numpy as np
from datetime import datetime
from pandas import DataFrame
import pandas as pd

# 3rd party modules
import yfinance as yf

# custom modules
currentFolder = os.path.dirname(os.path.abspath(__file__))
main_path = currentFolder.replace('classes','')
if main_path not in sys.path:
    sys.path.append(main_path)

from utils.yfinance_extension import load_EPS, load_CashFlow, load_KeyStatistics
from utils.generic import mergeDataFrame, npDateTime64_2_str
from classes.FinnhubAPI import FinnhubClient

# ---------- VARIABLES ----------

# Einstellungen, damit Pandas DataFrames immer vollstaendig geplotted werden
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# DEV-VARIABLES
DEBUG = False

# default symbol for the stock exchange trading place
# - de: XETRA
defaultTradingPlace = 'DE'

# currencies
EURO = u"Euro"
DOLLAR = u"Dollar"


# ---------- CLASSES ----------
class Stock:

    """
        TODO: growth rate anhand einer regressionsgerade beim EPS berechnen (falls plausibel?)
        TODO: growth rate anhand einer regressionsgerade beim Cashflow berechnen (falls plausibel?)
        TODO: plotten der strongBuy, buy, hold, sell und strongSell empfehlungen (auch aus mehreren Quellen, z.B. yahoo finance, Finnhub, ...)
    """

    # constant variables for deciding, how much data should be loaded
    LOAD_BASIC_DATA = 1
    LOAD_ALL_DATA = 2

    # variables
    PE_RATIO = 'P/E'
    BOOK_VALUE_PER_SHARE = 'bookValuePerShare'
    EARNINGS_PER_SHARE = 'EPS'
    MARKET_PRICE = 'marketPrice'
    DIVIDEND = 'dividend'
    DIVIDEND_YIELD = 'dividendYield'


    def __init__(self,symbol='',growthRateAnnualyPrc=0,switchLoadData=LOAD_ALL_DATA,tradingPlace=''):

        self.growthRateAnnualy = growthRateAnnualyPrc/100

        # init variables for data, which will be loaded from yahoo finance
        self.info = None
        self.name = None
        self.ticker = None
        self.currency = None
        self.currencySymbol = ''

        # dict and DataFrame to store all information
        self.basicData = {}
        self.keyStatistics = {}
        self.financialData = DataFrame()


        self.historicalData = None
        self.historicalDataRelative = None

        # storing recommendations for buying, holding and selling
        self.recommendations = None


        # Exchange traing place
        if ('.' in symbol) or (tradingPlace is ''):
            self.symbol = symbol
        else:
            self.symbol = symbol + '.' + defaultTradingPlace

        # Load data
        if switchLoadData == self.LOAD_ALL_DATA:
            self.loadMainData()
        elif switchLoadData == self.LOAD_BASIC_DATA:
            self.loadBasicData()


    def loadMainData(self):
        self.getStockName()
        self.getBookValuePerShare()
        self.getCurrency()
        self.getCurrentStockValue()
        self.getEarningsPerShare()
        self.getEpsHistory()
        self.getDividend()
        self.getPriceEarnigsRatio()
        self.getBalanceSheet()
        self.getFinancials()
        self.getRecommendations()
        self.getCashflow()
        self.getKeyStatistics()

        # monthly historical data
        self.historicalData = self.ticker.history(period="5y", interval = "1wk")


    def loadBasicData(self):
        self.getStockName()


    def calcRelativeHistoricalData(self):
        # take all absolute values and override them afterwards
        self.historicalDataRelative = self.historicalData.loc[:,'Close'].copy()

        firstDate = npDateTime64_2_str(self.historicalDataRelative.index.values[0])
        firstValue = self.historicalDataRelative.loc[firstDate]
        for row in self.historicalDataRelative.index.values:
            date = npDateTime64_2_str(row)
            self.historicalDataRelative.loc[date] = self.historicalDataRelative.loc[date]/firstValue*100           


    def getTicker(self):
        if DEBUG:
            print('Creating ticker...')

        if self.symbol is not None:
            self.ticker = yf.Ticker(self.symbol)
        else:
            raise ValueError('Stock symbol missing.')

        if DEBUG:
            print('Created ticker successfully')


    def getInfo(self):
        if DEBUG:
            print('Loading information...')

        if self.info is not None:
            return self.info
        elif self.ticker is None:
            self.getTicker()
        
        self.info = self.ticker.info

        if DEBUG:
            print(self.info)
            print('Information loaded successfully')


    def getEpsHistory(self):
        df = load_EPS(self.symbol)
        
        # add the data to the financialData data frame
        self.financialData = mergeDataFrame(self.financialData,df)
        return df


    def getStockName(self):
        if self.name is not None:
            return self.name
        else:
            if self.info is None:
                self.getInfo()
        
            if 'longName' in self.info.keys():
                self.name = self.info['longName']
            else:
                raise KeyError('Missing key "longName" in stock information')

            return self.name

    
    def getBookValuePerShare(self):
        if self.info is None:
            self.getInfo()

        if 'bookValue' in self.info.keys():
            self.basicData[self.BOOK_VALUE_PER_SHARE] = self.info['bookValue']
        else:
            raise KeyError('Missing Key "bookValue"')

        return self.basicData[self.BOOK_VALUE_PER_SHARE]

    
    def getCurrency(self):
        if self.info is None:
            self.getInfo()

        if 'currency' in self.info.keys():
            self.currency = self.info['currency']
        else:
            raise KeyError('Missing key "currency" in stock information')

        if self.currency == 'EUR':
            self.currencySymbol = EURO
        else:
            self.currencySymbol = DOLLAR

    
    def getCurrentStockValue(self):
        if self.info is None:
            self.getInfo()

        key = 'regularMarketPrice'
        if key in self.info.keys():
            self.basicData[self.MARKET_PRICE] = self.info[key]
        else:
            raise KeyError('Missing key "%s"' %(key))

        return self.basicData[self.MARKET_PRICE]

    
    def getEarningsPerShare(self):
        if self.info is None:
            self.getInfo()

        if ('trailingEps' in self.info.keys()):
            self.basicData[self.EARNINGS_PER_SHARE] = self.info['trailingEps']

        # use the forward value if it is not None
        if ('forwardEps' in self.info.keys()) and (self.info['forwardEps'] is not None):
            self.basicData[self.EARNINGS_PER_SHARE] = self.info['forwardEps']
            
        if self.EARNINGS_PER_SHARE not in self.basicData.keys():
            raise KeyError('Missing key "trailingEps" or "forwardEps" in stock information')

        return self.basicData[self.EARNINGS_PER_SHARE]


    def getPriceEarnigsRatio(self):
        if self.info is None:
            self.getInfo()

        if 'trailingPE' in self.info.keys():
            self.basicData[self.PE_RATIO] = self.info['trailingPE']

        # use the forward value, if it is not None
        if ('forwardPE' in self.info.keys()) and (self.info['forwardPE'] is not None):
            self.basicData[self.PE_RATIO] = self.info['forwardPE']

        if self.PE_RATIO not in self.basicData.keys():
            raise KeyError('Missing key "trailingPE" or "forwardPE" in stock information')

        return self.basicData[self.PE_RATIO]


    def getDividend(self):
        if self.info is None:
            self.getInfo()

        dividend = 0
        if ('dividendRate' in self.info.keys()):
            if (self.info['dividendRate'] is None):
                dividend = 0
            else:
                dividend = self.info['dividendRate'] 
        else:
            raise KeyError('Missing key "dividendRate" in stock information')

        # store dividend in basic stock data dict
        self.basicData[self.DIVIDEND] = dividend
        
        # calculate the dividend yield for the current market price in Percent
        if not self.isItemInBasicData(self.MARKET_PRICE):
            self.getCurrentStockValue()

        self.basicData[self.DIVIDEND_YIELD] = dividend/self.getBasicDataItem(self.MARKET_PRICE)*100

        return self.basicData[self.DIVIDEND]


    def getBalanceSheet(self):
        if self.ticker is None:
            self.getTicker()

        balanceSheet = self.ticker.balance_sheet
        self.financialData = mergeDataFrame(self.financialData,balanceSheet)
        return balanceSheet


    def getFinancials(self):
        if self.ticker is None:
            self.getTicker()

        financials = self.ticker.financials
        
        self.financialData = mergeDataFrame(self.financialData,financials)
        
        return financials


    def getCashflow(self):
        if self.ticker is None:
            self.getTicker()

        cashflow = self.ticker.cashflow
        self.financialData = mergeDataFrame(self.financialData,cashflow)

        # extension
        df = load_CashFlow(self.symbol)
        # add the data to the financialData data frame
        self.financialData = mergeDataFrame(self.financialData,df)
        return cashflow
    
    def getKeyStatistics(self):
        if self.ticker is None:
            self.getTicker()
            
        # extension
        self.keyStatistics = load_KeyStatistics(self.symbol)
        return self.keyStatistics


    def getBasicDataItem(self,keyName):
        return self.basicData[keyName]


    def isItemInBasicData(self,keyName):
        return keyName in self.basicData.keys()


    def getRecommendations(self):
        recommendations = FinnhubClient(self.symbol).getRecommendationsDataFrame()
        self.recommendations = recommendations
        return recommendations



    # Funktion zur Berechnung eines Gewichteten Mittelwerts
    def calcMeanWeightedValue(self,value):
        if isinstance(value,list) or isinstance(value,tuple):
            # Faktoren für die einzelnen Jahre
            # Die letzten Werte der Liste werden dabei mit den höchsten Faktoren bewertet
            # Faktoren in 1er-Schritten von 1 aufsteigend
            interval = 0.5
            factors = list(np.arange(1,len(value)*interval+1,interval))

            # Alle Werte mit den Faktoren gewichten
            weightedValues = [v*f for v,f in zip(value,factors)]
            
            # Gewichteter Mittelwert
            weightedMeanValue = sum(weightedValues)/sum(factors)
            return weightedMeanValue
        else:
            return value


    # Funktion zur Formattierung der Ausgabe
    def __str__(self):
        return '<Stock Object \'{stockName}\'>'.format(stockName=self.name)
