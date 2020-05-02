# -*- coding: utf-8 -*-

# ---------- MODULES ----------
# standard modules
import sys, os
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pandas import DataFrame
import pandas as pd
import json

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

# currencies
EURO = u"Euro"
DOLLAR = u"Dollar"


# ---------- CLASSES ----------
class Stock:

    """
        TODO: growth rate anhand einer regressionsgerade beim EPS berechnen (falls plausibel?)
        TODO: growth rate anhand einer regressionsgerade beim Cashflow berechnen (falls plausibel?)
        TODO: plotten der strongBuy, buy, hold, sell und strongSell empfehlungen (auch aus mehreren Quellen, z.B. yahoo finance, Finnhub, ...)
        TODO: Settings Datei entwerfen; Standardisierte Felder (zukünftiges CF Wachstum, zuküngtiges Gewinnwachstum) und einen Freitext, \
            dort koennen manuelle Infos oder Hinweise eingetragen werden. Pro Aktie ein File; bei Analysen wird immer der pessimistischste Wert \
            aus Analysten | eigene Meinung | extrapolierte Werte herangezogen 
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
    MARKET_CAP = 'marketCap'
    SHARES_OUTSTANDING = 'sharesOutstanding'

    # Format des Datums
    DATE_FORMAT = '%Y-%m-%d'


    def __init__(self,stockName,switchLoadData=LOAD_ALL_DATA):

        stockData = loadStockFile(stockName)
        self.symbol = stockData.stockSymbol
        self.indexSymbol = stockData.indexSymbol
        self.dates = stockData.dates
        self.assumptions = stockData.assumptions

        #self.growthRateAnnualy = growthRateAnnualyPrc/100

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
        # DataFrame for storing estimates for the future
        self.estimates = DataFrame()

        self.historicalData = None
        self.historicalDataRelative = None

        # storing recommendations for buying, holding and selling
        self.recommendations = None

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
        self.getEstimates()

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

    
    def getEstimates(self):
        epsEstimates = FinnhubClient(self.symbol).getEpsEstimates()

        df = DataFrame()
        for data in epsEstimates:
            eps = data['epsAvg']
            period = data['period']
            df.loc[self.EARNINGS_PER_SHARE,period] = eps

        # descending order of date column
        df = df.reindex(sorted(df.columns,reverse=True), axis=1)

        # add data frame to estimates data frame
        self.estimates = mergeDataFrame(self.estimates,df)

        return df


    def getBasicDataItem(self,keyName):
        return self.basicData[keyName]


    def isItemInBasicData(self,keyName):
        return keyName in self.basicData.keys()


    def getRecommendations(self):
        recommendations = FinnhubClient(self.symbol).getRecommendationsDataFrame()
        self.recommendations = recommendations
        return recommendations


    def getHistoricalStockPrice(self,startDate,endDate=None):

        # Start date
        start = datetime.strptime(startDate,Stock.DATE_FORMAT) + relativedelta(days=1)
        startDate = start.strftime(Stock.DATE_FORMAT)

        # End date
        if endDate is None:
            end = start + relativedelta(days=1)
        else:
            end = datetime.strptime(endDate,Stock.DATE_FORMAT) + relativedelta(days=1)
        endDate = end.strftime(Stock.DATE_FORMAT)

        # Load data from yahoo finance
        return yf.download(self.symbol,start=startDate,end=endDate)


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




class StockIndex():

    # Index Symbols
    DOW_JONES_INDEX_SYMBOL = '^DJI'
    DAX_INDEX_SYMBOL = '^GDAXI'
    MDAX_INDEX_SYMBOL = '^MDAXI'
    SDAX_INDEX_SYMBOL = '^SDAXI'

    def __init__(self,indexSymbol):

        self.symbol = indexSymbol
        self.ticker = yf.Ticker(indexSymbol)

        self.historicalData = None

        self.loadHistoricalData()

    def loadHistoricalData(self,startDate=None,endDate=None):

        if (startDate is None) and (endDate is None):
            return self.ticker.history(period="5y", interval = "1wk")
        else:
            if (startDate is None) and (endDate is not None):
                raise ValueError('Missing startDate. You passed endDate=' + str(endDate) + ' but no startDate')
            elif (startDate is not None) and (endDate is None):
                end = datetime.strptime(startDate)+1
                endDate = end.strftime(Stock.DATE_FORMAT)
            
            # add one day to start and end, to get the correct intervall
            start = datetime.strptime(startDate,Stock.DATE_FORMAT) + relativedelta(days=1)
            startDate = start.strftime(Stock.DATE_FORMAT)
            end = datetime.strptime(endDate,Stock.DATE_FORMAT) + relativedelta(days=1)
            endDate = end.strftime(Stock.DATE_FORMAT)

            # load data from yahoo finance
            return yf.download(self.symbol, start=startDate, end=endDate)




def loadStockFile(stockName,stocksFile='scripts/data/stocks.json'):

    if not os.path.isfile(stocksFile):
        raise Exception('The file "' + stocksFile + '" does not exist. This file needs to contain the stock list.')

    with open(stocksFile) as f:
        stockJSON = json.load(f)

    # Finden der angegebenen Aktie im JSON-File
    allStockNames = [s["Name"] for s in stockJSON["Stocks"]]
    if stockName not in allStockNames:
        raise ValueError('There is no stock named "' + stockName + '" in the file "' + stocksFile + '".')

    stock = stockJSON["Stocks"][allStockNames.index(stockName)]

    # Erstellen eines StockData Objekts
    stockData = StockData(stockName=stock["Name"],stockSymbol=stock["Symbol"])

    # Auslesen von Symbol und dem Index, in dem die Aktie gelistet ist
    stockIndex = stock["Index"]
    allIndexNames = [i["Name"] for i in stockJSON["Index"]]
    if stockIndex not in allIndexNames:
        raise ValueError('There is no index named "' + stockIndex + '" in the file "' + stocksFile + '".')

    stockData.indexName = stockIndex
    stockData.indexSymbol = stockJSON["Index"][allIndexNames.index(stockIndex)]["Symbol"]

    # Öffnen des zur Aktie zugehoerigen Data-Files mit
    # - der Wachstumsprognose
    # - Daten fuer das DCF-Verfahren
    # - Veroeffentlichungsterminen von Quartals- und Jahreszahlen
    data_file = 'scripts/data/' + stock["data_file"]
    if not os.path.isfile(data_file):
        raise Exception('The file "' + data_file + '" does not exist.')


    # Laden des zusaetzlichen Files mit den Daten zur Aktie
    with open(data_file) as f:
        stockExtraData = json.load(f)

    # Annahmen auslesen
    if "assumptions" not in stockExtraData.keys():
        raise KeyError('The key "assumptions" is missing in the file "' + data_file + '".')

    stockData.assumptions = stockExtraData["assumptions"]

    if "dates" not in stockExtraData.keys():
        raise KeyError('The key "dattes" is missing in the file "' + data_file + '".')

    stockData.dates = stockExtraData["dates"]

    return stockData

    


class StockData():

    def __init__(self,stockName,stockSymbol,indexName='',indexSymbol='',assumptions={},dates=[]):

        self._stockName = stockName
        self._stockSymbol = stockSymbol
        self._indexName = indexName
        self._indexSymbol = indexSymbol
        self._assumptions = assumptions
        self._dates = dates

    @property
    def stockName(self):
        return self._stockName

    @stockName.setter
    def stockName(self,name):
        self._stockName = name

    @property
    def stockSymbol(self):
        return self._stockSymbol

    @stockSymbol.setter
    def stockSymbol(self,symbol):
        self._stockSymbol = symbol

    @property
    def indexName(self):
        return self._indexName

    @indexName.setter
    def indexName(self,name):
        self._indexName = name

    @property
    def indexSymbol(self):
        return self._indexSymbol

    @indexSymbol.setter
    def indexSymbol(self,symbol):
        self._indexSymbol = symbol

    @property
    def assumptions(self):
        return self._assumptions

    @assumptions.setter
    def assumptions(self,assumptionsDict):
        if not isinstance(assumptionsDict,dict):
            raise TypeError('The assumptions need to be in a dict. ' + assumptionsDict + ' is not allowed.')
        self._assumptions = assumptionsDict

    @property
    def dates(self):
        return self._dates

    @dates.setter
    def dates(self,datesList):
        if not isinstance(datesList,dict):
            raise TypeError('The dates need to be in a dict. ' + datesList + ' is not allowed.')
        self._dates = datesList

    def __str__(self):
        return '<StockData object "' + self._stockName + '" ("' + self._stockSymbol + '")>'
    