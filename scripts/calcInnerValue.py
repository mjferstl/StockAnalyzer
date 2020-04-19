# -*- coding: utf-8 -*-
import sys
# ---------- MODULES ----------
# user modules
from classes.Stock import Stock
from classes.StockAnalyzer import StockAnalyzer

if __name__ == "__main__":

    # Allianz
    # Wachstumsprognose lt. finanten.net: 6.86% --> Niedrigzinsen: 3%
    # Dividene: 9.60€
    Allianz = Stock(growthRateAnnualyPrc=3,\
        symbol='ALV.DE')
    AllianzAnalysis = StockAnalyzer(Allianz)
    AllianzAnalysis.printAnalysis()

    #sys.exit()

    # Nike 
    # Wachstumsprognoe lt. finanzen.net: 17.76% --> Corona: 8%
    Nike = Stock(growthRateAnnualyPrc=8,\
        symbol='NKE')
    NikeAnalysis = StockAnalyzer(Nike)
    NikeAnalysis.printAnalysis()

    # Adidas
    # Wachstumsprognose lt. finanzen.net: 12.35% --> Corona: 8%
    Adidas = Stock(growthRateAnnualyPrc=8,\
        symbol='ADS.DE')
    AdidasAnalysis = StockAnalyzer(Adidas)
    AdidasAnalysis.printAnalysis()


    # RWE
    # Wachstumsrate lt. finanzen.net: 12.07% --> Corona: 8.5%
    # +++ Nicht ausreichend bewertbar, da sehr volatile Ergebnisse +++
    # Verbindlichkeiten in Höhe des 3-fachen Eigenkapitals
    # Eigenkapitalquote: 24%
    RWE = Stock(growthRateAnnualyPrc=4,\
        symbol='RWE.DE')
    RWEAnalysis = StockAnalyzer(RWE)
    RWEAnalysis.printAnalysis()

    # BASF
    # Wachstumsrate lt. finanzen.net: 9.43% --> Aufgrund Corona nur 2/3
    # Eigenkapitalquote: 46%; steigend über die letzten Jahre
    # Eigenkapital ~ Verbindlichkeiten
    # Dividende: 3.30€
    BASF = Stock(growthRateAnnualyPrc=9.43*(2/3),\
        symbol='BAS.DE')
    BASFAnalysis = StockAnalyzer(BASF)
    BASFAnalysis.printAnalysis()

    # Intel
    Intel = Stock(growthRateAnnualyPrc=6,\
        symbol='INL.DE')
    IntelAnalysis = StockAnalyzer(Intel)
    IntelAnalysis.printAnalysis()


    # Dutch Royal Shell
    # Wachstumsrate lt. finanzen.net: 8.6% --> Ölpreisverfall: 3%
    Shell = Stock(growthRateAnnualyPrc=3,\
        symbol='R6C.DE')
    ShellAnalysis = StockAnalyzer(Shell)
    ShellAnalysis.printAnalysis()

    # Microsoft
    # Wacchstumsrate lt. finanzen.net (21.03.2020): 17.02% --> 10% 
    Microsoft = Stock(growthRateAnnualyPrc=10,\
        symbol='MSF.DE')
    MicrosoftAnalysis = StockAnalyzer(Microsoft)
    MicrosoftAnalysis.printAnalysis()

    # Gazprom
    # Wachstumsrate lt. finanzen.net (21.03.2020): 5.42% --> Ölpreiskrise 3.5%
    Gazprom = Stock(growthRateAnnualyPrc=3.5,\
        symbol='GAZ.DE')
    GazpromAnalysis = StockAnalyzer(Gazprom)
    GazpromAnalysis.printAnalysis()

    # Siemens
    # Wachstumsprognose lt. finanzen.net (21.03.2020): 10.72% --> 8%
    Siemens = Stock(growthRateAnnualyPrc=8,\
        symbol='SIE.DE')
    SiemensAnalysis = StockAnalyzer(Siemens)
    SiemensAnalysis.printAnalysis()

    #
    # Wachstumsrate lt. finanzen.net (21.03.2020): 9.34% --> 6%
    # priceEarningsRatio fuer 2017 entfernt, da der Wert 297.28 die Berechnung verzerrt
    JohnsonJohnson = Stock(growthRateAnnualyPrc=6,\
        symbol='JNJ.DE')
    JohnsonJohnsonAnalysis = StockAnalyzer(JohnsonJohnson)
    JohnsonJohnsonAnalysis.printAnalysis()


    Aroundtown = Stock(growthRateAnnualyPrc=8,symbol="AT1.DE")
    AroundtownAnalysis = StockAnalyzer(Aroundtown)
    AroundtownAnalysis.printAnalysis()

    Vonovia = Stock(growthRateAnnualyPrc=6,symbol='VNA.DE')
    VonoviaAnalysis = StockAnalyzer(Vonovia)
    VonoviaAnalysis.printAnalysis()