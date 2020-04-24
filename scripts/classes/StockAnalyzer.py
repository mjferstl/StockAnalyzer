
# ---------- MODULES ----------
# standard modules
import numpy as np
import pandas as pd

import datetime

# custom modules
from classes.Stock import Stock
from classes.FinnhubAPI import FinnhubClient
from utils.generic import npDateTime64_2_str

# ---------- CLASSES ----------
class StockAnalyzer():

    # value shared across all class instances
    #
    # margin of safety: 20% --> 0.20
    marginOfSafety = 0.2
    # expected return (exprectedReturn): 15% --> 0.15
    expectedReturnPrc = 10
    expectedReturn = expectedReturnPrc/100
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
        self.calcLevermannScore()
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
        # Free Chashflow der letzten Jahre
        CF = self.stock.financialData.loc['freeCashFlow',:].copy()

        CF.fillna(CF.mean(), inplace=True) # TODO: NaN Werte werden durch Mittelwert ersetzt

        # Sortierung in aufsteigender Reihenfolge (alt -> neu)
        dates = CF.index.values.copy() # copy ist hier wichtig, da sonst der urspruegliche DataFrame falsch geordnet wird
        dates.sort()
        CF_sorted = [CF.loc[date] for date in dates]

        # mittleres Wachstum des Cashflows der letzten Jahre
        growthAbs, growthPrc = [], []
        for y in range(1,len(CF_sorted)):
            # absolutes Wachstum des Cashflows
            growthAbs.append(CF_sorted[y]-CF_sorted[y-1])
            # relatives Wachstum des Cashflows in Prozent
            growthPrc.append(growthAbs[-1]/CF_sorted[y-1]*100)
        
        # mittleres relatives Wachstum
        #print('growthPrc: ' + str(growthPrc))
        meanGrowthPrc = sum(growthPrc)/len(growthPrc)
        print('mittleres Cashflow-Wachstum der letzten {years:.0f} Jahre: {cfGrowth:.2f}%'.format(years=len(CF_sorted),cfGrowth=meanGrowthPrc))

        discountRate = self.expectedReturn # discount in percent
        presentValue = [] # present value
        # Scheife ueber alle zu betrachtenden Jahre
        for year in range(1,self.investmentHorizon+1):
            # Geldwert des zukuenftigen Cashflow fuer ein bestimmtes Jahr in der Zukunft
            CF_t = CF_sorted[-1]*pow(1+meanGrowthPrc/100,year)
            #print('Jahr: ' + str(year) + ', Cashflow: ' + str(CF_t))

            # "present value" des cashflows in der Zukunft
            PV_t = CF_t / pow(1+discountRate,year)

            # Aufsummierung des "present values" fuer den Betrachtungszeitraum
            presentValue.append(PV_t)

        # Summe der, auf den aktuellen Zeitpunkt bezogenen, zukuenfitgen Cashflows
        presentValue = sum(presentValue)
        #print(PV)

        self.NPV = (presentValue - self.stock.keyStatistics["marketCap"])/self.stock.keyStatistics["sharesOutstanding"]


    def calcLevermannScore(self):
        # TODO calcLevermannScore implementieren
        LevermannScore = 0
        #print(self.stock.financialData)

        # RoE Eigenkapitalrendite (Gewinn / Eigenkapital)
        # Eigenkapital
        EK = list(self.stock.financialData.loc['Total Stockholder Equity',:].copy())
        # TODO Klärung ob "Net Income" (abzgl. Steuern etc.) oder "Operating Income" (Steuern noch nicht abgezogen)
        Gewinn = list(self.stock.financialData.loc['Net Income',:].copy())

        # RoE fuer jedes Jahr
        annualyRoE = [gewinn/ek*100 for gewinn,ek in zip(Gewinn,EK)]
        # RoE Mittelwert ueber die Jahre
        RoE = sum(annualyRoE)/len(annualyRoE)

        # RoE > 20% -> +1, 10% < RoE < 20% -> 0, RoE < 10% -> -1
        if (RoE > 20):
            LevermannScore += 1
        elif (RoE < 10):
            LevermannScore -= 1

        # EBIT-Marge (EBIT / Umsatz)
        
        # EBIT
        EBIT = list(self.stock.financialData.loc['Ebit',:].copy())
        # Umsatz
        Gesamtumsatz = list(self.stock.financialData.loc['Total Revenue',:].copy())

        # EBIT-Marge der letzten Jahre und Mittelwert
        annualyEbitMarge = [ebit/umsatz*100 for ebit,umsatz in zip(EBIT,Gesamtumsatz)]
        EbitMarge = sum(annualyEbitMarge)/len(annualyEbitMarge)

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
        annualyEKratio = [ek/gk*100 for ek,gk in zip(EK,GK)]
        EKratio = sum(annualyEKratio)/len(annualyEKratio)

        # EKQ > 25% -> +1, 15% < EKQ < 25% -> 0, EKQ < 15% -> -1
        if (EKratio > 25):
            LevermannScore += 1
        elif (EKratio < 15):
            LevermannScore -= 1

        # KGV aktuelles Jahr
        # 
        KGV = self.stock.getBasicDataItem(Stock.PE_RATIO)
        
        # 0 < KGV < 12 -> +1, 12 < KGV < 16 -> 0, KGV < 0, KGV > 16 -> -1
        if (KGV < 12):
            LevermannScore += 1
        elif (KGV > 16):
            LevermannScore -= 1

        # KGV 5 Jahre (letzten 3 Jahre, aktuelles Jahr, nächstes Jahr)
        EPSdf = self.stock.financialData.loc['dilutedEPS',:].copy()
        EPS = list(EPSdf)

        dates = EPSdf.index.values.copy()
        kurse = []
        for d in dates:
            recordDates = npDateTime64_2_str(self.stock.historicalData.index.values)
            # finde ein passendes Datum
            if d not in recordDates:
                for i in range(1,30):
                    newLastDate = datetime.datetime.strptime(d,'%Y-%m-%d') + datetime.timedelta(days=1)
                    d = datetime.datetime.strftime(newLastDate,'%Y-%m-%d')
                    if d in recordDates:
                        break
            kurse.append(self.stock.historicalData.loc[d,'Close'])
        #print(kurse)
        kgv_past = [k/e for e,k in zip(EPS,kurse)]
        print('KGV letzte Jahre: ' + str(kgv_past))
        KGV_5y = kgv_past[0:3] # letzte 3 Jahre
        KGV_5y.reverse()
        KGV_5y.append(KGV) # aktuelles Jahr 
        print(KGV_5y)
        # TODO naechstes Jahr schaetzen und zur Liste hinzufuegen

        # Mittelwert 
        KGV_5y_avg = sum(KGV_5y)/len(KGV_5y)

        # 0 < KGV < 12 -> +1, 12 < KGV < 16 -> 0, KGV < 0, KGV > 16 -> -1
        if (KGV_5y_avg < 12):
            LevermannScore += 1
        elif (KGV_5y_avg > 16):
            LevermannScore -= 1

        # Mittelwert Analystenmeinung (Kaufen=1, Halten=2, Verkaufen=3)
        # 2,5 < Mittelwert -> +1, 1,5 < Mittelwert < 2,5 -> 0, Mittelwert < 1,5
        
        # Reaktion auf Quartalszahlen
        # ?

        # Gewinnrevisionen
        #
        
        # Kursverlauf der letzten 6 Monate
        #

        # Kursverlauf der letzten 12 Monate
        #

        # Kursmomentum
        #

        # Reversaleffekt
        #

        # Gewinnwachstum
        #

        # optinal: Marktkapitalisierung
        #

        # optional: Branche
        # 

        print('Levermann Score: ' + str(LevermannScore))
        # Gesamt Bewertung:
        # Kaufen: Large Caps >= 4 Punkte; Small und Mid >= 7 Punkte
        # Halten: Large Caps >= 3 Punkte; Small und Mid >= 5-6 Punkte
        # Verkaufen: Large Caps >= 2 Punkte; Small und Mid >= 4 Punkte
        pass
    
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
            if self.NPV > 0:
                strNPVcomment = 'time to invest!'
            else:
                strNPVcomment = 'too expensive...'
            strNetPresentValue = '{str:{strFormat}}{gn:6.2f}'.format(str='NetPresentValue:',gn=self.NPV,strFormat=stringFormat) + \
                ' ' + self.stock.currencySymbol + ' (' + strNPVcomment + ')\n'

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
            ' - investment horizon: {years:.0f} years\n'.format(years=self.investmentHorizon) + \
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