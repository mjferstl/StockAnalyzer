
# ---------- MODULES ----------
# standard modules
import numpy as np
import pandas as pd

import datetime
from dateutil.relativedelta import relativedelta
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# custom modules
from classes.Stock import Stock, StockIndex
from classes.FinnhubAPI import FinnhubClient
from utils.generic import npDateTime64_2_str

# ---------- CLASSES ----------
class StockAnalyzer():

    # value shared across all class instances
    # investment time: 10 years
    investmentHorizon = 10

    # variables
    NET_MARGIN = 'net margin'
    RETURN_ON_EQUITY = 'return on equity'

    #
    useWeightedHistoricalData = False
    weightingStep = 1
    
    def __init__(self,stock,index=None):
        if not isinstance(stock,Stock):
            raise TypeError('Object ' + str(stock) + ' is no instance of class Stock')

        if index is None:
            self.stockIndex = None
        elif isinstance(index,StockIndex):
            self.stockIndex = index
        elif isinstance(index,str):
            self.stockIndex = StockIndex(index)
        else:
            raise TypeError('The index needs to be a \'str\' or an object of StockIndex, but it is \'' + str(type(index)) + '.')
        
        self.stock = stock

        self.marginOfSafety = self.stock.assumptions["margin_of_safety"]

        # variables for anayzing the stock
        # EPS
        self.meanWeightedEps = None
        self.epsWeightYears = None
        self.calcWeightedEps()

        # P/E (Price Earnings Ratio)
        self.priceEarningsRatio = None
        self.getPriceEarningsRatio()

        self._GrahamNumber = None
        self.recommendations = None
        self.LevermannScore = None

        #
        self._NetMargin = None
        self._ReturnOnEquity = None
        self._ReturnOnAssets = None
        self._FreeCashFlowBySales = None
        self._PriceToSales = None
        self._PriceToEarnings = None

        self.dividendYield = 0

        # analyze the stock
        self.analyzeStock()

    
    def analyzeStock(self):
        self.calcGrahamNumber()
        self.calcDCF()
        self.calcLevermannScore()
        self.recommendations = self.getRecommendations()
        self.NetMargin
        self.calcReturnOnEquity()
        self.calcReturnOnAssets()
        self.calcFreeCashFlowBySales()
        self.PriceToSales

    @property
    def GrahamNumber(self):
        if self._GrahamNumber is None:
            self.calcGrahamNumber()
        return self._GrahamNumber

    @property
    def ReturnOnEquity(self):
        if self._ReturnOnEquity is None:
            self.calcReturnOnEquity()
        return self._ReturnOnEquity

    @property
    def ReturnOnAssets(self):
        if self._ReturnOnAssets is None:
            self.calcReturnOnAssets()
        return self._ReturnOnAssets

    @property
    def FreeCashFlowBySales(self):
        if self._FreeCashFlowBySales is None:
            self.calcFreeCashFlowBySales()
        return self._FreeCashFlowBySales

    @property
    def PriceToSales(self):
        if self._PriceToSales is None:
            self.calcPriceToSales()
        return self._PriceToSales

    @property
    def NetMargin(self):
        if self._NetMargin is None:
            self.calcNetMargin()
        return self._NetMargin


    def calcGrahamNumber(self):
        if (self.meanWeightedEps is not None) and (self.stock.isItemInBasicData(Stock.BOOK_VALUE_PER_SHARE)):

            if (self.meanWeightedEps < 0):
                print(' +++ avg. weighted EPS < 0! Stock: ' + self.stock.symbol + ' (' + self.stock.name + ') +++')
                self.meanWeightedEps = 0
            if (self.stock.getBasicDataItem(Stock.BOOK_VALUE_PER_SHARE) < 0):
                print(' +++ book value per share < 0! Stock: ' + self.stock.symbol + ' (' + self.stock.name + ') +++')
                
            self._GrahamNumber = np.sqrt(15 * self.meanWeightedEps * 1.5 * self.stock.getBasicDataItem(Stock.BOOK_VALUE_PER_SHARE))
        else:
            self._GrahamNumber = 0


    def calcDCF(self):
        # Free Chashflow der letzten Jahre
        CF = self.stock.financialData.loc['freeCashFlow',:].copy()

        CF.fillna(CF.mean(), inplace=True) # TODO: NaN Werte werden durch Mittelwert ersetzt

        # Sortierung in aufsteigender Reihenfolge (alt -> neu)
        CF_sorted = []
        for date in sorted(CF.index.values.copy()):
            CF_sorted.append(CF.loc[date])

        # Berechnung 
        model = linearRegression(range(len(CF_sorted)),CF_sorted,plotResult=False)
        FCFstartValue = model.predict(np.array([len(CF_sorted)-1]).reshape(1, -1))[0]
        
        # Wachstumsrate der naechsten 10 Jahre
        discountRate = self.stock.assumptions["discountRate"]/100

        # Free Cash Flow der naechsten 5 Jahre
        growthRate = self.stock.assumptions['growth_year_1_to_5']/100
        discountedCashFlow = []
        FCF = []
        for i in range(1,6):
            FCF.append((FCFstartValue*(1+growthRate)**i))
            discountedCashFlow.append(FCF[-1] / ((1 + discountRate)**i))

        # Free Cash Flow der Jahre 6-10
        growthRate = self.stock.assumptions['growth_year_6_to_10']/100
        for i in range(6,11):
            FCF.append((FCFstartValue*(1+growthRate)**i))
            discountedCashFlow.append(FCF[-1] / ((1 + discountRate)**i))

        # Free Cash Flow insgesamt ab dem 11. Jahr (perpetuity value) im heutigen Wert (discounted perpetuity value)
        # - FCF_10: Free Cash Flow in 10 Jahren
        # - growthRate_10: Wachstum des Free Cash Flows nach dem 10. Jahr
        # Formel: FCF_10 * (1 + growthRate_10) / ((discountRate - growthRate_10) * (1 + discountRate))
        growthRate = self.stock.assumptions['growth_year_10ff']/100
        # perpetuity value
        FCF.append((FCF[-1] * (1 + growthRate)) / (discountRate - growthRate))
        # discounted perpetuity value
        discountedCashFlow.append(FCF[-1] / ((1 + discountRate)**10))

        # Summe der, auf den aktuellen Zeitpunkt bezogenen, zukuenfitgen Cashflows
        totalEquityValue = sum(discountedCashFlow)

        # Wert einer Aktie zum aktuellen Zeitpunkt auf Grundlage aller zkünftigen Free Cash Flows
        # Beruecksichtigung einer Margin of safety
        marginOfSafety = self.marginOfSafety/100
        sharesOutstanding = self.stock.keyStatistics[Stock.SHARES_OUTSTANDING]
        perShareValue = totalEquityValue/sharesOutstanding/(1 + marginOfSafety)

        self.presentShareValue = perShareValue


    # Berechnung des Levermann scores
    def calcLevermannScore(self):
        if (self.stockIndex is not None):
            self.LevermannScore = LevermannScore(self.stock,self.stockIndex)
        else:
            print('Zur Berechnung des Levermann scores muss ein Index angegeben werden')

    
    def calcPiotroskiFScore(self):
        # TODO calcPiotroskiFScore implementieren
        # Nettogewinn
        #
        # Operating Cashflow
        #
        # Gesamtkapitalrendite
        #
        # Operating Cashflow versus Nettogewinn
        #
        # Verschuldungsgrad
        #
        # Liquidität 3. Grades
        #
        # Aktienanzahl
        #
        # Rohmarge
        #
        # Kapitalumschlag
        #
        # Gesamtbewertung
        # Hoch: 7-9P, Mittel: 3-6P, Niedrig: 0-2P
        pass

    def calcTechnicalIndicator(self):
        # TODO calcTechincalIndicator implementieren
        # GD 200 Linie
        # Historische Werte
        # MACD
        # Bewertung: 3 von 3 positiv -> kaufen
        # Bewertung: 3 von 3 negativ -> verkaufen
        # Bewertung: 0-2 von 3 -> halten
        pass


    def getMeanWeightedEPS(self):
        if (self.meanWeightedEps is None) or (self.epsWeightYears is None):
            self.calcWeightedEps()

        return self.meanWeightedEps, self.epsWeightYears

    def calcWeightedEps(self):

        epsKey = 'dilutedEPS'
        
        if (self.stock.financialData is not None) and (epsKey in self.stock.financialData.index.values):
            # get historical EPS data
            epsHistory = self.stock.financialData.loc[epsKey,:].copy()

            # remove NaN values
            for row in epsHistory.index.values:
                if np.isnan(epsHistory.loc[row]):
                    epsHistory = epsHistory.drop(row)

            if (self.useWeightedHistoricalData):
                # create weighting with the global defined stepsize
                weighting = [1]
                for i in range(len(epsHistory)-1):
                    weighting.append(weighting[-1]+StockAnalyzer.weightingStep)
                weighting = list(reversed(weighting))
            else:
                # same factor for every year
                weighting = [1 for i in range(len(epsHistory))]

            # calculate the weighted eps 
            weightedEps = [factor*value for value,factor in zip(epsHistory,weighting)]
            self.meanWeightedEps = sum(weightedEps)/sum(weighting)
            self.epsWeightYears = len(epsHistory)
        else:
            self.meanWeightedEps = self.stock.getBasicDataItem(Stock.EARNINGS_PER_SHARE)

    
    def getPriceEarningsRatio(self):
        self.priceEarningsRatio = self.stock.getBasicDataItem(Stock.PE_RATIO)


    def getRecommendations(self):
        if self.recommendations is None:
            recommendations = FinnhubClient(self.stock.symbol).getRecommendationsDataFrame()
            self.recommendations = recommendations
        
        return self.recommendations


    def getLatestRecommendations(self):
        latestRecommendations = self.getRecommendations().iloc[0,:]
        latest = latestRecommendations[['strongBuy','buy','hold','sell','strongSell']]
        return latest


    def calcNetMargin(self):
        if self.stock.financialData is None:
            raise Exception('The stock has no historical financial data. "Total Revenue" and "Net Income" needed!')
        else:
            # Nettogewinn
            netIncome = self.stock.financialData.loc['Net Income',:].copy()
            # Umsatz
            revenues = self.stock.financialData.loc['Total Revenue',:].copy()

            dic = {}
            for index in sorted(netIncome.index, reverse=True):
                dic[index] = netIncome.loc[index]/revenues.loc[index]

            df = pd.Series(dic, index=dic.keys())
            df.reindex(sorted(df.index, reverse=True))
            self._NetMargin = df

            return df


    def calcReturnOnEquity(self):
        if self.stock.financialData is None:
            raise Exception('The stock has no historical financial data. "Total Stockholder Equity" and "Net Income" needed!')
        else:
            # Eigenkapital
            equity = self.stock.financialData.loc['Total Stockholder Equity',:].copy()
            # Betriebseinkommen
            income = self.stock.financialData.loc['Net Income',:].copy()

            # Berechnung der Eigenkapitalrendite fuer jedes Jahr
            dic = {}
            for index in sorted(equity.index, reverse=True):
                dic[index] = income[index]/equity[index]

            df = pd.Series(dic, index=dic.keys())
            self._ReturnOnEquity = df

            return df

    def calcReturnOnAssets(self):
        if self.stock.financialData is None:
            raise Exception('The stock has no historical financial data. "Total Assets" and "Net Income" needed!')
        else:
            # Gesamtvermögen
            totalAssets = self.stock.financialData.loc['Total Assets',:].copy()
            # Betriebseinkommen
            income = self.stock.financialData.loc['Net Income',:].copy()

            # Berechnung der Kapitalrendite fuer jedes Jahr
            dic = {}
            for index in sorted(totalAssets.index,reverse=True):
                dic[index] = income[index]/totalAssets[index]

            df = pd.Series(dic, index=dic.keys())
            self._ReturnOnAssets = df

            return df


    def calcFreeCashFlowBySales(self):
        if self.stock.financialData is None:
            raise Exception('The stock has no historical financial data. "Total Revenue" and "freeCashFlow" needed!')
        else:
            # Umsatz
            revenues = self.stock.financialData.loc['Total Revenue',:].copy()
            # Free Cash Flow
            freeCashFlow = self.stock.financialData.loc['freeCashFlow',:].copy()
            
            # Berechnung des Free cash flows bezogen auf die Einnahmen fuer jedes Jahr
            dic = {}
            for index in sorted(revenues.index, reverse=True):
                dic[index] = freeCashFlow[index]/revenues[index]

            df = pd.Series(dic, index=dic.keys())
            self._FreeCashFlowBySales = df

            return df


    def calcPriceToSales(self):
        if self.stock.financialData is None:
            raise Exception('The stock has no historical financial data. "Total Revenue" and "Total Stockholder Equity" needed!')
        else:
            # Umsatz
            revenues = self.stock.financialData.loc['Total Revenue',:].copy()
            # Marktkapitalisierung
            totalStockHolderEquity = self.stock.financialData.loc['Total Stockholder Equity',:].copy() 

            # Price to Sales fuer jedes Jahr
            P_S = pd.Series()
            for date in list(revenues.index.values.copy()):
                # Price/Sales
                price = totalStockHolderEquity.loc[date]
                sales = revenues.loc[date]
                P_S.loc[date] = price/sales

            self._PriceToSales


    def printAnalysis(self):

        if self.priceEarningsRatio is None:
            self.getPriceEarningsRatio()

        # variables for formatting the console output
        stringFormat = "35s"
        dispLineLength = 50
        sepString = '-'*dispLineLength + '\n'

        # string to print the dividend and the dividend yield
        strDividend = ''
        if self.stock.isItemInBasicData(Stock.DIVIDEND):
            strDividendYield = ''

            stockPrice = self.stock.getBasicDataItem(Stock.MARKET_PRICE)
            if stockPrice is not None:
                strDividendYield = ' (' + u"ca. " + '{divYield:3.1f}%)'.format(divYield=self.stock.getBasicDataItem(Stock.DIVIDEND)/stockPrice*100)
            strDividend = '{str:{strFormat}}{div:6.2f}'.format(str='Dividend:',div=self.stock.getBasicDataItem(Stock.DIVIDEND),strFormat=stringFormat) + ' ' + self.stock.currencySymbol + strDividendYield + '\n'

        strWeightedEps = ''
        if (self.meanWeightedEps != self.stock.getBasicDataItem(Stock.EARNINGS_PER_SHARE)) and (self.epsWeightYears is not None):
            strEntry = 'avg. EPS ({years:.0f}y):'.format(years=self.epsWeightYears)
            strWeightedEps = '{str:{strFormat}}{epsw:6.2f}'.format(str=strEntry,epsw=self.meanWeightedEps,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

        # string to print the graham number
        strGrahamNumber = '{str:{strFormat}}{gn:6.2f}'.format(str='Graham number:',gn=self.GrahamNumber,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

        strNetPresentValue = ''
        if self.presentShareValue is not None:
            if self.presentShareValue > self.stock.getBasicDataItem(Stock.MARKET_PRICE):
                strNPVcomment = 'time to invest!'
            else:
                strNPVcomment = 'too expensive...'
            strNetPresentValue = '{str:{strFormat}}{gn:6.2f}'.format(str='Present share value (DCF):',gn=self.presentShareValue,strFormat=stringFormat) + \
                ' ' + self.stock.currencySymbol + ' (' + strNPVcomment + ')\n'

        # string to print the stock's current value
        strCurrentStockValue = ''
        stockPrice = self.stock.getBasicDataItem(Stock.MARKET_PRICE)
        if (stockPrice is not None):
            strCurrentStockValue = '{str:{strFormat}}{val:6.2f}'.format(str="Current share price:",val=stockPrice,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

        # Free Cash flow bezogen auf die Einnahmen
        limit = 5/100.0
        isGood = sum([1 if fcfps > limit else 0 for fcfps in self.FreeCashFlowBySales]) == len(self.FreeCashFlowBySales)
        avgFcfps = sum(self.FreeCashFlowBySales)/len(self.FreeCashFlowBySales)
        if isGood: # groesser als 5%
            strFcfpsComment = 'good, always >= {limit:.0f}%'.format(limit=limit*100)
        elif avgFcfps > limit:
                strFcfpsComment = 'ok, avg >= {limit:.0f}%'.format(limit=limit*100)
        else:
            strFcfpsComment = '?'
        # String fuer die Ausgabe
        strFreeCashFlowPerSales = '{str:{strFormat}}{val:6.2f}'.format(str="Free Cash Flow/Sales (" + str(len(self.FreeCashFlowBySales)) + "y avg.):",val=avgFcfps*100,strFormat=stringFormat) + \
            '% (' + strFcfpsComment + ')\n'    

        # Nettogewinn
        limit = 15/100.0
        limit2 = 5/100.0
        isGood = sum([1 if nm > limit else 0 for nm in self.NetMargin]) == len(self.NetMargin)
        isBad = sum([1 if nm < limit2 else 0 for nm in self.NetMargin]) == len(self.NetMargin)
        avgNetMargin = sum(self.NetMargin)/len(self.NetMargin)
        if isGood: # groesser als 15%
            strNetMarginComment = 'good, always >= {limit:.0f}%'.format(limit=limit*100)
        elif avgNetMargin > limit:
            strNetMarginComment = 'ok, avg >= {limit:.0f}%'.format(limit=limit*100)
        elif isBad: # kleiner als 5%
            strNetMarginComment = 'Caution!, avg < {limit:.0f}%'.format(limit=limit2*100)
        else:
            strNetMarginComment = '-'

        strNetMargin = '{str:{strFormat}}{val:6.2f}'.format(str="Net margin (" + str(len(self.NetMargin)) + "y avg.):",val=avgNetMargin*100,strFormat=stringFormat) + \
            '% (' + strNetMarginComment + ')\n'

        # Eigenkapitalrenidte
        limit = 15/100.0
        isGood = sum([1 if roe > limit else 0 for roe in self.ReturnOnEquity]) == len(self.ReturnOnEquity)
        avgRoE = sum(self.ReturnOnEquity)/len(self.ReturnOnEquity)
        if isGood: 
            strRoEcomment = 'good, always >= {limit:.0f}%'.format(limit=limit*100)
        elif avgRoE > limit:
            strRoEcomment = 'ok, avg >= {limit:.0f}%'.format(limit=limit*100)
        else:
            strRoEcomment = '?'
        # String fuer die Ausgabe
        strReturnOnEquity = '{str:{strFormat}}{val:6.2f}'.format(str="Return on equity (" + str(len(self.ReturnOnEquity)) + "y avg.):",val=avgRoE*100,strFormat=stringFormat) + \
            '% (' + strRoEcomment + ')\n'

        # Kapitalrendite
        limit = 6/100.0
        isGood = sum([1 if roa >= limit else 0 for roa in self._ReturnOnAssets]) == len(self.ReturnOnAssets)
        avgRoA = sum(self.ReturnOnAssets)/len(self.ReturnOnAssets)
        if isGood:
            strRoAcomment = 'good, always >= {limit:.0f}%'.format(limit=limit*100)
        elif avgRoA >= limit:
            strRoAcomment = 'ok, avg >= {limit:.0f}%'.format(limit=limit*100)
        else:
            strRoAcomment = '?'
        # String fuer die Ausgabe
        strReturnOnAssets = '{str:{strFormat}}{val:6.2f}'.format(str="Return on assets (" + str(len(self.ReturnOnAssets)) + "y avg.):",val=avgRoA*100,strFormat=stringFormat) + \
            '% (' + strRoAcomment + ')\n'


        # format margin around stock name
        stockNameOutput = self.stock.name
        if (len(self.stock.name) < dispLineLength):
            margin = int((dispLineLength-len(self.stock.name))/2)
            stockNameOutput = ' '*margin + self.stock.name + ' '*margin

        string2Print = sepString + \
            stockNameOutput + '\n' + \
            sepString + \
            '{str:{strFormat}}{eps:6.2f}'.format(str='EPS:',eps=self.stock.getBasicDataItem(Stock.EARNINGS_PER_SHARE),strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n' + \
            strWeightedEps + \
            '{str:{strFormat}}{priceEarningsRatio:6.2f}'.format(str='P/E:',priceEarningsRatio=self.priceEarningsRatio,strFormat=stringFormat) + '\n' + \
            strDividend + \
            sepString + \
            'Analysis:\n' + \
            ' - margin of safety: {marginOfSafety:2.0f}%\n'.format(marginOfSafety=self.marginOfSafety) + \
            ' - investment horizon: {years:.0f} years\n'.format(years=self.investmentHorizon) + \
            ' - exp. growth: 1-5y: {grwth:.1f}%, 6-10y: {grwth2:.1f}%, 10ff y: {grwth3:.1f}%\n'.format(grwth=self.stock.assumptions["growth_year_1_to_5"], \
                grwth2=self.stock.assumptions["growth_year_6_to_10"],grwth3=self.stock.assumptions["growth_year_10ff"]) + '\n' + \
            strGrahamNumber + \
            strNetPresentValue + \
            strNetMargin + \
            strReturnOnEquity + \
            strReturnOnAssets + \
            strFreeCashFlowPerSales + \
            sepString + \
            strCurrentStockValue + \
            sepString

        # print to the console
        print(string2Print)

        if (self.LevermannScore is not None):
            self.LevermannScore.printScore()

        print('\n')



class LevermannScore():

    MOMENTUM_CONST = '-'
    MOMENTUM_RISING = 'steigend'
    MOMENTUM_FALLING = 'fallend'

    REVERSAL_DEFAULT = 'nicht eindeutig'
    REVERSAL_POSITIVE = 'Aktie schlaegt Index'
    REVERSAL_NEGATIVE = 'Aktie schlechter als Index'

    # Kommentare zum berechneten Score
    COMMENT_BUY = 'kaufen'
    COMMENT_HOLD = 'halten'
    COMMENT_SELL = 'verkaufen'
    COMMENT_DEFAULT = ''


    def __init__(self,stock,index):
        if not isinstance(stock,Stock):
            raise TypeError('Object ' + str(stock) + ' is no instance of class Stock')

        if not isinstance(index,StockIndex):
            raise TypeError('Object ' + str(index) + ' is no instance of class StockIndex')
        
        # Speichern des Objekts
        self.stock = stock
        self.stockIndex = index
        self.Score = None
        self.Comment = self.COMMENT_DEFAULT

        # Werte fuer die Berechnung des Levermann-Scores
        # Return on Equity (RoE), Eigenkapitalrenite letztes Jahr
        self._ReturnOnEquity = None 
        # EBIT-Marge letztes Jahr
        self.EbitMarge = None
        # Eigenkapitalquote letztes Jahr
        self.EKratio = None
        # KGV 5 Jahre (letzte 3 Jahre, aktuelles Jahr und nächstes Jahr)
        self.KGV_5y = None
        # KGV aktuell
        self.KGV_now = None
        # Analystenmeinungen
        self.recommendations = None
        # Reaktion auf Quartalszahlen
        self.quarterlyReaction = None
        # Gewinnrevision
        self.profitRevision = None
        # Kurs heute gg. Kurs vor 6 Monaten
        self.sharePriceRelative_6m = None
        # Kurs heute gg. Kurs vor 1 Jahr 
        self.sharePriceRelative_1y = None
        # Kursmomentum steigend 
        self.sharePriceMomentum = None
        # Dreimonatsreversal 
        self.reversal_3m = None
        # Gewinnwachstum 
        self.profitGrowth = None

        # Berechnung des LevermannScores fuer die Aktien
        self.calcScore()

    def getScore(self):
        if self.Score is None:
            self.calcScore()

        return self.Score


    def calcScore(self):
        # TODO calcLevermannScore implementieren
        LevermannScore = 0
        #print(self.stock.financialData)

        # RoE (Return on Equity) Eigenkapitalrendite (Gewinn / Eigenkapital)
        # Eigenkapital
        equity = list(self.stock.financialData.loc['Total Stockholder Equity',:].copy())
        # TODO Klärung ob "Net Income" (abzgl. Steuern etc.) oder "Operating Income" (Steuern noch nicht abgezogen)
        # laut dem Wert auf "https://aktien.guide/levermann-strategie/Microsoft-US5949181045" muss der Eintrag aus "Operating Income" genutzt werden
        # da sonst ein zu niedriger Prozentwert entsteht
        Gewinn = list(self.stock.financialData.loc['Operating Income',:].copy())

        # Eigenkapitalrendite fuer jedes Jahr
        annualyRoE = [gewinn/ek*100 for gewinn,ek in zip(Gewinn,equity)]
        # Eigenkapitalrendite: Mittelwert ueber die Jahre
        RoE = sum(annualyRoE)/len(annualyRoE)
        self._ReturnOnEquity = RoE

        # RoE > 20% -> +1, 10% < RoE < 20% -> 0, RoE < 10% -> -1
        if (RoE > 20):
            LevermannScore += 1
        elif (RoE < 10):
            LevermannScore -= 1

        # EBIT-Marge (EBIT / Umsatz)
        # EBIT
        EBIT = list(self.stock.financialData.loc['Ebit',:].copy())
        if 0 in EBIT:
            print('\n +++ EBIT enthält mindestens einen Eintrag mit 0 +++')
            print(self.stock.financialData.loc['Ebit',:])
            print(self.stock.financialData)
            print('\n')

        # Umsatz
        totalSales = list(self.stock.financialData.loc['Total Revenue',:].copy())

        # EBIT-Marge der letzten Jahre und Mittelwert
        annualyEbitMarge = [ebit/umsatz*100 for ebit,umsatz in zip(EBIT,totalSales)]
        EbitMarge = sum(annualyEbitMarge)/len(annualyEbitMarge)
        self.EbitMarge = EbitMarge

        # EBIT-Marge > 12% -> +1, 6% < EBIT-Marge < 12% -> 0, EBIT-Marge < 6% -> -1
        if (EbitMarge > 12):
            LevermannScore += 1
        elif (EbitMarge < 6):
            LevermannScore -= 1

        # EKQ Eigenkapitalquote
        # Eigenkapital (schon vorhanden, da bei RoE verwendet)
        # Gesamtverbindlichkeiten + Eigenkapital
        GK = list(self.stock.financialData.loc['Total Assets',:].copy())

        # Eigenkapitalquote
        annualyEKratio = [ek/gk*100 for ek,gk in zip(equity,GK)]
        EKratio = sum(annualyEKratio)/len(annualyEKratio)
        self.EKratio = EKratio

        # EKQ > 25% -> +1, 15% < EKQ < 25% -> 0, EKQ < 15% -> -1
        if (EKratio > 25):
            LevermannScore += 1
        elif (EKratio < 15):
            LevermannScore -= 1

        # KGV aktuelles Jahr
        # 
        currentYear = int(datetime.datetime.utcnow().strftime('%Y'))
        nextYear = currentYear+1

        # Geschaetztes EPS 
        EPS_estimates = self.stock.estimates.loc[self.stock.EARNINGS_PER_SHARE,:].copy()

        # Geschaetztes EPS fuer das aktuelle Jahr
        # Datum finden
        dateKey_this_year = [d for d in EPS_estimates.index.values if str(currentYear) in d]
        dateKey_next_year = [d for d in EPS_estimates.index.values if str(nextYear) in d]
        EPS_est_this_year = EPS_estimates.loc[dateKey_this_year[0]]
        EPS_est_next_year = EPS_estimates.loc[dateKey_next_year[0]]

        KGV = self.stock.getBasicDataItem(self.stock.MARKET_PRICE)/EPS_est_this_year
        self.KGV_now = KGV
        
        # 0 < KGV < 12 -> +1, 12 < KGV < 16 -> 0, KGV < 0, KGV > 16 -> -1
        if (KGV < 12):
            LevermannScore += 1
        elif (KGV > 16):
            LevermannScore -= 1

        # KGV 5 Jahre (letzten 3 Jahre, aktuelles Jahr, nächstes Jahr)
        # EPS der letzten Jahre auslesen und von alt zu neu sortieren
        EPSdf = self.stock.financialData.loc['dilutedEPS',:].copy()
        # Die Eintraege absteigend nach dem Datum auslesen
        EPS = [EPSdf.loc[date] for date in sorted(EPSdf.index,reverse=True)]
        # alt zu neu
        EPS.reverse()

        # EPS-Schaetzung fuer aktuelles und naechstes Jahr anhaengen
        EPS.append(EPS_est_this_year)
        EPS.append(EPS_est_next_year)

        # nur die letzten 5 Eintraege
        if len(EPS) > 5:
            EPS = EPS[-5:]
        
        # NaN-Werte durch den Mittelwert ersetzen
        if ('NaN' in str(EPS)) or ('nan' in str(EPS)):
            EPS_wo_nan = [eps for eps in EPS if not np.isnan(eps)]
            EPS_avg = sum(EPS_wo_nan)/len(EPS_wo_nan)
            EPS = [eps if not np.isnan(eps) else EPS_avg for eps in EPS]

        #print('EPS der letzten Jahre: ' + str(EPS))

        # mittleres EPS des 5-Jahres-Zeitraums berechnen
        EPS_mean_5y = sum(EPS)/len(EPS)

        # aktueller Kurs der Aktie
        stockPrice = self.stock.getBasicDataItem(self.stock.MARKET_PRICE)

        # Wert zur Ermittlung des LevermannScores berechnen
        KGV_5y = stockPrice/EPS_mean_5y
        self.KGV_5y = KGV_5y

        # 0 < KGV < 12 -> +1, 12 < KGV < 16 -> 0, KGV < 0, KGV > 16 -> -1
        if (KGV_5y < 12):
            LevermannScore += 1
        elif (KGV_5y > 16):
            LevermannScore -= 1

        #
        # Mittelwert Analystenmeinung (Kaufen=1, Halten=2, Verkaufen=3)
        analystRecommendations = self.stock.getRecommendations()
        # Datum (Index) absteigend sortieren
        analystRecommendations.reindex(sorted(analystRecommendations.index,reverse=True), axis=0)
        newestRecommendations = analystRecommendations.iloc[0,:]
        # Auslesen der Meinungen 
        recommendationsBuy = newestRecommendations.loc['strongBuy'] + newestRecommendations.loc['buy']
        recommendationsHold = newestRecommendations.loc['hold']
        recommendationsSell = newestRecommendations.loc['sell'] + newestRecommendations.loc['strongSell']

        # Anzahl aller Analystenmeinungen
        numRecommendations = recommendationsBuy + recommendationsHold + recommendationsSell

        # Bewertung Kaufen=1, Halten=2, Verkaufen=3
        avgRecScore = (recommendationsBuy*1 + recommendationsHold*2 + recommendationsSell*3)/numRecommendations
        self.recommendations = avgRecScore

        # 2,5 < Mittelwert -> +1, 1,5 < Mittelwert < 2,5 -> 0, Mittelwert < 1,5 -> -1
        if (avgRecScore >= 2.5):
            LevermannScore += 1
        elif (avgRecScore <= 1.5):
            LevermannScore -= 1

        # Reaktion auf Quartalszahlen

        # Daten fuer das vergangene Jahr laden, da diese mehrfach benoetigt werden
        today = datetime.datetime.utcnow()
        date_1y_ago = today + relativedelta(years=-1)
        date_1y_ago_str = date_1y_ago.strftime(Stock.DATE_FORMAT)

        # Wert fuer die Aktie und den Index
        stock_1y_ago = self.stock.getHistoricalStockPrice(startDate=date_1y_ago_str,endDate=today.strftime(Stock.DATE_FORMAT))
        index_1y_ago = self.stockIndex.loadHistoricalData(startDate=date_1y_ago_str,endDate=today.strftime(Stock.DATE_FORMAT))

        # 
        if (self.stock.dates is not None) and ("quarterlyReports" in self.stock.dates):
            # get latest date of quarterly reports of the past
            quarterlyReportDates = [qrd["date"] for qrd in self.stock.dates["quarterlyReports"] if qrd["date"] < today.strftime(Stock.DATE_FORMAT)]
            lastquarterlyReportDate = sorted(quarterlyReportDates,reverse=True)[0]
            date_quarterlyReport_nearest = findNearestDate(lastquarterlyReportDate,npDateTime64_2_str(stock_1y_ago.index.values.copy()))

            # Eröffnungskurs Aktie und Index am Tag der Veröffentlichung der Quartalszahlen
            stockOpen1 = stock_1y_ago.loc[date_quarterlyReport_nearest,'Open']
            indexOpen1 = index_1y_ago.loc[date_quarterlyReport_nearest,'Open']

            # Eroeffnungskurs am nächsten Handelstag
            nextDateIndex = npDateTime64_2_str(stock_1y_ago.index.values.copy()).index(date_quarterlyReport_nearest)+1
            stockOpen2 = stock_1y_ago.iloc[nextDateIndex].loc['Open']
            indexOpen2 = index_1y_ago.iloc[nextDateIndex].loc['Open']

            # Änderung in %
            stockChange = stockOpen2/stockOpen1-1
            indexChange = indexOpen2/indexOpen1-1
            reaction = (stockChange - indexChange)*100
            self.quarterlyReaction = reaction

            if reaction > 1:
                LevermannScore += 1
            elif reaction < -1:
                LevermannScore -= 1
        else:
            print('\n +++ Fehlende Daten: Datum der Veröffentichung der Quartalszahlen fehlt +++\n')
            print(self.stock.dates)


        # Gewinnrevisionen
        #

        # Kursverlauf der letzten 12 Monate
        #
        
        # Kurs heute
        stockPrice_today = self.stock.getBasicDataItem(self.stock.MARKET_PRICE)
        # Kurs vor einem Jahr
        date_1y_ago_nearest = findNearestDate(date_1y_ago,npDateTime64_2_str(stock_1y_ago.index.values.copy()))
        price_1y_ago = stock_1y_ago.loc[date_1y_ago_nearest,'Close']
        
        
        # relative Aenderung seit einem Jahr
        relativeChangePrc_1y = (stockPrice_today/price_1y_ago-1)*100
        self.sharePriceRelative_1y = relativeChangePrc_1y

        # Veraenderung > 5% -> +1, -5% < Veraenderung < 5% -> 0, Veraenderung < -5% -> -1
        if (relativeChangePrc_1y > 5):
            LevermannScore += 1
        elif (relativeChangePrc_1y < -5):
            LevermannScore -= 1

        
        # Kursverlauf der letzten 6 Monate
        # historischer Wert vor 6 Monaten
        date_6m_ago = today + relativedelta(months=-6)
        date_6m_ago_nearest = findNearestDate(date_6m_ago,npDateTime64_2_str(stock_1y_ago.index.values.copy()))
        price_6m_ago = stock_1y_ago.loc[date_6m_ago_nearest,'Close']
        relativeChangePrc_6m = (stockPrice_today/price_6m_ago-1)*100
        self.sharePriceRelative_6m = relativeChangePrc_6m

        # Veraenderung > 5% -> +1, -5% < Veraenderung < 5% -> 0, Veraenderung < -5% -> -1
        if (relativeChangePrc_6m > 5):
            LevermannScore += 1
        elif (relativeChangePrc_6m < -5):
            LevermannScore -= 1


        # Kursmomentum
        # Kursaenderung letzte 6m > +5% UND Kursaenderung seit 1 Jahr < +5% -> +1
        # Kursaenderung letzte 6m < -5% UND Kursaenderung seit 1 Jahr > -5% -> -1
        self.sharePriceMomentum = self.MOMENTUM_CONST
        if (relativeChangePrc_6m > 5) and (relativeChangePrc_1y < 5):
            LevermannScore += 1
            self.sharePriceMomentum = self.MOMENTUM_RISING
        elif (relativeChangePrc_6m < -5) and (relativeChangePrc_1y > -5):
            LevermannScore -= 1
            self.sharePriceMomentum = self.MOMENTUM_FALLING


        # Reversaleffekt der letzten drei Monate
        # Vergleich der Aktienperformance mit der Performance des Index
        date_4m_ago = today + relativedelta(months=-4)
        date_3m_ago = today + relativedelta(months=-3)
        date_2m_ago = today + relativedelta(months=-2)
        date_1m_ago = today + relativedelta(months=-1)
        

        # Performance der Aktie
        stockPrices_3m, indexPrices_3m = [], []
        dateList = npDateTime64_2_str(stock_1y_ago.index.values)
        for date in [date_3m_ago,date_2m_ago,date_1m_ago,today]:
            # finden eines passenden Datums
            date_str = date.strftime(Stock.DATE_FORMAT)
            if date_str in dateList:
                stockPrices_3m.append(stock_1y_ago.loc[date_str,'Close'])
                indexPrices_3m.append(index_1y_ago.loc[date_str,'Close'])
            else:
                nearestDate = findNearestDate(date,dateList)
                stockPrices_3m.append(stock_1y_ago.loc[nearestDate,'Close'])
                indexPrices_3m.append(index_1y_ago.loc[nearestDate,'Close'])

        # Performance der Aktie
        stockPerformanceRelative = [(stockPrices_3m[i]/stockPrices_3m[i-1]-1)*100 for i in range(1,len(stockPrices_3m))]
        # Performace des Index
        indexPerformanceRelative = [(indexPrices_3m[i]/indexPrices_3m[i-1]-1)*100 for i in range(1,len(indexPrices_3m))]

        # Vergleich der relativen Performance 
        # 0 --> Index ist besser, 1 --> Aktie ist besser
        performanceCompare = []
        for stock,index in zip(stockPerformanceRelative,indexPerformanceRelative):
            if stock < index:
                performanceCompare.append(0)
            else:
                performanceCompare.append(1)

        # Bewertung
        # Aktie immer besser -> +1, Index immer besser -> -1, sonst -> 0
        self.reversal_3m = self.REVERSAL_DEFAULT
        if (sum(performanceCompare) == 0):
            LevermannScore += 1
            self.reversal_3m = self.REVERSAL_NEGATIVE
        elif (sum(performanceCompare) == len(performanceCompare)):
            LevermannScore -= 1
            self.reversal_3m = self.REVERSAL_POSITIVE


        # Gewinnwachstum
        # Vergleich des Gewinnwachstums fuer das aktuelle Jahr mit dem fuer das naechste Jahr
        profitGrowthPrc = (EPS_est_next_year/EPS_est_this_year-1)*100
        self.profitGrowth = profitGrowthPrc/100
        if (profitGrowthPrc > 5):
            LevermannScore += 1
        elif (profitGrowthPrc < -5):
            LevermannScore -= 1

        # optional: Marktkapitalisierung
        #

        # optional: Branche
        # 

        self.Score = LevermannScore

        # Gesamt Bewertung:
        # Kaufen: Large Caps >= 4 Punkte; Small und Mid >= 7 Punkte
        # Halten: Large Caps >= 3 Punkte; Small und Mid >= 5-6 Punkte
        # Verkaufen: Large Caps >= 2 Punkte; Small und Mid >= 4 Punkte

        # Fazit/Kommentar
        # Unterscheidung zwischen Large Caps (> 5 Mrd.), Mid Caps (> 2 Mrd.) und Small Caps (< 2 Mrd.)
        marketCap = self.stock.keyStatistics[Stock.MARKET_CAP]
        # Large Cap
        if (marketCap > 5*10**9):
            if (LevermannScore >= 4):
                self.Comment = self.COMMENT_BUY
            elif (LevermannScore >= 3):
                self.Comment = self.COMMENT_HOLD
            else: 
                self.Comment = self.COMMENT_SELL
        # Mid Cap
        elif (marketCap > 2*10**9):
            if (LevermannScore >= 7):
                self.Comment = self.COMMENT_BUY
            elif (LevermannScore >= 5):
                self.Comment = self.COMMENT_HOLD
            else: 
                self.Comment = self.COMMENT_SELL
        # Small Cap
        else:
            if (LevermannScore >= 7):
                self.Comment = self.COMMENT_BUY
            elif (LevermannScore >= 6):
                self.Comment = self.COMMENT_HOLD
            else: 
                self.Comment = self.COMMENT_SELL


    def printScore(self):

        #print(self.stock.financialData)

        sepLineLength = 45

        print('-'*sepLineLength)
        print('    Levermann Score     ')
        print('-'*sepLineLength)
        
        if (self._ReturnOnEquity is not None):
            print('1. Eigenkapitalrendite LJ: {roe:.2f}%'.format(roe=self._ReturnOnEquity))
        else:
            print('1. Eigenkapitalrendite LJ: MISSING')

        if (self.EbitMarge is not None):
            print('2. EBIT-Marge LJ: {ebitm:.2f}%'.format(ebitm=self.EbitMarge))
        else:
            print('2. EBIT-Marge LJ: MISSING')

        if (self.EKratio is not None):
            print('3. Eigenkapitalquote LJ: {ekr:.2f}%'.format(ekr=self.EKratio))
        else:
            print('3. Eigenkapitalquote LJ: MISSING')

        if (self.KGV_5y is not None):
            print('4. KGV 5 Jahre: {kgv:.2f}'.format(kgv=self.KGV_5y))
        else:
            print('4. KGV 5 Jahre: MISSING')

        if (self.KGV_now is not None):
            print('5. KGV aktuell: {kgv:.2f}'.format(kgv=self.KGV_now))
        else:
            print('5. KGV aktuell: MISSING')

        if (self.recommendations is not None):
            print('6. Analystenmeinungen: {rec:.2f}'.format(rec=self.recommendations))
        else:
            print('6. Analystenmeinungen: MISSING')

        if (self.quarterlyReaction is not None):
            print('7. Reaktion auf Quartalszahlen: {reaction:.2f}%'.format(reaction=self.quarterlyReaction))
        else:
            print('7. Reaktion auf Quartalszahlen: MISSING')

        print('8. Gewinnrevision FEHLT NOCH')

        if (self.sharePriceRelative_6m is not None):
            print('9. Kurs heute gg. Kurs vor 6 Monaten: {spr:.2f}%'.format(spr=self.sharePriceRelative_6m))
        else:
            print('9. Kurs heute gg. Kurs vor 6 Monaten: MISSING')
            
        if (self.sharePriceRelative_1y is not None):
            print('10. Kurs heute gg. Kurs vor 1 Jahr: {spr:.2f}%'.format(spr=self.sharePriceRelative_1y))
        else:
            print('10. Kurs heute gg. Kurs vor 1 Jahr: MISSING')

        if (self.sharePriceMomentum is not None):
            print('11. Kursmomentum steigend: {mom}'.format(mom=self.sharePriceMomentum))
        else:
            print('11. Kursmomentum steigend: MISSING')

        if (self.reversal_3m is not None):
            print('12. Dreimonatsreversal: {rev}'.format(rev=self.reversal_3m))
        else:
            print('12. Dreimonatsreversal: MISSING')

        if (self.profitGrowth is not None):
            print('13. Gewinnwachstum: {pgrw:.2f}%'.format(pgrw=self.profitGrowth*100))
        else:
            print('13. Gewinnwachstum: MISSING')

        print('-'*sepLineLength)
        print('Levermann score: {ls} ({comment}) !unvollständig!'.format(ls=self.Score,comment=self.Comment))
        print('-'*sepLineLength + '\n')



def findNearestDate(date,datesList,dateFormat=Stock.DATE_FORMAT):
    """
        Gibt das Datum als String zurueck, das die geringste Differenz zum Datum
        im Argument datetime_object hat
        - datetime_object: Objekt der Klasse datetime.datetime
        - datesList: list mit allen Datums als Strings im Format des Arguments dateFormat
    """

    # Finden eines passenden Datums
    if isinstance(date,str):
        date_str = date
        datetime_object = datetime.datetime.strptime(date,dateFormat)
    elif isinstance(date,datetime.datetime):
        datetime_object = date
        date_str = date.strftime(dateFormat)
    else:
        raise ValueError('Argument of type ' + type(date) + ' is not supported.')

    if date_str in datesList:
        return date_str
    else:
        # 100 Versuche, um ein anderes Datum in der Naehe zu finden
        for i in range(1,100):
            newDate = datetime_object + relativedelta(days=1*i)
            newDate_str = newDate.strftime(dateFormat)
            if newDate_str in datesList:
                return newDate_str

            newDate_reverse = datetime_object + relativedelta(days=-1*i)
            newDate_reverse_str = newDate_reverse.strftime(dateFormat)
            if newDate_reverse_str in datesList:
                return newDate_reverse_str

    # Wenn nichts gefunden wurde, dann wird ein leerer String zurueckgegeben
    return ''


def linearRegression(x,y,plotResult=False):

    if not isinstance(x,np.ndarray):
        x_data = np.array(x).reshape((-1, 1))
    else:
        x_data = x

    if not isinstance(y,np.ndarray):
        y_data = np.array(y)
    else:
        y_data = y

    # Fit the model
    model = LinearRegression(fit_intercept=True,copy_X=True).fit(x_data, y_data)

    if plotResult:
        r_sq = model.score(x_data, y_data)
        print('coefficient of determination:', r_sq)

        print('intercept:', model.intercept_)
        print('slope:', model.coef_)

        # create a plot
        fig, ax = plt.subplots()
        ax.plot(x_data,y_data, linestyle = 'None', marker='o', label='Data')
        ax.plot(x_data,model.predict(x_data), label='Linear Regression')
        ax.legend(loc='upper left')
        fig.tight_layout()
        plt.show()

    return model