
# ---------- MODULES ----------
# standard modules
import numpy as np
from sklearn.linear_model import LinearRegression 

# custom modules
from classes.Stock import Stock
from classes.FinnhubAPI import FinnhubClient

# ---------- CLASSES ----------
class StockAnalyzer():

    # value shared across all class instances
    #
    # margin of safety: 20% --> 0.20
    marginOfSafety = 0.2
    # expected return (exprectedReturn): 15% --> 0.15
    expectedReturn = 0.15
    # investment time: 10 years
    investmentHorizon = 10

    #
    useWeightedHistoricalData = False
    weightingStep = 1
    
    def __init__(self,stock):
        if not isinstance(stock,Stock):
            raise TypeError('Object ' + str(stock) + ' is no instance of class Stock')
        
        self.stock = stock

        # variables for anayzing the stock
        # EPS
        self.meanWeightedEps = None
        self.epsWeightYears = None
        self.calcWeightedEps()

        # P/E (Price Earnings Ratio)
        self.priceEarningsRatio = None
        self.getPriceEarningsRatio()

        self.GrahamNumber = None
        self.fairValue = None
        self.recommendations = None

        self.dividendYield = 0

        # analyze the stock
        self.analyzeStock()

    
    def analyzeStock(self):
        self.getFairValue()
        self.calcGrahamNumber()
        self.calcNPV()
        self.recommendations = self.getRecommendations()


    def getGrahamNumber(self):
        if self.GrahamNumber is None:
            self.calcGrahamNumber()

        return self.GrahamNumber


    def calcGrahamNumber(self):
        if (self.meanWeightedEps is not None) and (self.stock.isItemInBasicData(Stock.BOOK_VALUE_PER_SHARE)):

            if (self.meanWeightedEps < 0):
                print(' +++ avg. weighted EPS < 0! Stock: ' + self.stock.symbol + ' (' + self.stock.name + ') +++')
                self.meanWeightedEps = 0
            if (self.stock.getBasicDataItem(Stock.BOOK_VALUE_PER_SHARE) < 0):
                print(' +++ book value per share < 0! Stock: ' + self.stock.symbol + ' (' + self.stock.name + ') +++')
                
            self.GrahamNumber = np.sqrt(15 * self.meanWeightedEps * 1.5 * self.stock.getBasicDataItem(Stock.BOOK_VALUE_PER_SHARE))
        else:
            self.GrahamNumber = 0

    def calcNPV(self):
        CF = self.stock.financialData.loc['freeCashFlow',:]
        CF.fillna(CF.mean(), inplace=True) # TODO: NaN Werte werden durch Mittelwert ersetzt
        CF_y = np.array(CF.values)
        CF_x = np.array(range(CF.size))
        CF_x = CF_x.reshape(-1, 1)
        model = LinearRegression()
        model.fit(CF_x, CF_y)
        growth = model.coef_ / CF_y[-1] *100 # cashflow growth in percent
        i = 10 # discount in percent
        PV = 0
        for index in range(self.investmentHorizon):
            CF_t = CF_y[-1]*pow(1+growth/100,index)
            product = pow(1+i/100,index+1)
            PV_t = CF_t / product
            PV += PV_t
        self.NPV = (PV - self.stock.keyStatistics["marketCap"])/self.stock.keyStatistics["sharesOutstanding"]

    # Funktion zur Berechnung des sog. "inneren Wertes" der Aktie
    def getFairValue(self):
        if self.fairValue is None:

            if self.stock.growthRateAnnualy is None:
                raise ValueError('The expected annualy growth rate for ' + self.stock.symbol + ' (' + self.stock.name + ') is of type None')
            if not self.stock.isItemInBasicData(Stock.PE_RATIO):
                raise KeyError('The P/E for ' + self.stock.name + ' is not existant')
            

            # calclate the new growth rate, as the dividend yield gets added
            growthRateAnnualy = self.stock.growthRateAnnualy# + self.dividendYield
            if growthRateAnnualy != self.stock.growthRateAnnualy:
                print("growthRateAnnualy: " + str(self.stock.growthRateAnnualy))
                print("The annualy growth rate gets increased by the dividend yield of {divYield:5.2f}%. New annualy growth rate: {grwRate:5.2f}".format(divYield=self.dividendYield,grwRate=growthRateAnnualy))

            self.fairValue = calcFairValue(self.meanWeightedEps,growthRateAnnualy,self.stock.getBasicDataItem(Stock.PE_RATIO),StockAnalyzer.expectedReturn,StockAnalyzer.marginOfSafety,StockAnalyzer.investmentHorizon)

        return self.fairValue

    def getMeanWeightedEPS(self):
        if (self.meanWeightedEps is None) or (self.epsWeightYears is None):
            self.calcWeightedEps()

        return self.meanWeightedEps, self.epsWeightYears

    def calcWeightedEps(self):

        epsKey = 'dilutedEPS'
        
        if (self.stock.financialData is not None) and (epsKey in self.stock.financialData.index.values):
            # get historical EPS data
            epsHistory = self.stock.financialData.loc[epsKey,:]

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


    def printAnalysis(self):

        if self.priceEarningsRatio is None:
            self.getPriceEarningsRatio()

        # variables for formatting the console output
        stringFormat = "24s"
        dispLineLength = 40
        sepString = '-'*dispLineLength + '\n'

        #
        if self.fairValue is None:
            self.getFairValue()

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
        strGrahamNumber = ''
        if self.GrahamNumber is not None:
            strGrahamNumber = '{str:{strFormat}}{gn:6.2f}'.format(str='Graham number:',gn=self.GrahamNumber,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

        strNetPresentValue = ''
        if self.NPV is not None:
            strNetPresentValue = '{str:{strFormat}}{gn:6.2f}'.format(str='NetPresentValue:',gn=self.NPV[0],strFormat=stringFormat) + \
            ' ' + self.stock.currencySymbol + ' (positiv:good)\n'

        # string to print the stock's current value
        strCurrentStockValue = ''
        stockPrice = self.stock.getBasicDataItem(Stock.MARKET_PRICE)
        if (stockPrice is not None):
            strCurrentStockValue = '{str:{strFormat}}{val:6.2f}'.format(str="current value:",val=stockPrice,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'


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
            ' - margin of safety: {marginOfSafety:2.0f}%\n'.format(marginOfSafety=StockAnalyzer.marginOfSafety*100) + \
            ' - exp. growth rate: {expGrwRate:2.0f}%\n'.format(expGrwRate=StockAnalyzer.expectedReturn*100) + \
            '\n' + \
            '{str:{strFormat}}{val:6.2f}'.format(str="Fair value:",val=self.fairValue,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n' + \
            strGrahamNumber + \
            strNetPresentValue + \
            strCurrentStockValue + \
            sepString + '\n'

        # print to the console
        print(string2Print)


DEBUG = False

# ---------- FUNCTIONS ----------
#
def calcFairValue(earningsPerShare,growthRateAnnualy,priceEarningsRatio,expectedReturn,marginOfSafety,investmentHorizon=10):
    """
        Berechnung des "Inneren Wertes" (oft auch als "Fairer Wert" bezeichnet)
        Berechnungsgrundpagen:
        - angegebene growthRateAnnualy gilt fuer die naechsten Jahre
    """

    if DEBUG:
        print('Argumente fuer die Funktion calcFairValue()')
        print('earningsPerShare:   ' + str(earningsPerShare))
        print('growthRateAnnualy:  ' + str(growthRateAnnualy))
        print('priceEarningsRatio: ' + str(priceEarningsRatio))
        print('expectedReturn:     ' + str(expectedReturn))
        print('marginOfSafety:     ' + str(marginOfSafety))
        print('investmentHorizon:  ' + str(investmentHorizon))

    # Berechnung des Gewinns pro Aktie in der Zukunft
    futureEarningsPerShare = earningsPerShare*((1+growthRateAnnualy)**StockAnalyzer.investmentHorizon)

    # Berechnung des zukuenfiten Aktienpreises auf Grundlage des aktuellen Kurs-Gewinn-Verhaeltnisses
    futureStockValue = futureEarningsPerShare*priceEarningsRatio

    # Berechnung des fairen/inneren Preises zum aktuellen Zeitpunkt auf Grundlage der Renditeerwartung
    fairValue = futureStockValue/((1+(expectedReturn/100))**investmentHorizon)
    
    # Berechnung des fairen Wertes mit einer Sicherheit (Margin of Safety)
    fairValueSafe = fairValue*(1-marginOfSafety)

    # return the 
    return fairValueSafe