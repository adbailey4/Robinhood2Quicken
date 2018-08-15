#!/usr/bin/env python
"""Create setup script for pip installation"""
########################################################################
# File: export_mint_csv.py
#  executable: export_mint_csv.py
#
# Author: Andrew Bailey
# History: Created 08/12/18
########################################################################

import sys
import os
import csv
import argparse
import numpy as np
from timeit import default_timer as timer
from datetime import datetime
from Robinhood import Robinhood

MINT_HEADERS = ("Date", "Description Original", "Description", "Amount", "Transaction Type", "Category", "Account Name",
                "Labels", "Notes")


class CommandLine(object):
    """
    Handle the command line, usage and help requests.

    attributes:
    myCommandLine.args is a dictionary which includes each of the available
    command line arguments as myCommandLine.args['option']

    methods:
    do_usage_and_die(message): prints usage and help and terminates with an error.

    """

    def __init__(self, in_opts=None):
        """CommandLine constructor.

        Implements a parser to interpret the command line argv string using
        argparse.
        """
        # define program description, usage and epilog
        self.parser = argparse.ArgumentParser(description='Export Robinhood trades to a Mint CSV file which can be '
                                                          'imported into Quicken',
                                              usage='%(prog)s use "-h" for help')

        # get username and password
        self.parser.add_argument('--username', help='your Robinhood username', required=True)
        self.parser.add_argument('--password', help='your Robinhood password', required=True)
        self.parser.add_argument('--trades', help='return trade information', required=False, default=True)
        self.parser.add_argument('--dividends', help='returns dividend information', required=False, default=True)
        self.parser.add_argument('--date', help='filters to transactions after specific date: MM/DD/YYYY',
                                 required=False, default=False)
        self.parser.add_argument('--output', help='output file path. Must include .csv at the end of the file name',
                                 required=False, default=False)

        # allow optional arguments not passed by the command line
        if in_opts is None:
            self.args = vars(self.parser.parse_args())
        elif type(in_opts) is list:
            self.args = vars(self.parser.parse_args(in_opts))
        else:
            self.args = in_opts

    def do_usage_and_die(self, message):
        """ Print string and usage then return 2

        If a critical error is encountered, where it is suspected that the
        program is not being called with consistent parameters or data, this
        method will write out an error string (str), then terminate execution
        of the program.
        """
        print(message, file=sys.stderr)
        self.parser.print_help(file=sys.stderr)
        return 2


def get_robinhood_trade_data(robinhood_api):
    """Export trade and/or dividend information into the same format as Mint exported csv's
    :param robinhood_api: an already logged in Robinhood class
    """
    orders = robinhood_api.order_history()["results"]
    trade_data = []
    for order in orders:
        ticker = robinhood_api.get_custom_endpoint(order['instrument'])['symbol']
        print(ticker)
        if len(order["executions"]) > 0:
            side = order['side']
            quantity = order["executions"][0]['quantity']
            price = order['executions'][0]['price']
            timestamp = order['executions'][0]['timestamp'].split("T")[0]
            data = dict(ticker=ticker, side=side, quantity=quantity,
                        price=price, Date=timestamp, cost=float(price)*float(quantity))
            trade_data.append(data)

    return trade_data


def get_robinhood_dividend_data(robinhood_api):
    """Export trade and/or dividend information into the same format as Mint exported csv's
    :param robinhood_api: an already logged in Robinhood class
    """
    dividend_data = []
    dividends = robinhood_api.dividends()["results"]
    for dividend in dividends:

        paid_at = dividend["paid_at"]
        if paid_at:
            amount = dividend["amount"]
            payable_date = dividend["payable_date"]
            ticker = robinhood_api.get_custom_endpoint(dividend['instrument'])['symbol']
            data = dict(amount=amount, Date=payable_date, ticker=ticker)
            dividend_data.append(data)

    return dividend_data


