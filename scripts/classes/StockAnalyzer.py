
# ---------- MODULES ----------
# standard modules
import numpy as np

# custom modules
from classes.Stock import Stock

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
    
    def __init__(self,stock):
        if not isinstance(stock,Stock):
            raise TypeError('Object ' + str(stock) + ' is no instance of class Stock')
        
        self.stock = stock

        # variables for anayzing the stock
        self.GrahamNumber = None
        self.fairValue = None

        self.dividendYield = 0
        if (self.stock.dividend is not None) and (self.stock.currentStockValue is not None):
            self.dividendYield = self.stock.dividend / self.stock.currentStockValue

        self.analyzeStock()

    
    def analyzeStock(self):
        self.calcFairValue()
        self.calcGrahamNumber()

    
    def calcGrahamNumber(self):
        if (self.stock.earningsPerShare is not None) and (self.stock.bookValuePerShare is not None):
            self.GrahamNumber = np.sqrt(15 * self.stock.earningsPerShare * 1.5 * self.stock.bookValuePerShare)


    # Funktion zur Berechnung des sog. "inneren Wertes" der Aktie
    def calcFairValue(self):

        # calclate the new growth rate, as the dividend yield gets added
        growthRateAnnualy = self.stock.growthRateAnnualy# + self.dividendYield
        if growthRateAnnualy != self.stock.growthRateAnnualy:
            print("growthRateAnnualy: " + str(self.stock.growthRateAnnualy))
            print("The annualy growth rate gets increased by the dividend yield of {divYield:5.2f}%. New annualy growth rate: {grwRate:5.2f}".format(divYield=self.dividendYield,grwRate=growthRateAnnualy))

        self.fairValue = calcFairValue(self.stock.earningsPerShare,growthRateAnnualy,self.stock.priceEarningsRatio,StockAnalyzer.expectedReturn,StockAnalyzer.marginOfSafety,StockAnalyzer.investmentHorizon)


    def printAnalysis(self):

        # variables for formatting the console output
        stringFormat = "24s"
        dispLineLength = 40
        sepString = '-'*dispLineLength + '\n'

        #
        if self.fairValue is None:
            self.calcFairValue()

        # string to print the dividend and the dividend yield
        strDividend = ''
        if self.stock.dividend is not None:
            strDividendYield = ''
            if self.stock.currentStockValue is not None:
                strDividendYield = ' (' + u"\u2248" + '{divYield:3.1f}%)'.format(divYield=self.stock.dividend/self.stock.currentStockValue*100)
            strDividend = '{str:{strFormat}}{div:6.2f}'.format(str='Dividend:',div=self.stock.dividend,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + strDividendYield + '\n'

        # string to print the graham number
        strGrahamNumber = ''
        if self.GrahamNumber is not None:
            strGrahamNumber = '{str:{strFormat}}{gn:6.2f}'.format(str='Graham number:',gn=self.GrahamNumber,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'

        # string to print the stock's current value
        strCurrentStockValue = ''
        if (self.stock.currentStockValue is not None):
            strCurrentStockValue = '{str:{strFormat}}{val:6.2f}'.format(str="current value:",val=self.stock.currentStockValue,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n'


        # format margin around stock name
        stockNameOutput = self.stock.name
        if (len(self.stock.name) < dispLineLength):
            margin = int((dispLineLength-len(self.stock.name))/2)
            stockNameOutput = ' '*margin + self.stock.name + ' '*margin

        string2Print = sepString + \
            stockNameOutput + '\n' + \
            sepString + \
            '{str:{strFormat}}{eps:6.2f}'.format(str='EPS:',eps=self.stock.earningsPerShare,strFormat=stringFormat) + ' ' + self.stock.currencySymbol + '\n' + \
            '{str:{strFormat}}{priceEarningsRatio:6.2f}'.format(str='P/E:',priceEarningsRatio=self.stock.priceEarningsRatio,strFormat=stringFormat) + '\n' + \
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