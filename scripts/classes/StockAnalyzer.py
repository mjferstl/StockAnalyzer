
# ---------- MODULES ----------
# standard modules
import numpy as np

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
    useWeightedHistoricalData = True
    weightingStep = 1
    
    def __init__(self,stock):
        if not isinstance(stock,Stock):
            raise TypeError('Object ' + str(stock) + ' is no instance of class Stock')
        
        self.stock = stock

        # variables for anayzing the stock
        # EPS
        self.eps = None
        self.epsWeightYears = None
        self.calcWeightedEps()

        # P/E (Price Earnings Ratio)
        self.priceEarningsRatio = None
        self.calcPriceEarningsRatio()

        self.GrahamNumber = None
        self.fairValue = None
        self.recommendations = None

        self.dividendYield = 0

        # analyze the stock
        self.analyzeStock()

    
    def analyzeStock(self):
        self.calcFairValue()
        self.calcGrahamNumber()
        self.recommendations = self.getRecommendations()


    def calcGrahamNumber(self):
        if (self.eps is not None) and (self.stock.isItemInBasicData('bookValuePerShare')):

            if (self.eps < 0):
                print(' +++ EPS < 0! +++')
                self.eps = 0
            if (self.stock.getBasicDataItem('bookValuePerShare') < 0):
                print(' +++ book value per share < 0! +++')
                
            self.GrahamNumber = np.sqrt(15 * self.eps * 1.5 * self.stock.getBasicDataItem('bookValuePerShare'))
        else:
            self.GrahamNumber = 0


    # Funktion zur Berechnung des sog. "inneren Wertes" der Aktie
    def calcFairValue(self):

        if self.stock.growthRateAnnualy is None:
            raise ValueError('The expected annualy growth rate for ' + self.stock.name + ' is of type None')
        if not self.stock.isItemInBasicData('P/E'):
            raise KeyError('The P/E for ' + self.stock.name + ' is not existant')

        # calclate the new growth rate, as the dividend yield gets added
        growthRateAnnualy = self.stock.growthRateAnnualy# + self.dividendYield
        if growthRateAnnualy != self.stock.growthRateAnnualy:
            print("growthRateAnnualy: " + str(self.stock.growthRateAnnualy))
            print("The annualy growth rate gets increased by the dividend yield of {divYield:5.2f}%. New annualy growth rate: {grwRate:5.2f}".format(divYield=self.dividendYield,grwRate=growthRateAnnualy))

        self.fairValue = calcFairValue(self.eps,growthRateAnnualy,self.stock.getBasicDataItem('P/E'),StockAnalyzer.expectedReturn,StockAnalyzer.marginOfSafety,StockAnalyzer.investmentHorizon)


    def calcWeightedEps(self):

        epsKey = 'dilutedEPS'
        
        if (self.useWeightedHistoricalData) and (self.stock.financialData is not None) and (epsKey in self.stock.financialData.index.values):
            # get historical EPS data
            epsHistory = self.stock.financialData.loc[epsKey,:]

            # remove NaN values
            for row in epsHistory.index.values:
                if np.isnan(epsHistory.loc[row]):
                    epsHistory = epsHistory.drop(row)

            # create weighting with the global defined stepsize
            weighting = [1]
            for i in range(len(epsHistory)-1):
                weighting.append(weighting[-1]+StockAnalyzer.weightingStep)
            weighting = list(reversed(weighting))

            # calculate the weighted eps 
            weightedEps = [factor*value for value,factor in zip(epsHistory,weighting)]
            self.eps = sum(weightedEps)/sum(weighting)
            self.epsWeightYears = len(epsHistory)
        else:
            self.eps = self.stock.getBasicDataItem('EPS')

    
    def calcPriceEarningsRatio(self):
        if (self.stock.financialData is not None) and ('dilutedEPS' in self.stock.financialData.index.values):
            self.priceEarningsRatio = self.stock.getBasicDataItem('P/E')
        else:
            self.priceEarningsRatio = self.stock.getBasicDataItem('P/E')


    def getRecommendations(self):
        recommendations = FinnhubClient(self.stock.symbol).getRecommendationsDataFrame()
        return recommendations


    def printAnalysis(self):

        if self.priceEarningsRatio is None:
            self.calcPriceEarningsRatio()

        # variables for formatting the console output
        stringFormat = "24s"
        dispLineLength = 40
        sepString = '-'*dispLineLength + '\n'

        #
        if self.fairValue is None:
            self.calcFairValue()

        # string to print the dividend and the dividend yield
        strDividend = ''
        if self.stock.isItemInBasicData('dividend'):
            strDividendYield = ''

            stockPrice = self.stock.getBasicDataItem(Stock.MARKET_PRICE)
            if stockPrice is not None:
                strDividendYield = ' (' + u"ca. " + '{divYield:3.1f}%)'.format(divYield=self.stock.getBasicDataItem(Stock.DIVIDEND)/stockPrice*100)
            strDividend = '{str:{strFormat}}{div:6.2f}'.format(str='Dividend:',div=self.stock.getBasicDataItem(Stock.DIVIDEND),strFormat=stringFormat) + ' ' + self.stock.currencySymbol + strDividendYield + '\n'

        strWeightedEps = ''
        if (self.eps != self.stock.getBasicDataItem('EPS')) and (self.epsWeightYears is not None):
            strEntry = 'weighted EPS ({years:.0f}y):'.format(years=self.epsWeightYears)
            strWeightedEps = '{str:{strFormat}}{epsw:6.2f}'.format(str=strEntry,epsw=self.eps,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

        # string to print the graham number
        strGrahamNumber = ''
        if self.GrahamNumber is not None:
            strGrahamNumber = '{str:{strFormat}}{gn:6.2f}'.format(str='Graham number:',gn=self.GrahamNumber,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

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
            '{str:{strFormat}}{eps:6.2f}'.format(str='EPS:',eps=self.stock.getBasicDataItem('EPS'),strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n' + \
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
            strCurrentStockValue + \
            sepString + '\n'

        # print to the console
        print(string2Print)




# ---------- FUNCTIONS ----------
#
def calcFairValue(earningsPerShare,growthRateAnnualy,priceEarningsRatio,exprectedReturn,marginOfSafety,investmentHorizon=10):
    """
        Berechnung des "Inneren Wertes" (oft auch als "Fairer Wert" bezeichnet)
        Berechnungsgrundpagen:
        - angegebene growthRateAnnualy gilt fuer die naechsten Jahre
    """

    # Berechnung des Gewinns pro Aktie in der Zukunft
    futureEarningsPerShare = earningsPerShare*((1+growthRateAnnualy)**StockAnalyzer.investmentHorizon)

    # Berechnung des zukuenfiten Aktienpreises auf Grundlage des aktuellen Kurs-Gewinn-Verhaeltnisses
    futureStockValue = futureEarningsPerShare*priceEarningsRatio

    # Berechnung des fairen/inneren Preises zum aktuellen Zeitpunkt auf Grundlage der Renditeerwartung
    fairValue = futureStockValue/((1+(exprectedReturn/100))**investmentHorizon)
    
    # Berechnung des fairen Wertes mit einer Sicherheit (Margin of Safety)
    fairValueSafe = fairValue*(1-marginOfSafety)

    # return the 
    return fairValueSafe