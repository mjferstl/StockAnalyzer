import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes.Stock import Stock
from classes.StockAnalyzer import StockAnalyzer


### Eingabe Start

stockName = 'Aroundtown'

### Eingabe Ende

# Laden der Daten der Aktie
stock = Stock(stockName=stockName)

# Analysieren der Daten
StockAnalyzer(stock,stock.indexSymbol).printBasicAnalysis()

for peer in stock.getPeerGroup().remove(stock.symbol):
    StockAnalyzer(Stock(stockSymbol=peer)).printBasicAnalysis()