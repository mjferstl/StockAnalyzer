
# ---------- MODULES ----------
# standard modules
import numpy as np

# custom modules
from classes.Stock import Stock

# ---------- CLASSES ----------
class StockAnalyzer():
    
    def __init__(self,stock):
        if not isinstance(stock,Stock):
            raise TypeError('Object ' + str(stock) + ' is no instance of class Stock')
        
        self.stock = stock

        # variables for anayzing the stock
        self.GrahamNumber = None
        self.innerValue = None

    
    def calcGrahamNumber(self):
        if (self.stock.meanEarningsPerShare is not None) and (self.stock.bookValuePerShare is not None):
            self.GrahamNumber = np.sqrt(15 * self.stock.meanEarningsPerShare * 1.5 * self.stock.bookValuePerShare)


    # Funktion zur Berechnung des sog. "inneren Wertes" der Aktie
    def calcInnerValue(self,renditeerwartung=8):
        self.innerValue = calcInnerValue10years(self.stock.meanEarningsPerShare,self.stock.Wachstumsrate,self.stock.meanPriceEarningsRatio,renditeerwartung)


    def printAnalysis(self):
        if self.innerValue is None:
            self.calcInnerValue()

        strGrahamNumber = ''
        if self.GrahamNumber is not None:
            strGrahamNumber = 'Graham Number:     {gn:6.2f}'.format(gn=self.GrahamNumber) + ' ' + self.stock.currencySymbol + '\n'

        #self.currentStockValue = self.getCurrentStockValue()
        strCurrentStockValue = ''
        if (self.stock.currentStockValue is not None):
            strCurrentStockValue = 'Aktueller Kurs:    {val:6.2f}'.format(val=self.stock.currentStockValue) + ' ' + self.stock.currencySymbol + '\n'

        strDividend = ''
        if self.stock.dividend is not None:
            strDividendYield = ''
            if self.stock.currentStockValue is not None:
                strDividendYield = ' (' + u"\u2248" + '{divYield:3.1f}%)'.format(divYield=self.stock.dividend/self.stock.currentStockValue*100)
            strDividend = 'Dividend:          {div:6.2f}'.format(div=self.stock.dividend) + ' ' + self.stock.currencySymbol + strDividendYield + '\n'

        print('-'*27 + '\n' + \
            ' '*3 + self.stock.name + '\n' + \
            'avg. weighted EPS: {eps:6.2f}'.format(eps=self.stock.meanEarningsPerShare) + ' ' + self.stock.currencySymbol + '\n' + \
            'avg. P/E:          {priceEarningsRatio:6.2f}'.format(priceEarningsRatio=self.stock.meanPriceEarningsRatio) + '\n' + \
            strDividend + \
            '\n' + \
            'Fairer Wert:       {val:6.2f}'.format(val=self.innerValue) + ' ' + self.stock.currencySymbol + '\n' + \
            strGrahamNumber + \
            strCurrentStockValue + \
            '-'*27 + '\n')




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