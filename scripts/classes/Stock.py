# -*- coding: utf-8 -*-

# ---------- MODULES ----------
# standard modules
import sys, os
import numpy as np
from datetime import datetime
from pandas import DataFrame

# 3rd party modules
import yfinance as yf

# custom modules
currentFolder = os.path.dirname(os.path.abspath(__file__))
main_path = currentFolder.replace('classes','')
if main_path not in sys.path:
    sys.path.append(main_path)

from utils.yfinance_extension import load_EPS
from utils.generic import mergeDataFrame

# ---------- VARIABLES ----------

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

    # constant variables for deciding, how much data should be loaded
    LOAD_BASIC_DATA = 1
    LOAD_ALL_DATA = 2

    def __init__(self,growthRateAnnualyPrc,symbol='',switchLoadData=LOAD_ALL_DATA,tradingPlace=''):

        self.growthRateAnnualy = growthRateAnnualyPrc/100

        # init variables for data, which will be loaded from yahoo finance
        self.info = None
        self.name = None
        self.ticker = None
        self.currency = None
        self.currencySymbol = ''
        self.currentStockValue = None
        self.bookValuePerShare = None
        self.dividend = None
        self.netIncome = None
        self.priceEarningsRatio = None
        self.earningsPerShare = None

        self.financialData = DataFrame()

        self.historicalData = None

        #
        self.mainDataLoaded = False

        # Exchange traing place
        if ('.' in symbol) and (tradingPlace is ''):
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

        # monthly historical data
        self.historicalData = self.ticker.history(period="5y", interval = "1mo")

        # change the flag to indicate that all data has been loaded
        self.mainDataLoaded = True

    def loadBasicData(self):
        self.getStockName()


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
        self.bookValuePerShare = self.info['bookValue']

    
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
        if self.ticker is None:
            self.getTicker()

        lastDayData = self.ticker.history(period='1d')
        closeValue = lastDayData.iloc[0]['Close']
        self.currentStockValue = closeValue

    
    def getEarningsPerShare(self):
        if self.info is None:
            self.getInfo()

        if ('forwardEps' in self.info.keys()) and (self.info['forwardEps'] is not None):
            self.earningsPerShare = self.info['forwardEps']
        elif 'trailingEps' in self.info.keys():
            self.earningsPerShare = self.info['trailingEps']
        else:
            raise KeyError('Missing key "trailingEps" or "forwardEps" in stock information')


    def getPriceEarnigsRatio(self):
        if self.info is None:
            self.getInfo()

        if ('forwardPE' in self.info.keys()) and (self.info['forwardPE'] is not None):
            self.priceEarningsRatio = self.info['forwardPE']
        elif 'trailingPE' in self.info.keys():
            self.priceEarningsRatio = self.info['trailingPE']
        else:
            raise KeyError('Missing key "trailingPE" or "forwardPE" in stock information')


    def getDividend(self):
        if self.info is None:
            self.getInfo()

        if 'dividendRate' in self.info.keys():
            self.dividend = self.info['dividendRate']
        else:
            raise KeyError('Missing key "dividendRate" in stock information')


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

        return cashflow



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
