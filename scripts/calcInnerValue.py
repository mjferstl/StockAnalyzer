# -*- coding: utf-8 -*-

# ---------- MODULES ----------
# user modules
from classes.Stock import Stock
from classes.StockAnalyzer import StockAnalyzer

if __name__ == "__main__":
    print()

    # Allianz
    # Wachstumsprognose lt. finanten.net: 6.86% --> Niedrigzinsen: 3%
    # Dividene: 9.60€
    Allianz = Stock(\
        earningsPerShare=[13.05,13.64,14.55,15.00,15.23,17.30,18.83],\
        WachstumsratePrc=3,\
        priceEarningsRatio=[9.85,10.02,11.23,10.37,12.57,10.05,11.55],\
        symbol='ALV')
    AllianzAnalysis = StockAnalyzer(Allianz)
    AllianzAnalysis.printAnalysis()
    #print(Allianz)


    # # Nike 
    # # Wachstumsprognoe lt. finanzen.net: 17.76% --> Corona: 9%
    # Nike = Stock(name='Nike',\
    #     earningsPerShare=[1.23,1.49,1.85,2.16,2.51,1.17,2.49],\
    #     WachstumsratePrc=9,\
    #     priceEarningsRatio=[25.07,25.90,27.48,25.56,21.11,61.37,30.99],
    #     BuchwertProAktie=7.39,\
    #     symbol='NKE')
    # print(Nike)


    # # Adidas
    # # Wachstumsprognose lt. finanzen.net: 12.35% --> Corona: 8%
    # Adidas = Stock(name='Adidas',\
    #     earningsPerShare=[3.76,2.35,3.30,4.99,6.63,8.42,10.00],\
    #     WachstumsratePrc=8,\
    #     priceEarningsRatio=[24.64,24.52,27.25,29.56,24.99,21.62,28.98],\
    #     BuchwertProAktie=31.87,\
    #     symbol='ADS')
    # print(Adidas)


    # # RWE
    # # Wachstumsrate lt. finanzen.net: 12.07% --> Corona: 8.5%
    # # +++ Nicht ausreichend bewertbar, da sehr volatile Ergebnisse +++
    # # Verbindlichkeiten in Höhe des 3-fachen Eigenkapitals
    # # Eigenkapitalquote: 24%
    # RWE = Stock(name='RWE',\
    #     earningsPerShare=[-4.49,2.77,-0.28,-9.29,3.09,0.54,13.82],\
    #     WachstumsratePrc=8.5,\
    #     priceEarningsRatio=[9.26,5.50,34.80,1.98],\
    #     BuchwertProAktie=10.99,\
    #     symbol='RWE')
    # print(RWE)

    # # BASF
    # # Wachstumsrate lt. finanzen.net: 9.43% --> Aufgrund Corona nur 2/3
    # # Eigenkapitalquote: 46%; steigend über die letzten Jahre
    # # Eigenkapital ~ Verbindlichkeiten
    # # Dividende: 3.30€
    # BASF = Stock(name='BASF',\
    #     earningsPerShare=[5.27,5.60,4.33,4.41,6.61,5.12,2.98],\
    #     WachstumsratePrc=9.43*(2/3),\
    #     priceEarningsRatio=[14.70,12.46,16.29,19.98,13.86,11.79,22.60],\
    #     BuchwertProAktie=36.84,\
    #     symbol='BAS')
    # print(BASF)

    # # Intel
    # Intel = Stock(name='Intel',\
    #     earningsPerShare=[1.89,2.31,2.33,2.12,1.99,4.48,4.71],\
    #     WachstumsratePrc=6,\
    #     priceEarningsRatio=[13.54,16.26,15.01,17.11,23.20,10.44,12.77],\
    #     BuchwertProAktie=14.46,\
    #     symbol='INL')
    # print(Intel)


    # # Dutch Royal Shell
    # # Wachstumsrate lt. finanzen.net: 8.6% --> Ölpreisverfall: 4%
    # Shell = Stock(name='Shell',\
    #     earningsPerShare=[1.66,1.43,0.20,0.43,1.21,2.10,1.53],\
    #     WachstumsratePrc=4,\
    #     priceEarningsRatio=[13.00,15.0,75.21,52.16,20.21,10.91,14.50],\
    #     BuchwertProAktie=23.44,\
    #     symbol='R6C')
    # print(Shell)

    # # Continental
    # # Wachstumrate lt. finanten.net (21.03.2020): 5.4% --> Corona: 4% (langfristig)
    # # priceEarningsRatio für 2019 mit 0 angenommen
    # Continental = Stock(name='Continental',\
    #     earningsPerShare=[9.62,11.88,13.64,14.01,14.92,14.49,-6.13],\
    #     WachstumsratePrc=4,\
    #     priceEarningsRatio=[16.57,14.78,16.46,13.11,15.08,8.34,0],\
    #     BuchwertProAktie=77.00,\
    #     symbol='CON')
    # print(Continental)

    # Microsoft
    # Wacchstumsrate lt. finanzen.net (21.03.2020): 17.02% --> 13% 
    Microsoft = Stock(\
        earningsPerShare=[2.58,2.63,1.48,2.10,2.71,2.13,5.06],\
        WachstumsratePrc=13,\
        priceEarningsRatio=[13.39,15.86,29.83,24.37,25.44,46.30,26.47],\
        symbol='MSF')
    MicrosoftAnalysis = StockAnalyzer(Microsoft)
    MicrosoftAnalysis.printAnalysis()

    # # Wachstumsrate lt. finanzen.net (21.03.2020): 12.31% --> 10%
    # SiemensHealthineers = Stock(name='Siemens Healthineers',\
    #     earningsPerShare=[1.28,1.31,1.43,1.26,1.57],\
    #     WachstumsratePrc=10,\
    #     priceEarningsRatio=[29.94,23.02],\
    #     BuchwertProAktie=9.77)
    # print(SiemensHealthineers)

    # # Gazprom
    # # Wachstumsrate lt. finanzen.net (21.03.2020): 5.42% --> Ölpreiskrise 3.5%
    # Gazprom = Stock(name='Gazprom',\
    #     earningsPerShare=[3.31,3.12,0.36,1.12,1.26,1.11,2.10],\
    #     WachstumsratePrc=3.5,\
    #     priceEarningsRatio=[2.85,2.74,12.99,3.31,4.02,3.98,2.11],\
    #     BuchwertProAktie=19.83,\
    #     symbol='GAZ')
    # print(Gazprom)

    # # Siemens
    # # Wachstumsprognose lt. finanzen.net (21.03.2020): 10.72% --> 8%
    # Siemens = Stock(name='Siemens',\
    #     earningsPerShare=[5.03,6.31,6.46,6.52,7.29,7.01,6.32],\
    #     WachstumsratePrc=8,\
    #     priceEarningsRatio=[17.53,14.81,12.22,15.76,16.02,15.49,15.33],\
    #     BuchwertProAktie=59.32,\
    #     symbol='SIE')
    # print(Siemens)

    # #
    # # Wachstumsrate lt. finanzen.net (21.03.2020): 9.34% --> 8%
    # # priceEarningsRatio fuer 2017 entfernt, da der Wert 297.28 die Berechnung verzerrt
    # JohnsonJohnson = Stock(name='Johnson & Johnson',\
    #     earningsPerShare=[4.81,5.70,5.48,5.93,0.47,5.61,5.63],\
    #     WachstumsratePrc=8,\
    #     priceEarningsRatio=[19.20,18.43,18.74,19.43,22.69,25.88],\
    #     BuchwertProAktie=22.32,\
    #     symbol='JNJ')
    # print(JohnsonJohnson)