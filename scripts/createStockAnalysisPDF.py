
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes.Stock import Stock
from classes.StockCompare import StockCompare
from classes.StockAnalyzer import StockAnalyzer

symbol = 'MSFT'

stock = Stock(6,symbol)
StockAnalyzer(stock).printAnalysis()

msftCompare = StockCompare(symbol)
compareDataFrame = msftCompare.getPeerGroupComparison()
msftCompare.createPDF()