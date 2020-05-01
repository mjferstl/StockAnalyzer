
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes.Stock import Stock, StockIndex
from classes.StockCompare import StockCompare, StockComparePDF
from classes.StockAnalyzer import StockAnalyzer

import json

### Eingabe Start

stockName = 'Aroundtown'

### Eingabe Ende


# Laden der Informationen aus dem JSON-File
stocksFile = "scripts/stocks.json"
with open(stocksFile) as f:
    stockJSON = json.load(f)

# Finden der ausgewählten Aktie im JSON-File
stock = ''
for s in stockJSON["Stocks"]:
    if s["Name"] == stockName:
        stock = s
        break

if stock == '':
    print('\n +++ Please add the stock in the file ' + stocksFile + ' +++\n')
    sys.exit(1000)

# Auslesen von Symbol und dem Index, in dem die Aktie gelistet ist
symbol = stock["Symbol"]
stockIndex = stock["Index"]

# Öffnen des zur Aktie zugehörigen Data-Files mit dem Wachstumsprognosen
# sowie den VEröffentlichungsterminen für Quartals- und Jahreszahlen
data_file = 'scripts/' + stock["data_file"]
if os.path.isfile(data_file):
    with open(data_file) as f:
        stockData = json.load(f)

    # Geschätztes jährliches Wachstum in %
    annualGrowthPrc = stockData["annualGrowthEstimates"][0]["growthPrc"]

    # Termine
    if "dates" in stockData.keys():
        stockDates = stockData["dates"]
    else:
        stockDates = None
else:
    print('\n +++ Please create a data file for ' + stockName + ' +++\n')
    sys.exit(1000)

# Auslesen des Symbols für den zur Aktie zugehörigen Index
index = ''
if stockIndex == '':
    print('No index for ' + stockName + ' given..')
    index = {}
    index["Symbol"] = None
else:
    for i in stockJSON["Index"]:
        if i["Name"] == stockIndex:
            index = i
            break

if index == '':
    print('\n +++ Please add the index "' + stockIndex + ' to the Index-Array in the file ' + stocksFile + ' +++\n')
    sys.exit(1000)


# Laden der Daten der Aktie
stock = Stock(symbol=symbol,growthRateAnnualyPrc=float(annualGrowthPrc),dates=stockDates)

# Analysieren der Daten
StockAnalyzer(stock,index["Symbol"]).printAnalysis()
