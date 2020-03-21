import numpy as np
from datetime import datetime
#import time

#from alpha_vantage.timeseries import TimeSeries

#AlphaVantageKey = '0KZWQB1Z0MEJW1PU'
boerseDefault = 'FRK'

class Aktie:
    def __init__(self,earningsPerShare,WachstumsratePrc,KGV,BuchwertProAktie=0,name='unnamed',symbol='',boerse=''):
        self.meanEarningsPerShare = self.calcMeanWeightedValue(earningsPerShare)
        self.Wachstumsrate = 1+(WachstumsratePrc/100)
        self.meanKGV = self.calcMeanWeightedValue(KGV)
        self.name = name
        self.bookValuePerShare = self.calcMeanWeightedValue(BuchwertProAktie)
        self.symbol = symbol
        self.currentStockValue = None

        # Handelsplatz
        if boerse is '':
            self.boerse = boerseDefault
        else:
            self.boerse = boerse

        # Initialwert für den "inneren Wert"
        self.innerValue = -1
        self.GrahamNumber = -1

        # Berechnungen
        if self.bookValuePerShare != 0:
            self.calcGrahamNumber()


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
        if self.bookValuePerShare != 0:
            self.GrahamNumber = np.sqrt(15 * self.meanEarningsPerShare * 1.5 * self.bookValuePerShare)

    # Funktion zur Berechnung des sog. "inneren Wertes" der Aktie
    def calcInnerValue(self,renditeerwartung=8):
        self.innerValue = getInnerValue10years(self.meanEarningsPerShare,self.Wachstumsrate,self.meanKGV,renditeerwartung)

    #
    def getCurrentStockValue(self):
        if (self.symbol is not ''):
            today = datetime.utcnow().strftime('%Y-%m-%d')
            try:
                ts = TimeSeries(AlphaVantageKey)
                aapl, meta = ts.get_daily(symbol=self.symbol + '.' + self.boerse)
                return float(aapl[today]['4. close'])
            except:
                return None
        else:
            return None


    # Funktion zur Formattierung der Ausgabe
    def __str__(self):
        if self.innerValue == -1:
            self.calcInnerValue()

        strGrahamNumber = ''
        if self.GrahamNumber != -1:
            strGrahamNumber = 'Graham Number:     {gn:6.2f} €\n'.format(gn=self.GrahamNumber)

        #self.currentStockValue = self.getCurrentStockValue()
        strCurrentStockValue = ''
        if (self.currentStockValue is not None):
            strCurrentStockValue = 'Aktueller Kurs:    {val:6.2f} €\n'.format(val=self.currentStockValue)

        return '-'*27 + '\n' + \
            ' '*3 + self.name + '\n' + \
            'avg. weighted EPS: {eps:6.2f} €'.format(eps=self.meanEarningsPerShare) + '\n' + \
            'avg. KGV:          {kgv:6.2f}'.format(kgv=self.meanKGV) + '\n\n' + \
            'Fairer Wert:       {val:6.2f} €'.format(val=self.innerValue) + '\n' + \
            strGrahamNumber + \
            strCurrentStockValue + \
            '-'*27 + '\n'

# Berechnung des "Inneren Wertes" (oft auch als "Fairer Wert" bezeichnet)
# Berechnungsgrundpagen:
# - angegebene Wachstumsrate gilt fuer die naechsten 10 Jahre
# - Margin of Safety: 10%, sofern nicht anders angegeben
def getInnerValue10years(earningsPerShare,Wachstumsrate,KGV,Renditeerwartung,marginOfSafety=0.1,):
    # Berechnung des Gewinns pro Aktie in 10 Jahren
    gewinn10y = earningsPerShare*(Wachstumsrate**10)

    # Berechnung des Aktienpreises in 10 Jahren auf Grundlage des aktuellen Kurs-Gewinn-Verhältnisses
    price10y = gewinn10y*KGV

    # Berechnung des fairen/inneren Preises zum aktuellen Zeitpunkt auf Grundlage der Renditeerwartung
    innererWert = price10y/((1+(Renditeerwartung/100))**10)
    return innererWert*(1-marginOfSafety)


