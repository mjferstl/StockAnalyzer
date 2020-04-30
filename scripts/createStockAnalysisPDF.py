
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes.Stock import Stock, StockIndex
from classes.StockCompare import StockCompare, StockComparePDF
from classes.StockAnalyzer import StockAnalyzer

import json

### Eingabe Start

stockName = 'Wabtec'


### Eingabe Ende


stocksFile = "scripts/stocks.json"
with open(stocksFile) as f:
    stockJSON = json.load(f)

stock = ''
for s in stockJSON["Stocks"]:
    if s["Name"] == stockName:
        stock = s
        break

if stock == '':
    print('please add the stock in the file ' + stocksFile)
    sys.exit(1000)

symbol = stock["Symbol"]
stockIndex = stock["Index"]

data_file = 'scripts/' + stock["data_file"]
if os.path.isfile(data_file):
    with open(data_file) as f:
        stockEstimates = json.load(f)
    annualGrowthPrc = stockEstimates["annualGrowthPrc"]
else:
    print('\n +++ no data file +++\n')
    sys.exit(1000)


index = ''
# get the index
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
    print('please add the index "' + stockIndex + ' in the file ' + stocksFile)
    sys.exit(1000)



# Laden der Daten
stock = Stock(symbol=symbol,growthRateAnnualyPrc=int(annualGrowthPrc))

# Analysieren der Daten
StockAnalyzer(stock,index["Symbol"]).printAnalysis()

#msftCompare = StockCompare(symbol)
#peerGroupList = msftCompare.getPeerGroup(symbol=symbol)
#df = msftCompare.getPeerGroupChangePrc(peerGroupList)
#mainValueCompareDF = msftCompare.comparePeerGoupMainValues(peerGroupList)

#pdf_filename = symbol + '_peer_group_compare.pdf'
#scPDF = StockComparePDF(pdf_filename)
#scPDF.addPlot(df,xlabel='Date',ylabel='stock value growth in %',title=symbol + ' - Peer group comparison')
#scPDF.addTable(mainValueCompareDF)
#scPDF.closePDF()
