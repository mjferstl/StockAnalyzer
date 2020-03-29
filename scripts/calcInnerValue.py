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
    Allianz = Stock(3,\
        symbol='ALV.DE')
    AllianzAnalysis = StockAnalyzer(Allianz)
    AllianzAnalysis.printAnalysis()

    # Nike 
    # Wachstumsprognoe lt. finanzen.net: 17.76% --> Corona: 8%
    Nike = Stock(8,\
        symbol='NKE')
    NikeAnalysis = StockAnalyzer(Nike)
    NikeAnalysis.printAnalysis()

    # Adidas
    # Wachstumsprognose lt. finanzen.net: 12.35% --> Corona: 8%
    Adidas = Stock(8,\
        symbol='ADS.DE')
    AdidasAnalysis = StockAnalyzer(Adidas)
    AdidasAnalysis.printAnalysis()


    # RWE
    # Wachstumsrate lt. finanzen.net: 12.07% --> Corona: 8.5%
    # +++ Nicht ausreichend bewertbar, da sehr volatile Ergebnisse +++
    # Verbindlichkeiten in Höhe des 3-fachen Eigenkapitals
    # Eigenkapitalquote: 24%
    RWE = Stock(4,\
        symbol='RWE.DE')
    RWEAnalysis = StockAnalyzer(RWE)
    RWEAnalysis.printAnalysis()

    # BASF
    # Wachstumsrate lt. finanzen.net: 9.43% --> Aufgrund Corona nur 2/3
    # Eigenkapitalquote: 46%; steigend über die letzten Jahre
    # Eigenkapital ~ Verbindlichkeiten
    # Dividende: 3.30€
    BASF = Stock(9.43*(2/3),\
        symbol='BAS.DE')
    BASFAnalysis = StockAnalyzer(BASF)
    BASFAnalysis.printAnalysis()

    # Intel
    Intel = Stock(6,\
        symbol='INL.DE')
    IntelAnalysis = StockAnalyzer(Intel)
    IntelAnalysis.printAnalysis()


    # Dutch Royal Shell
    # Wachstumsrate lt. finanzen.net: 8.6% --> Ölpreisverfall: 3%
    Shell = Stock(3,\
        symbol='R6C.DE')
    ShellAnalysis = StockAnalyzer(Shell)
    ShellAnalysis.printAnalysis()

    # # Continental
    # # Wachstumrate lt. finanten.net (21.03.2020): 5.4% --> Corona: 4% (langfristig)
    # # priceEarningsRatio für 2019 mit 0 angenommen
    # Continental = Stock(4,\
    #     symbol='CON.DE')
    # ContinentalAnalysis = StockAnalyzer(Continental)
    # ContinentalAnalysis.printAnalysis()

    # Microsoft
    # Wacchstumsrate lt. finanzen.net (21.03.2020): 17.02% --> 10% 
    Microsoft = Stock(10,\
        symbol='MSF.DE')
    MicrosoftAnalysis = StockAnalyzer(Microsoft)
    MicrosoftAnalysis.printAnalysis()

    # Gazprom
    # Wachstumsrate lt. finanzen.net (21.03.2020): 5.42% --> Ölpreiskrise 3.5%
    Gazprom = Stock(3.5,\
        symbol='GAZ.DE')
    GazpromAnalysis = StockAnalyzer(Gazprom)
    GazpromAnalysis.printAnalysis()

    # Siemens
    # Wachstumsprognose lt. finanzen.net (21.03.2020): 10.72% --> 8%
    Siemens = Stock(8,\
        symbol='SIE.DE')
    SiemensAnalysis = StockAnalyzer(Siemens)
    SiemensAnalysis.printAnalysis()

    #
    # Wachstumsrate lt. finanzen.net (21.03.2020): 9.34% --> 6%
    # priceEarningsRatio fuer 2017 entfernt, da der Wert 297.28 die Berechnung verzerrt
    JohnsonJohnson = Stock(6,\
        symbol='JNJ.DE')
    JohnsonJohnsonAnalysis = StockAnalyzer(JohnsonJohnson)
    JohnsonJohnsonAnalysis.printAnalysis()