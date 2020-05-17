import sys, os
import argparse

import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from classes.Stock import Stock
from classes.StockAnalyzer import StockAnalyzer


def analyseStockBySymbol(symbol, growthRateEstimated=None, margin_of_safety=None, discountRate=None):
    # creating a stock object
    stock = Stock(stockSymbol=symbol, growthRateEstimate=growthRateEstimated, margin_of_safety=margin_of_safety, discountRate=discountRate)
    # analyse the stock data
    StockAnalyzer(stock).printBasicAnalysis()


def save_config(arguments):
    if (arguments.discountRate is not None) or (arguments.growthRate is not None) or (arguments.margin_of_safety is not None):
        config = {}
        config["assumptions"] = {}

        if arguments.discountRate is not None:
            config["assumptions"]["discountRate"] = arguments.discount_rate

        if arguments.growthRate is not None:
            growth_year_1_to_5, growth_year_6_to_10, growth_year_10ff = Stock.estimateGrowthRates(arguments.growthRate)
            config["assumptions"]["growth_year_1_to_5"] = growth_year_1_to_5
            config["assumptions"]["growth_year_6_to_10"] = growth_year_6_to_10
            config["assumptions"]["growth_year_10ff"] = growth_year_10ff

        if arguments.margin_of_safety is not None:
            config["assumptions"]["margin_of_safety"] = arguments.margin_of_safety

        with open(symbol + '.json','w') as f:
            r = json.dumps(config)
            f.write(r)


if __name__ == "__main__":
    # Parse the command line arguments
    parser = argparse.ArgumentParser(description='Create a minimum stock analysis by the stocks symbol and some optional estimates')
    parser.add_argument('symbol', metavar='symbol', type=str, help='symbol of the stock')
    parser.add_argument('--growthRate', help='estimated gowth rate for the next 5 years', default=None, type=float)
    parser.add_argument('--discount-rate', help='discount rate for use int the discounted cash flow calculation', default=None, type=float)
    parser.add_argument('--margin-of-safety', help='margin of safety as value in percent', default=None, type=float)
    parser.add_argument('--save-config', action='store_true', help='save the cofiguration in a json-file')
    args = parser.parse_args()
    
    # analyse the stock
    analyseStockBySymbol(symbol=args.symbol, growthRateEstimated=args.growthRate, margin_of_safety=args.margin_of_safety, discountRate=args.discount_rate)

    # Optional: Save the configuration
    if args.save_config:
        save_config(args)
        