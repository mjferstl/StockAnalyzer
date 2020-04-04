# extensions for the module "yfinance", because it does not have the ability to load all necessary data

# import modules
import requests as _requests
import json as _json
import pandas as _pd
from datetime import datetime


# Function to get the annualDilutedEPS from yahoo finance
def get_annualDilutedEPS(symbol):

    url = "https://finance.yahoo.com/quote/" + symbol + "/financials"

    data = {}
    html = _requests.get(url=url).text

    json_str = html.split('root.App.main =')[1].split(
        '(this)')[0].split(';\n}')[0].strip()
    
    if "QuoteTimeSeries" in html:
        annualDilutedEPSlist = _json.loads(json_str)[
            'context']['dispatcher']['stores']['QuoteTimeSeriesStore']['timeSeries']['annualDilutedEPS']
        #print(annualDilutedEPSlist)
        for eps in annualDilutedEPSlist:
            if eps is not None:
                data[eps['asOfDate']] = eps['reportedValue']['raw']

    df = _pd.DataFrame(columns=list(data.keys()))
    df.loc['dilutedEPS'] = [d for d in data.values()]

    return df