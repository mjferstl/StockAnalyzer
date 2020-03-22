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

        # variables for anayzing the stock
        self.GrahamNumber = None
        self.innerValue = None

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

        # Analyze Stock
        self.analyzeStock()


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


    def analyzeStock(self):
        if not self.mainDataLoaded:
            self.loadMainData()

        self.calcGrahamNumber()
    

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


    def calcGrahamNumber(self):
        if self.bookValuePerShare is not None:
            self.GrahamNumber = np.sqrt(15 * self.meanEarningsPerShare * 1.5 * self.bookValuePerShare)


    # Funktion zur Berechnung des sog. "inneren Wertes" der Aktie
    def calcInnerValue(self,renditeerwartung=8):
        self.innerValue = calcInnerValue10years(self.meanEarningsPerShare,self.Wachstumsrate,self.meanPriceEarningsRatio,renditeerwartung)


    # Funktion zur Formattierung der Ausgabe
    def __str__(self):
        if self.innerValue is None:
            self.calcInnerValue()

        strGrahamNumber = ''
        if self.GrahamNumber is not None:
            strGrahamNumber = 'Graham Number:     {gn:6.2f}'.format(gn=self.GrahamNumber) + ' ' + self.currencySymbol + '\n'

        #self.currentStockValue = self.getCurrentStockValue()
        strCurrentStockValue = ''
        if (self.currentStockValue is not None):
            strCurrentStockValue = 'Aktueller Kurs:    {val:6.2f}'.format(val=self.currentStockValue) + ' ' + self.currencySymbol + '\n'

        if self.currencySymbol is None:
            self.getCurrency()

        strDividend = ''
        if self.dividend is not None:
            strDividendYield = ''
            if self.currentStockValue is not None:
                strDividendYield = ' (' + u"\u2248" + '{divYield:3.1f}%)'.format(divYield=self.dividend/self.currentStockValue*100)
            strDividend = 'Dividend:          {div:6.2f}'.format(div=self.dividend) + ' ' + self.currencySymbol + strDividendYield + '\n'

        return '-'*27 + '\n' + \
            ' '*3 + self.name + '\n' + \
            'avg. weighted EPS: {eps:6.2f}'.format(eps=self.meanEarningsPerShare) + ' ' + self.currencySymbol + '\n' + \
            'avg. P/E:          {priceEarningsRatio:6.2f}'.format(priceEarningsRatio=self.meanPriceEarningsRatio) + '\n' + \
            strDividend + \
            '\n' + \
            'Fairer Wert:       {val:6.2f}'.format(val=self.innerValue) + ' ' + self.currencySymbol + '\n' + \
            strGrahamNumber + \
            strCurrentStockValue + \
            '-'*27 + '\n'


# ---------- FUNCTIONS ----------
#

def calcInnerValue10years(earningsPerShare,Wachstumsrate,priceEarningsRatio,Renditeerwartung,marginOfSafety=0.1):
    """
        Berechnung des "Inneren Wertes" (oft auch als "Fairer Wert" bezeichnet)
        Berechnungsgrundpagen:
        - angegebene Wachstumsrate gilt fuer die naechsten 10 Jahre
        - Margin of Safety: 10%, sofern nicht anders angegeben
    """
    # Berechnung des Gewinns pro Aktie in 10 Jahren
    gewinn10y = earningsPerShare*(Wachstumsrate**10)

    # Berechnung des Aktienpreises in 10 Jahren auf Grundlage des aktuellen Kurs-Gewinn-Verhältnisses
    price10y = gewinn10y*priceEarningsRatio

    # Berechnung des fairen/inneren Preises zum aktuellen Zeitpunkt auf Grundlage der Renditeerwartung
    innererWert = price10y/((1+(Renditeerwartung/100))**10)
    return innererWert*(1-marginOfSafety)