if __name__ == "__main__":
    # Allianz
    # Wachstumsprognose lt. finanten.net: 6.86% --> Niedrigzinsen: 3%
    # Dividene: 9.60€
    Allianz = Aktie(name='Allianz',\
        earningsPerShare=[13.05,13.64,14.55,15.00,15.23,17.30,18.83],\
        WachstumsratePrc=3,\
        KGV=[9.85,10.02,11.23,10.37,12.57,10.05,11.55],\
        BuchwertProAktie=149.44,\
        symbol='ALV')
    print(Allianz)


    # Nike 
    # Wachstumsprognoe lt. finanzen.net: 17.76% --> Corona: 9%
    Nike = Aktie(name='Nike',\
        earningsPerShare=[1.23,1.49,1.85,2.16,2.51,1.17,2.49],\
        WachstumsratePrc=9,\
        KGV=[25.07,25.90,27.48,25.56,21.11,61.37,30.99],
        BuchwertProAktie=7.39,\
        symbol='NKE')
    print(Nike)


    # Adidas
    # Wachstumsprognose lt. finanzen.net: 12.35% --> Corona: 8%
    Adidas = Aktie(name='Adidas',\
        earningsPerShare=[3.76,2.35,3.30,4.99,6.63,8.42,10.00],\
        WachstumsratePrc=8,\
        KGV=[24.64,24.52,27.25,29.56,24.99,21.62,28.98],\
        BuchwertProAktie=31.87,\
        symbol='ADS')
    print(Adidas)


    # RWE
    # Wachstumsrate lt. finanzen.net: 12.07% --> Corona: 8.5%
    # +++ Nicht ausreichend bewertbar, da sehr volatile Ergebnisse +++
    # Verbindlichkeiten in Höhe des 3-fachen Eigenkapitals
    # Eigenkapitalquote: 24%
    RWE = Aktie(name='RWE',\
        earningsPerShare=[-4.49,2.77,-0.28,-9.29,3.09,0.54,13.82],\
        WachstumsratePrc=8.5,\
        KGV=[9.26,5.50,34.80,1.98],\
        BuchwertProAktie=10.99,\
        symbol='RWE')
    print(RWE)

    # BASF
    # Wachstumsrate lt. finanzen.net: 9.43% --> Aufgrund Corona nur 2/3
    # Eigenkapitalquote: 46%; steigend über die letzten Jahre
    # Eigenkapital ~ Verbindlichkeiten
    # Dividende: 3.30€
    BASF = Aktie(name='BASF',\
        earningsPerShare=[5.27,5.60,4.33,4.41,6.61,5.12,2.98],\
        WachstumsratePrc=9.43*(2/3),\
        KGV=[14.70,12.46,16.29,19.98,13.86,11.79,22.60],\
        BuchwertProAktie=36.84,\
        symbol='BAS')
    print(BASF)

    # Intel
    Intel = Aktie(name='Intel',\
        earningsPerShare=[1.89,2.31,2.33,2.12,1.99,4.48,4.71],\
        WachstumsratePrc=6,\
        KGV=[13.54,16.26,15.01,17.11,23.20,10.44,12.77],\
        BuchwertProAktie=14.46,\
        symbol='INL')
    print(Intel)


    # Dutch Royal Shell
    # Wachstumsrate lt. finanzen.net: 8.6% --> Ölpreisverfall: 4%
    Shell = Aktie(name='Shell',\
        earningsPerShare=[1.66,1.43,0.20,0.43,1.21,2.10,1.53],\
        WachstumsratePrc=4,\
        KGV=[13.00,15.0,75.21,52.16,20.21,10.91,14.50],\
        BuchwertProAktie=23.44,\
        symbol='R6C')
    print(Shell)

    # Continental
    # Wachstumrate lt. finanten.net (21.03.2020): 5.4% --> Corona: 4% (langfristig)
    # KGV für 2019 mit 0 angenommen
    Continental = Aktie(name='Continental',\
        earningsPerShare=[9.62,11.88,13.64,14.01,14.92,14.49,-6.13],\
        WachstumsratePrc=4,\
        KGV=[16.57,14.78,16.46,13.11,15.08,8.34,0],\
        BuchwertProAktie=77.00,\
        symbol='CON')
    print(Continental)

    # Microsoft
    # Wacchstumsrate lt. finanzen.net (21.03.2020): 17.02% --> 13% 
    Microsoft = Aktie(name='Microsoft',\
        earningsPerShare=[2.58,2.63,1.48,2.10,2.71,2.13,5.06],\
        WachstumsratePrc=13,\
        KGV=[13.39,15.86,29.83,24.37,25.44,46.30,26.47],\
        BuchwertProAktie=13.2,\
        symbol='MSF')
    print(Microsoft)

    # Wachstumsrate lt. finanzen.net (21.03.2020): 12.31% --> 10%
    SiemensHealthineers = Aktie(name='Siemens Healthineers',\
        earningsPerShare=[1.28,1.31,1.43,1.26,1.57],\
        WachstumsratePrc=10,\
        KGV=[29.94,23.02],\
        BuchwertProAktie=9.77)
    print(SiemensHealthineers)

    # Gazprom
    # Wachstumsrate lt. finanzen.net (21.03.2020): 5.42% --> Ölpreiskrise 3.5%
    Gazprom = Aktie(name='Gazprom',\
        earningsPerShare=[3.31,3.12,0.36,1.12,1.26,1.11,2.10],\
        WachstumsratePrc=3.5,\
        KGV=[2.85,2.74,12.99,3.31,4.02,3.98,2.11],\
        BuchwertProAktie=19.83,\
        symbol='GAZ')
    print(Gazprom)

    # Siemens
    # Wachstumsprognose lt. finanzen.net (21.03.2020): 10.72% --> 8%
    Siemens = Aktie(name='Siemens',\
        earningsPerShare=[5.03,6.31,6.46,6.52,7.29,7.01,6.32],\
        WachstumsratePrc=8,\
        KGV=[17.53,14.81,12.22,15.76,16.02,15.49,15.33],\
        BuchwertProAktie=59.32,\
        symbol='SIE')
    print(Siemens)

    #
    # Wachstumsrate lt. finanzen.net (21.03.2020): 9.34% --> 8%
    # KGV fuer 2017 entfernt, da der Wert 297.28 die Berechnung verzerrt
    JohnsonJohnson = Aktie(name='Johnson & Johnson',\
        earningsPerShare=[4.81,5.70,5.48,5.93,0.47,5.61,5.63],\
        WachstumsratePrc=8,\
        KGV=[19.20,18.43,18.74,19.43,22.69,25.88],\
        BuchwertProAktie=22.32,\
        symbol='JNJ')
    print(JohnsonJohnson)