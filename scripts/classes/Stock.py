# -*- coding: utf-8 -*-

# ---------- MODULES ----------
# standard modules
import numpy as np
from datetime import datetime

# 3rd party modules
import yfinance as yf


# ---------- VARIABLES ----------

# default symbol for the stock exchange trading place
# - de: XETRA
exchangeTradingPlace = 'DE'

# currencies
EURO = u"\u20AC"
DOLLAR = u"\u0024"


# ---------- CLASSES ----------
class Stock:
    def __init__(self,earningsPerShare,WachstumsratePrc,priceEarningsRatio,name='unnamed',symbol='',boerse=''):

        # init variables
        self.info = None
        self.ticker = None
        self.currency = None
        self.currencySymbol = ''
        self.currentStockValue = None
        self.bookValuePerShare = None
        self.dividend = None
        self.netIncome = None

        #
        self.mainDataLoaded = False

        # Exchange traing place
        if boerse is '':
            self.boerse = exchangeTradingPlace
        else:
            self.boerse = boerse

        # initialize object
        self.symbol = symbol + '.' + exchangeTradingPlace

        # the following initialization is to be replaced in the future...
        self.meanEarningsPerShare = self.calcMeanWeightedValue(earningsPerShare)
        self.Wachstumsrate = 1+(WachstumsratePrc/100)
        self.meanPriceEarningsRatio = self.calcMeanWeightedValue(priceEarningsRatio)

        # Load data
        self.loadMainData()
        print(self.ticker.balance_sheet)
        print(self.ticker.financials)
        print(self.ticker.isin)


    def loadMainData(self):
        self.getStockName()
        self.getBookValuePerShare()
        self.getCurrency()
        self.getCurrentStockValue()
        self.getEarningsPerShare()
        self.getDividend()
        self.getNetIncome()

        # change the flag to indicate that all data has been loaded
        self.mainDataLoaded = True


    def getTicker(self):
        print('Creating ticker...')
        if self.symbol is not None:
            self.ticker = yf.Ticker(self.symbol)
        else:
            raise ValueError('Stock symbol missing.')

        print('Created ticker successfully')


    def getInfo(self):
        print('Loading information...')
        if self.info is not None:
            return self.info
        elif self.ticker is None:
            self.getTicker()
        
        self.info = self.ticker.info
        print('Information loaded successfully')


    def getStockName(self):
        if self.info is None:
            self.getInfo()
        
        if 'longName' in self.info.keys():
            self.name = self.info['longName']
        else:
            raise KeyError('Missing key "longName" in stock information')

    
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

        if 'trailingEps' in self.info.keys():
            self.earningsPerShare = self.info['trailingEps']
        elif 'forwardEps' in self.info.keys():
            self.earningsPerShare = self.info['forwardEps']
        else:
            raise KeyError('Missing key "trailingEps" or "forwardEps" in stock information')


    def getDividend(self):
        if self.info is None:
            self.getInfo()

        if 'dividendRate' in self.info.keys():
            self.dividend = self.info['dividendRate']
        else:
            raise KeyError('Missing key "dividendRate" in stock information')


    def getNetIncome(self):
        if self.ticker is None:
            self.getTicker()

        financials = self.ticker.financials
        netIncome = financials.loc['Net Income']
        lastNetIncome = netIncome[0]
        print(lastNetIncome)
        self.netIncome = lastNetIncome


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
        return '<Stock Object>'
