
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
from utils.plot import createPlot

# ---------- CLASSES ----------
class StockAnalyzer():

    # value shared across all class instances

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

        # variables for anayzing the stock
        # EPS
        self.meanWeightedEps = None
        self.calcWeightedEps()

        self._GrahamNumber = None
        self._Recommendations = None
        self._LevermannScore = None

        #
        self._NetMargin = None
        self._ReturnOnEquity = None
        self._ReturnOnAssets = None
        self._FreeCashFlowBySales = None
        self._PriceToSales = None
        self._PriceToEarnings = None
        self._PresentShareValue = None

        self.dividendYield = 0

        a = self.stock.financialStatements
        print(a)

        # analyze the stock
        self.analyzeStock()

        
    def analyzeStock(self):
        self.calcGrahamNumber()
        self.calcDCF()
        self.calcReturnOnEquity()
        self.calcReturnOnAssets()
        self.calcFreeCashFlowBySales()


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

    @property
    def LevermannScore(self):
        if self._LevermannScore is None:
            self.calcLevermannScore()
        return self._LevermannScore

    @property
    def Recommendations(self):
        if self._Recommendations is None:
            self._Recommendations = self.getLatestRecommendations()
        return self._Recommendations

    @property
    def PresentShareValue(self):
        if self._PresentShareValue is None:
            self.calcDCF()
        return self._PresentShareValue

    """
        Berechnung der Graham Number
    """
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

    """
        Check if all necessary assumptions for DCF is available
    """
    def isAssumptionsCompleteForDCF(self):
        return (self.stock.assumptions is not None) and \
            ('discountRate' in self.stock.assumptions.keys()) and \
            ('margin_of_safety' in self.stock.assumptions.keys()) and \
            ('growth_year_1_to_5' in self.stock.assumptions.keys()) and\
            ('growth_year_6_to_10' in self.stock.assumptions.keys()) and\
            ('growth_year_10ff' in self.stock.assumptions.keys())


    """
        Discounted Cash Flow Verfahren
    """
    def calcDCF(self,detailed=True,generatePlot=False):
        # check if all needed assumptions data is available
        if self.isAssumptionsCompleteForDCF():
            # Free Chashflow der letzten Jahre
            CF = self.stock.financialStatements.loc['freeCashFlow',:].copy()

            CF.fillna(CF.mean(), inplace=True) # TODO: NaN Werte werden durch Mittelwert ersetzt

            # Sortierung in aufsteigender Reihenfolge (alt -> neu)
            CF_sorted = []
            years = []
            for date in sorted(CF.index.values.copy()):
                CF_sorted.append(CF.loc[date])
                years.append(int(date[0:4]))

            # Berechnung 
            model = linearRegression(range(len(CF_sorted)),CF_sorted,plotResult=False)
            todaysCashFlow_regression = model.predict(np.array([len(CF_sorted)-1]).reshape(1, -1))[0]
            todaysCashFlow_thisYear = CF_sorted[-1]
            FCFstartValue = (todaysCashFlow_regression+todaysCashFlow_thisYear)/2
            if detailed:
                print('DCF start value is the mean value of last years value and the regression value: {v:.2f} Mrd. {c}'.format(v=FCFstartValue/10**9,c=self.stock.currencySymbol))
                print('-'*54)
                print('  year | Free Cash Flow | discounted free cash flow')
                print(' ' + '-'*52 + ' ')
            
            # Wachstumsrate der naechsten 10 Jahre
            discountRate = self.stock.assumptions["discountRate"]/100

            # Free Cash Flow der naechsten 5 Jahre
            growthRate = self.stock.assumptions['growth_year_1_to_5']/100
            discountedCashFlow = []
            FCF, year = [], []
            for i in range(1,6):
                FCF.append((FCFstartValue*(1+growthRate)**i))
                discountedCashFlow.append(FCF[-1] / ((1 + discountRate)**i))
                year.append(years[-1]+i)
                if detailed:
                    print('    {y:2.0f} | {fcf:6.2f} Mrd.    | {dfcf:6.2f} Mrd.'.format(y=i,fcf=FCF[-1]/10**9,dfcf=discountedCashFlow[-1]/10**9))

            # Free Cash Flow der Jahre 6-10
            growthRate = self.stock.assumptions['growth_year_6_to_10']/100
            for i in range(6,11):
                FCF.append((FCF[4]*(1+growthRate)**(i-5)))
                discountedCashFlow.append(FCF[-1] / ((1 + discountRate)**i))
                year.append(years[-1]+i)
                if detailed:
                    print('    {y:2.0f} | {fcf:6.2f} Mrd.    | {dfcf:6.2f} Mrd.'.format(y=i,fcf=FCF[-1]/10**9,dfcf=discountedCashFlow[-1]/10**9))

            # Free Cash Flow insgesamt ab dem 11. Jahr (perpetuity value) im heutigen Wert (discounted perpetuity value)
            # - FCF_10: Free Cash Flow in 10 Jahren
            # - growthRate_10: Wachstum des Free Cash Flows nach dem 10. Jahr
            # Formel: FCF_10 * (1 + growthRate_10) / ((discountRate - growthRate_10) * (1 + discountRate))
            growthRate = self.stock.assumptions['growth_year_10ff']/100
            # perpetuity value
            FCF.append((FCF[-1] * (1 + growthRate)) / (discountRate - growthRate))
            # discounted perpetuity value
            discountedCashFlow.append(FCF[-1] / ((1 + discountRate)**10))

            if detailed:
                print('   inf | {fcf:6.2f} Mrd.    | {dfcf:6.2f} Mrd.'.format(y=i,fcf=FCF[-1]/10**9,dfcf=discountedCashFlow[-1]/10**9))
                print(' ' + '-'*52 + ' ')

            # Summe der, auf den aktuellen Zeitpunkt bezogenen, zukuenfitgen Cashflows
            totalEquityValue = sum(discountedCashFlow)

            # Wert einer Aktie zum aktuellen Zeitpunkt auf Grundlage aller zkünftigen Free Cash Flows
            # Beruecksichtigung einer Margin of safety
            marginOfSafety = self.stock.assumptions["margin_of_safety"]/100
            sharesOutstanding = self.stock.keyStatistics[Stock.SHARES_OUTSTANDING]
            perShareValue = totalEquityValue/sharesOutstanding/(1 + marginOfSafety)

            if detailed:
                print('                          {v:7.2f} Mrd.'.format(v=totalEquityValue/10**9))
                print(' shares outstanding:      {v:7.0f} Mio.'.format(v=sharesOutstanding/10**6))
                print(' ' + '-'*52 + ' ')
                print(' present value per share: {v:7.2f}'.format(v=perShareValue))
                print('-'*54 + '\n')

            self._PresentShareValue = perShareValue

            if generatePlot:
                createPlot([years,years[-1],year],[CF_sorted,FCFstartValue,FCF[:-1]],legend_list=['historical free cash flows','start value for DCF method','estimated free cash flows'])
        else:
            print(' +++ Discounted Cash Flow Analysis failed due to missing data +++ ')


    """
        Berechnung des Levermann Scores
    """
    def calcLevermannScore(self):
        if (self.stockIndex is not None):
            self._LevermannScore = LevermannScore(self.stock,self.stockIndex)
        else:
            print('Zur Berechnung des Levermann Scores muss ein Index angegeben werden')

    
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
    

    def calcWeightedEps(self):

        epsKey = 'dilutedEPS'
        
        if (self.stock.financialStatements is not None) and (epsKey in self.stock.financialStatements.index.values):
            # get historical EPS data
            epsHistory = self.stock.financialStatements.loc[epsKey,:].copy()

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
        else:
            self.meanWeightedEps = self.stock.getBasicDataItem(Stock.EARNINGS_PER_SHARE)


    def loadRecommendations(self):
        self._Recommendations = FinnhubClient(self.stock.symbol).getRecommendationsDataFrame()


    def getLatestRecommendations(self):
        latestRecommendations = self.Recommendations.iloc[0,:]
        latest = latestRecommendations[['strongBuy','buy','hold','sell','strongSell']]
        return latest


    """
        Berechnung des Nettogewinns
    """
    def calcNetMargin(self):
        if self.stock.financialStatements is None:
            raise Exception('The stock has no historical financial data. "Total Revenue" and "Net Income" needed!')
        else:
            # Nettogewinn
            netIncome = self.stock.financialStatements.loc['Net Income',:].copy()
            # Umsatz
            revenues = self.stock.financialStatements.loc['Total Revenue',:].copy()

            dic = {}
            for index in sorted(netIncome.index, reverse=True):
                dic[index] = netIncome.loc[index]/revenues.loc[index]

            df = pd.Series(dic, index=dic.keys())
            df.reindex(sorted(df.index, reverse=True))
            self._NetMargin = df

            return df


    def calcReturnOnEquity(self):
        if self.stock.financialStatements is None:
            raise Exception('The stock has no historical financial data. "Total Stockholder Equity" and "Net Income" needed!')
        else:
            # Eigenkapital
            equity = self.stock.financialStatements.loc['Total Stockholder Equity',:].copy()
            # Betriebseinkommen
            income = self.stock.financialStatements.loc['Net Income',:].copy()

            # Berechnung der Eigenkapitalrendite fuer jedes Jahr
            dic = {}
            for index in sorted(equity.index, reverse=True):
                # ignore NAN-values
                if (not np.isnan(income[index])) and (not np.isnan(equity[index])):
                    dic[index] = income[index]/equity[index]

            df = pd.Series(dic, index=dic.keys())
            self._ReturnOnEquity = df

            return df

    def calcReturnOnAssets(self):
        if self.stock.financialStatements is None:
            raise Exception('The stock has no historical financial data. "Total Assets" and "Net Income" needed!')
        else:
            # Gesamtvermögen
            totalAssets = self.stock.financialStatements.loc['Total Assets',:].copy()
            # Betriebseinkommen
            income = self.stock.financialStatements.loc['Net Income',:].copy()

            # Berechnung der Kapitalrendite fuer jedes Jahr
            dic = {}
            for index in sorted(totalAssets.index,reverse=True):
                dic[index] = income[index]/totalAssets[index]

            df = pd.Series(dic, index=dic.keys())
            self._ReturnOnAssets = df

            return df


    def calcFreeCashFlowBySales(self):
        if self.stock.financialStatements is None:
            raise Exception('The stock has no historical financial data. "Total Revenue" and "freeCashFlow" needed!')
        else:
            # Umsatz
            revenues = self.stock.financialStatements.loc['Total Revenue',:].copy()
            # Free Cash Flow
            freeCashFlow = self.stock.financialStatements.loc['freeCashFlow',:].copy()
            
            # Berechnung des Free cash flows bezogen auf die Einnahmen fuer jedes Jahr
            dic = {}
            for index in sorted(revenues.index, reverse=True):
                dic[index] = freeCashFlow[index]/revenues[index]

            df = pd.Series(dic, index=dic.keys())
            self._FreeCashFlowBySales = df

            return df


    def calcPriceToSales(self):
        if self.stock.financialStatements is None:
            raise Exception('The stock has no historical financial data. "Total Revenue" and "Total Stockholder Equity" needed!')
        else:
            # Umsatz
            revenues = self.stock.financialStatements.loc['Total Revenue',:].copy()
            # Marktkapitalisierung
            totalStockHolderEquity = self.stock.financialStatements.loc['Total Stockholder Equity',:].copy() 

            # Price to Sales fuer jedes Jahr
            P_S = pd.Series()
            for date in list(revenues.index.values.copy()):
                # Price/Sales
                price = totalStockHolderEquity.loc[date]
                sales = revenues.loc[date]
                P_S.loc[date] = price/sales

            self._PriceToSales


    def calcGrowth(self,valueList,percentage=False):
        if percentage:
            factor = 100
        else: 
            factor = 1
        return [(valueList[i]-valueList[i-1])/valueList[i-1]*factor for i in range(1,len(valueList))]


    def printBasicAnalysis(self):

        # variables for formatting the console output
        stringFormat = "35s"
        dispLineLength = 55
        sepString = '-'*dispLineLength + '\n'

        # format margin around stock name
        stockName = self.stock.company.longName
        stockNameOutput = stockName
        if (len(stockName) < dispLineLength):
            margin = int((dispLineLength-len(stockName))/2)
            stockNameOutput = ' '*margin + stockName + ' '*margin

        # string to print the graham number
        strGrahamNumber = '{str:{strFormat}}{gn:6.2f}'.format(str='Graham number:',gn=self.GrahamNumber,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

        # string to print the stock's current value
        strCurrentStockValue = ''
        stockPrice = self.stock.getBasicDataItem(Stock.MARKET_PRICE)
        if (stockPrice is not None):
            strCurrentStockValue = '{str:{strFormat}}{val:6.2f}'.format(str="Current share price:",val=stockPrice,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

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


        """
            Marktkapitalisierung
        """
        strMarketCapComment = ''
        # Wenn die Marktkapitalisierung geringer als 500Mio ist, dann wird eine Warnung ausgegeben
        if self.stock.keyStatistics[Stock.MARKET_CAP] < 500*10**6:
            strMarketCapComment = '!ACHTUNG: kleines Unternehmen!'
            strSize = 'Mio.'
            marketCap = self.stock.keyStatistics[Stock.MARKET_CAP]/10**6
        if self.stock.keyStatistics[Stock.MARKET_CAP] > 10**9:
            strSize = 'Mrd.'
            marketCap = self.stock.keyStatistics[Stock.MARKET_CAP]/10**9
        # String fuer die Ausgabe
        strMarketCap = '{str:{strFormat}}{val:6.2f}'.format(str="Market capitalization: ",val=marketCap,strFormat=stringFormat) + \
            ' ' + strSize + ' ' + self.stock.currencySymbol + ' ' + strMarketCapComment +'\n'

        """
            Operating Income (Pruefung, ob die Firma jemals Geld verdient hat)
        """
        operatingIncome = self.stock.financialStatements.loc['Operating Income'].copy()
        opIncList, opIncSize = [], 'Mrd.'
        strYear, strValue = ' '*6 + '|', ' '*6 + '|'
        for date in list(sorted(operatingIncome.index.values.copy())):
            value = operatingIncome.loc[date]/10**9 # in Mrd 
            opIncList.append(value)
            strYear = strYear   + '  {year}  |'.format(year=date[:4])
            strValue = strValue + ' {v:6.2f} |'.format(v=value)

        # Waehrung
        strValue = strValue + ' ' + opIncSize + ' ' + self.stock.currencySymbol

        # mittleres Wachstum
        operatingIncomeGrowth = self.calcGrowth(opIncList,percentage=True)
        avgOperatingIncomeGrowth = sum(operatingIncomeGrowth)/len(operatingIncomeGrowth)
        # String fuer die Ausgabe
        strOperatingIncome = '{str:{strFormat}}{val:6.2f}'.format(str="Operating Income Growth: ",val=avgOperatingIncomeGrowth,strFormat=stringFormat) + \
            '%\n' + strYear + '\n' + strValue + '\n'

        """
            Cash flow from operating activities
        """
        totalCashFlowFromOperations = self.stock.financialStatements.loc['Total Cash From Operating Activities'].copy()

        cashFromOpActList = []
        strYear, strValue = ' '*6 + '|', ' '*6 + '|'
        for date in list(sorted(totalCashFlowFromOperations.index.values.copy())):
            value = totalCashFlowFromOperations.loc[date]/10**9 # in Mrd 
            cashFromOpActList.append(value)
            strYear = strYear   + '  {year}  |'.format(year=date[:4])
            strValue = strValue + ' {v:6.2f} |'.format(v=value)

        # Waehrung
        strValue = strValue + ' ' + opIncSize + ' ' + self.stock.currencySymbol

        # Mittleres Wachstum
        cashFromOpActGrowth = self.calcGrowth(cashFromOpActList,percentage=True)
        avgCashFromOpActGrowth = sum(cashFromOpActGrowth)/len(cashFromOpActGrowth)
        # String fuer die Ausgabe
        strCashFlowFromOperatingActivities = '{str:{strFormat}}{val:6.2f}'.format(str="Cash flow from operating activities growth: ",val=avgCashFromOpActGrowth,strFormat=stringFormat) + \
            '% \n' + strYear + '\n' + strValue + '\n'

        """
            ROE - Return on Equity - Eigenkapitalrenidte
            ROA - Return on Assets
            Financial Leverage
        """
        equity = self.stock.financialStatements.loc["Total Stockholder Equity"].copy()
        assets = self.stock.financialStatements.loc["Total Assets"].copy()

        leverageList = []
        strYear, strROE, strROA, strLeverage = ' '*6 + '|', '- ROE |', '- ROA |', '- LEV |'
        for date in list(sorted(self.ReturnOnEquity.index.values.copy())):
            strYear = strYear   + '  {year}  |'.format(year=date[:4])
            strROE = strROE + ' {v:6.2f} |'.format(v=self.ReturnOnEquity.loc[date]*100) # in Prozent
            strROA = strROA + ' {v:6.2f} |'.format(v=self.ReturnOnAssets.loc[date]*100) # in Prozent
            leverageList.append(assets.loc[date]/equity.loc[date])
            strLeverage = strLeverage + ' {v:6.2f} |'.format(v=leverageList[-1])

        # Einheit
        strROE = strROE + ' %'
        strROA = strROA + ' %'

        # Beurteilung ROE
        avgROE = sum(self.ReturnOnEquity)/len(self.ReturnOnEquity)*100 # Mittelwert in Prozent
        if avgROE >= 15:
            strRoeComment = '      mittleres ROE > 15% --> sehr gut'
        elif avgROE >= 10:
            strRoeComment = '      mittleres ROE > 10% --> gut'
        else:
            strRoeComment = '      mittleres ROE < 10% --> ACHTUNG!'

        # Beurteilung ROA
        avgROA = sum(self.ReturnOnAssets)/len(self.ReturnOnAssets)*100 # Mittelwert in Prozent
        if avgROA > 1.2:
            strRoaComment = '      ROA > 1.2% --> gut'
        elif avgROA > 1.0:
            strRoaComment = '      ROA > 1.0% --> in Ordnung'
        elif avgROA < 0.7:
            strRoaComment = '      ROA < 0.7% --> Pruefen, warum so gering!'
        else:
            strRoaComment = '      ROA sollte noch etwas besser sein'

        # Beurteilung der Leverage
        model = linearRegression(range(len(leverageList)),leverageList)
        # Mittelwert
        avgLeverage = sum(leverageList)/len(leverageList)
        if 'Banks' in self.stock.company.industry:
            if avgLeverage > 13:
                strLeverageComment = ' '*6 + 'hohe Leverage (> 13) --> ACHTUNG!'
            elif (avgLeverage < 9):
                strLeverageComment = ' '*6 + 'recht geringe Leverage für Banken (< 9) --> PRUEFEN!'
            else:
                strLeverageComment = ' '*6 + 'Leverage ok'
        else:
            if (avgLeverage > 3.5):
                strLeverageComment = ' '*6 + 'hohe Leverage (> 3.5) --> ACHTUNG!'
            elif (avgLeverage > 2.5) and (model.coef_/avgLeverage > 0.2):
                strLeverageComment = ' '*6 + 'Leverage steigt schnell an --> ACHTUNG!'
            else:
                strLeverageComment = ' '*6 + 'Leverage ok'

        # String fuer die Ausgabe
        strReturnOnEquity = '{str:{strFormat}}{val:6.2f}'.format(str="Return on Equity: ",val=avgROE,strFormat=stringFormat) + \
            '% \n' + strYear + '\n' + strROE + '\n' + strROA + '\n' + strLeverage + '\n' + strRoeComment + '\n' + strRoaComment + '\n' + strLeverageComment + '\n'


        """
            Earnings Growth - Gewinnwachstum
        """
        earnings = self.stock.financialStatements.loc['Net Income'].copy()

        earningsList = []
        strYear, strEarnings = ' '*6 + '|', ' '*6 + '|'
        for date in list(sorted(earnings.index.values.copy())):
            earningsList.append(earnings.loc[date])
            strYear = strYear   + '  {year}  |'.format(year=date[:4])
            strEarnings = strEarnings + ' {v:6.2f} |'.format(v=earnings.loc[date]/10**9)

        # Waehrung
        strEarnings = strEarnings + ' Mrd. ' + self.stock.currencySymbol

        earningsGrowth = self.calcGrowth(earningsList,percentage=True)
        avgEarningsGrowth = sum(earningsGrowth)/len(earningsGrowth)
        # String fuer die Ausgabe
        strEarningsGrwoth = '{str:{strFormat}}{val:6.2f}'.format(str="Earnings Growth: ",val=avgEarningsGrowth,strFormat=stringFormat) + \
            '% \n' + strYear + '\n' + strEarnings + '\n'

        """
            Debt
        """

        """
            Free Cash Flow / Sales
        """
        freeCashFlow = self.stock.financialStatements.loc['freeCashFlow'].copy()
        sales = self.stock.financialStatements.loc['Total Revenue'].copy()

        freeCashFlowToSales = []
        strYear, strValue = ' '*6 + '|', ' '*6 + '|'
        for date in list(sorted(freeCashFlow.index.values.copy())):
            freeCashFlowToSales.append(freeCashFlow.loc[date]/sales.loc[date]*100) # in Prozent
            strYear = strYear   + '  {year}  |'.format(year=date[:4])
            strValue = strValue + ' {v:6.2f} |'.format(v=freeCashFlowToSales[-1])

        # Einheit
        strValue = strValue + ' %'

        # Mittelwert und Bewertung
        avgFreeCashFlowPerSales = sum(freeCashFlowToSales)/len(freeCashFlowToSales)
        if avgFreeCashFlowPerSales >= 10:
            strFCF_Sales_comment = ' '*6 + '--> sehr gut'
        if avgFreeCashFlowPerSales >= 5:
            strFCF_Sales_comment = ' '*6 + '--> gut'
        else:
            strFCF_Sales_comment = ' '*6 + '-> Prüfen, ob das Unternehmen stark wächst!'

        # String fuer die Ausgabe
        strFreeCashFlowPerSales = '{str:{strFormat}}'.format(str="Free Cash Flow / Sales: ",strFormat=stringFormat) + \
            '\n' + strYear + '\n' + strValue + ' \n' + strFCF_Sales_comment + '\n'

        
        """
            Number of shares
        """
        averageShares = self.stock.financialStatements.loc['dilutedAverageShares'].copy()

        avgSharesList = []
        strYear, strValue = ' '*6 + '|', ' '*6 + '|'
        for date in list(sorted(averageShares.index.values.copy())):
            # ignore NAN values
            if not np.isnan(averageShares.loc[date]):
                avgSharesList.append(averageShares.loc[date]/10**6) # in Millionen
                strYear = strYear   + '  {year}  |'.format(year=date[:4])
                strValue = strValue + ' {v:5.0f}  |'.format(v=avgSharesList[-1])

        # Mittelwert und Bewertung
        averageSharesGrowth = self.calcGrowth(avgSharesList,percentage=True)
        avgAverageSharesGrowth = sum(averageSharesGrowth)/len(averageSharesGrowth)
        if avgAverageSharesGrowth < 0:
            strAverageShares = ' '*6 + 'Aktienrückkäufe --> könnte gut sein'
        elif (avgAverageSharesGrowth > 0) and (avgAverageSharesGrowth < 1.5):
            strAverageShares = ' '*6 + 'Anzahl der Aktien steigt um jährlich ca. {v:.1f}%'.format(v=avgAverageSharesGrowth)
        elif avgAverageSharesGrowth > 2:
            strAverageShares = ' '*6 + 'ACHTUNG: Die Anzahl der Aktien steigt sehr stark! Jährlich ca. {v:.1f}%'.format(v=avgAverageSharesGrowth)
        elif np.isnan(avgAverageSharesGrowth):
            nonNanValues = [asg for asg in averageSharesGrowth if not np.isnan(asg)]
            avgGrowth = sum(nonNanValues)/len(nonNanValues)
            strAverageShares = ' '*6 + '+++ Es fehlende Werte +++.\n' + ' '*6 + 'jährlicher Anstieg: ca. {v:.1f}%'.format(v=avgGrowth)
        else:
            strAverageShares = '+++Bitte ersetze diesen Text+++'

        strNumberOfShares = '{str:{strFormat}}'.format(str="Number of Shares (Mio.): ",strFormat=stringFormat) + \
            '\n' + strYear + '\n' + strValue + ' \n' + strAverageShares + '\n'


        """
            Free Cash Flow
        """
        freeCashFlow = self.stock.financialStatements.loc['freeCashFlow'].copy()

        strYear, strValue = ' '*6 + '|', ' '*6 + '|'
        for date in list(sorted(freeCashFlow.index.values.copy())):
            strYear = strYear   + '  {year}  |'.format(year=date[:4])
            strValue = strValue + ' {v:6.2f} |'.format(v=freeCashFlow.loc[date]/10**9) # in Mrd

        # Einheit
        strValue = strValue + ' Mrd. ' + self.stock.currencySymbol 

        # String fuer die Ausgabe
        strFreeCashFlow = '{str:{strFormat}}'.format(str="Free Cash Flow: ",strFormat=stringFormat) + \
            '\n' + strYear + '\n' + strValue + ' \n'

        """
            Discounted Cash Flow
        """
        freeCashFlow = self.stock.financialStatements.loc['freeCashFlow'].copy()
        freeCashFlowList = [freeCashFlow[date] for date in list(sorted(freeCashFlow.index.values.copy()))]
        freeCashFlowGrowth = self.calcGrowth(freeCashFlowList,percentage=True)
        avgFreeCashFlowGrowth = sum(freeCashFlowGrowth)/len(freeCashFlowGrowth)

        if self.isAssumptionsCompleteForDCF():
            strDiscountedCashFlow = 'Discounted Cash Flow (DCF)\n' + \
                ' - margin of safety: {v:.1f}%'.format(v=self.stock.assumptions["margin_of_safety"]) + '\n' + \
                ' - discount rate:    {v:.1f}%'.format(v=self.stock.assumptions["discountRate"]) + '\n' + \
                ' - expected cash flow growth: \n' + \
                '   - year 1-5:   {v:.1f}%'.format(v=self.stock.assumptions["growth_year_1_to_5"]) + '\n' + \
                '   - year 6-10:  {v:.1f}%'.format(v=self.stock.assumptions["growth_year_6_to_10"]) + '\n' + \
                '   - afterwards: {v:.1f}%'.format(v=self.stock.assumptions["growth_year_10ff"]) + '\n' + \
                '   (previous average cash flow growth: {v:.1f}%)'.format(v=avgFreeCashFlowGrowth) + '\n' + \
                '\n' + \
                '{str:{strFormat}}{val:6.2f}'.format(str="Present Share Value: ",val=self.PresentShareValue,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'
        else:
            strDiscountedCashFlow = 'Discounted Cash Flow (DCF)\n' + ' +++ Can\'t be calculated due to missing data +++\n' + \
                '   (previous average cash flow growth: {v:.1f}%)'.format(v=avgFreeCashFlowGrowth) + '\n'

        # Combine all fragments to a string
        string2Print = sepString + \
            stockNameOutput + '\n' + \
            sepString + \
            strMarketCap + \
            sepString + \
            strOperatingIncome + \
            sepString + \
            strCashFlowFromOperatingActivities + \
            sepString + \
            strReturnOnEquity + \
            sepString + \
            strEarningsGrwoth + \
            sepString + \
            strFreeCashFlowPerSales + \
            sepString + \
            strNumberOfShares + \
            sepString + \
            strFreeCashFlow + \
            sepString + \
            strDiscountedCashFlow + \
            sepString + \
            strCurrentStockValue + \
            sepString
            
        # print to the console
        print(string2Print)


    def printDetailedAnalysis(self):
        pass



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
        #print(self.stock.financialStatements)

        # RoE (Return on Equity) Eigenkapitalrendite (Gewinn / Eigenkapital)
        # Eigenkapital
        equity = list(self.stock.financialStatements.loc['Total Stockholder Equity',:].copy())
        # TODO Klärung ob "Net Income" (abzgl. Steuern etc.) oder "Operating Income" (Steuern noch nicht abgezogen)
        # laut dem Wert auf "https://aktien.guide/levermann-strategie/Microsoft-US5949181045" muss der Eintrag aus "Operating Income" genutzt werden
        # da sonst ein zu niedriger Prozentwert entsteht
        Gewinn = list(self.stock.financialStatements.loc['Operating Income',:].copy())

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
        EBIT = list(self.stock.financialStatements.loc['Ebit',:].copy())
        if 0 in EBIT:
            print('\n +++ EBIT enthält mindestens einen Eintrag mit 0 +++')
            print(self.stock.financialStatements.loc['Ebit',:])
            print(self.stock.financialStatements)
            print('\n')

        # Umsatz
        totalSales = list(self.stock.financialStatements.loc['Total Revenue',:].copy())

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
        GK = list(self.stock.financialStatements.loc['Total Assets',:].copy())

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
        EPSdf = self.stock.financialStatements.loc['dilutedEPS',:].copy()
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

        #print(self.stock.financialStatements)

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