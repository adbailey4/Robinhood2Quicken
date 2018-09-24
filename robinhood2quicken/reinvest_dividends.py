#!/usr/bin/env python
"""Reinvest dividends into the stock which paid the dividend"""
########################################################################
# File: reinvest_dividends.py
#  executable: reinvest_dividends.py
#
# Author: Andrew Bailey
# History: Created 08/15/18
########################################################################

import sys
import os
import csv
import argparse
import numpy as np
from timeit import default_timer as timer
from datetime import datetime
from Robinhood import Robinhood
from robinhood2quicken.export_mint_csv import get_robinhood_dividend_data

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
