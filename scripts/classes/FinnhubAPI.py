
import requests
from datetime import datetime
from pandas import DataFrame


class FinnhubClient():

    APIkey = "bq8r88frh5rc96c0kjf0"

    def __init__(self,symbol):
        self.symbol = symbol
        self.getPeerGroup()

    def getData(self):
        print('Open and close data')
        r = requests.get('https://finnhub.io/api/v1/quote?symbol=' + self.symbol + '&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return ''


    def getDividend(self):
        print('Dividend')
        r = requests.get('https://finnhub.io/api/v1/stock/dividend?symbol=' + self.symbol + '&from=2015-04-01&to=2020-04-01&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else: 
            return ''


    def getPeerGroup(self):
        r = requests.get('https://finnhub.io/api/v1/stock/peers?symbol=' + self.symbol + '&token=' + self.APIkey)
        if not r.ok:
            return ''
        else:
            return r.json()

    def getMetricsPerShare(self):
        print('Metrics per share')
        r = requests.get('https://finnhub.io/api/v1/stock/metric?symbol=' + self.symbol + '&metric=perShare&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return ''


    def getRecommendations(self):
        r = requests.get('https://finnhub.io/api/v1/stock/recommendation?symbol=' + self.symbol + '&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return ''

    def getRecommendationsDataFrame(self):
        # get the recommandations 
        recommendations = self.getRecommendations()

        # create an empty data frame
        df = DataFrame()

        # check if the received data is not empty
        if recommendations is not '':

            # add all items to the data frame
            for recommendation in recommendations:
                date = recommendation['period']

                # get all key names exept 'date'
                dataKeys = list(recommendation.keys())
                dataKeys.remove('period')

                for key in dataKeys:
                    df.loc[date,key] = recommendation[key]

        # return the data frame
        return df
