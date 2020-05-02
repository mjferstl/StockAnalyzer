
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes.Stock import Stock, StockIndex
from classes.StockCompare import StockCompare, StockComparePDF
from classes.StockAnalyzer import StockAnalyzer

import json

### Eingabe Start

stockName = 'Microsoft'

### Eingabe Ende


# Laden der Daten der Aktie
stock = Stock(stockName=stockName)

# Analysieren der Daten
StockAnalyzer(stock,stock.indexSymbol).printAnalysis()