def parse_robinhood_data_to_mint(trade_data, dividend_data):
    """Convert trade data and dividend data into mint output format
    :param trade_data: list of dictionaries with trade data via the get_robinhood_trade_data function
    :param dividend_data: list of dictionaries with dividend data via the get_robinhood_dividend_data function
    :return: reformatted data for mint export
    """
    mint_data = []
    if trade_data:
        # 5/18/2017,Investments:Dividend Income,Investments:Dividend Income,5.04,credit,Apple Inc,,,

        for line in trade_data:
            mint_data.append({"Date": convert_robinhood_date(line["Date"]),
                              "Description Original": line["ticker"],
                              "Description": "Investments:{}".format(line["side"]),
                              "Amount": np.round(float(line["cost"]), 2),
                              "Transaction Type": "credit",
                              "Category": line["side"],
                              "Account Name": None,
                              "Labels": line["quantity"],
                              "Notes": line["price"]})
    if dividend_data:
        for line in dividend_data:
            mint_data.append({"Date": convert_robinhood_date(line["Date"]),
                              "Description Original": line["ticker"],
                              "Description": "Investments:Dividend Income",
                              "Amount": np.round(float(line["amount"]), 2),
                              "Transaction Type": "credit",
                              "Category": None,
                              "Account Name": None,
                              "Labels": None,
                              "Notes": None})

    return mint_data


def convert_robinhood_date(robinhood_date):
    """Convert date from YYYY-MM-DD format to MM/DD/YYYY
    :param robinhood_date: string with YYYY-MM-DD format
    """
    new_date = robinhood_date.split("-")
    return '/'.join([new_date[1], new_date[2], new_date[0]])


def write_csv(header, data, output_path):
    """Write a csv with a given header and the corresponding data
    :param header: list of strings for header names
    :param data: list of dictionaries where each dictionary has corresponding keys as the header
    """
    assert os.path.splitext(output_path)[1] == ".csv", "Outpath must end with the .csv extension"
    # assert set(header) == set(data[0].keys()), \
    #     "The shape of data does not match the number of headers: {} != {}".format(len(header), len(data[0]))

    with open('{}'.format(output_path), 'w', newline='') as csvfile:
        # print(','.join(header), file=csvfile)
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        for row in data:
            # print(','.join(row), file=csvfile)
            writer.writerow(row)

    return output_path


def filter_by_date(date, data, key="Date"):
    """Filter transaction/dividend data by specific date
    :param date: MM/DD/YYYY formatted date
    :param data: list of dictionaries. must have key in each dictionary
    :param key: key for dictionary in data to compare with date
    :return: filtered data
    """
    filtered_data = []
    m, d, y = date.split("/")
    filter_day = datetime(int(y), int(m), int(d))
    for transaction in data:
        m, d, y = transaction[key].split("/")
        transaction_day = datetime(int(y), int(m), int(d))
        if transaction_day > filter_day:
            filtered_data.append(transaction)

    return filtered_data


def main():
    """Main docstring"""
    start = timer()

    dividend_data = None
    trade_data = None

    command_line = CommandLine()
    robinhood_api_handle = Robinhood()
    logged_in = robinhood_api_handle.login(username=command_line.args["username"],
                                           password=command_line.args["password"])
    # log in
    if not logged_in:
        command_line.do_usage_and_die("Username or Password is incorrect")

    # decide to grab dividends and/or trades
    if command_line.args["dividends"]:
        dividend_data = get_robinhood_dividend_data(robinhood_api_handle)

    if command_line.args["trades"]:
        trade_data = get_robinhood_trade_data(robinhood_api_handle)

    # convert into mint format
    mint_data = parse_robinhood_data_to_mint(trade_data, dividend_data)

    # if passed filter by date
    if command_line.args["date"]:
        mint_data = filter_by_date(command_line.args["date"], mint_data)

    # if output is passed, use the path as the output file
    if command_line.args["output"]:
        write_csv(MINT_HEADERS, mint_data, command_line.args["output"])
    else:
        write_csv(MINT_HEADERS, mint_data, "robinhood_output.csv")

    # keep track of how long everything takes
    stop = timer()
    print("export_mint_csv.py took {} seconds".format(stop - start), file=sys.stderr)


if __name__ == "__main__":
    main()
    raise SystemExit
