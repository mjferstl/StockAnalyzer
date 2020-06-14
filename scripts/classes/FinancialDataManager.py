
from classes.FinnhubAPI import FinnhubClient
from classes.YFinanceAPI import YFinanceClient
from utils.generic import mergeDataFrame
from classes.GlobalVariables import *

class DataLoader():

    def __init__(self,symbol):

        # initialize variables
        self.initVariables()

        self.symbol = symbol


    def initVariables(self):
        self._mainFinancialData = None
        self._fullFinancialData = None
        self._finnhubClient = None
        self._yfinanceClient = None
        self._symbol = None

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self,symbol):
        self._symbol = symbol


    @property
    def FinnhubClient(self):
        if self._finnhubClient is None:
            self._finnhubClient = FinnhubClient(self.symbol)

        return self._finnhubClient


    @FinnhubClient.setter
    def FinnhubClient(self,finnhubClient):
        if isinstance(finnhubClient,FinnhubClient):
            self._finnhubClient = finnhubClient
        else:
            raise TypeError('Argument "finnhubClient" must be of type "FinnhubClient". You passed a object of type "' + type(finnhubClient) + '"')


    @property
    def YFinanceClient(self):
        if self._yfinanceClient is None:
            self._yfinanceClient = YFinanceClient(self.symbol)

        return self._yfinanceClient

    @YFinanceClient.setter
    def YFinanceClient(self,yfinanceClient):
        if isinstance(yfinanceClient,YFinanceClient):
            self._yfinanceClient = yfinanceClient
        else:
            raise TypeError('Argument "yfinanceClient" must be of type "YFinanceClient". You passed a object of type "' + type(yfinanceClient) + '"')


    def getFinancialStatements(self):
        # load financial statements from Finnhub
        finnhubFinancialStatements = self.getFinnhubFinancialStatements()
        yfinanceFinancialStatements = self.getYahooFinancialStatements()
        
        # merge data
        df = mergeDataFrame(finnhubFinancialStatements,yfinanceFinancialStatements)
        return df


    def getYahooFinancialStatements(self):
        return self.YFinanceClient.getFinancialStatements()
        

    def getFinnhubFinancialStatements(self):
        allData, mainData = self.FinnhubClient.getFinancialsAsReportedDataFrame()
        return mainData