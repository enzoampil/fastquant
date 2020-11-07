#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Jul 29, 2020
@authors: jpdeleon & benjamincabalona1029
"""

from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import scipy.optimize as optimization
from fastquant.data import get_stock_data

TODAY = datetime.now().date().strftime("%Y-%m-%d")


class Portfolio:
    def __init__(
        self,
        stock_list,
        start_date="2015-01-01",
        end_date=TODAY,
        init_weights=None,
        verbose=False,
    ):
        """
        Allows constrained optimization of portfolio consisting of PSE stocks

        Attributes
        ----------
        stock_list : list
            list of stock symbols e.g. ["MBT","JFC","ALI"]
        start_date : str
            starting date of stock data (default="2020-01-01")
        end_date : str
            ending date of stock data (default is date today)
        init_weights : list
            list of initial weights for each stock in portfolio
        """
        self.stock_list = stock_list
        self.start_date = start_date
        self.end_date = end_date
        self.verbose = verbose
        self.data = self.get_data()
        self.returns = self.data.pct_change()
        if init_weights is None:
            self.random_weights = np.random.random(len(stock_list))
        else:
            assert len(init_weights) == len(stock_list)
            self.random_weights = init_weights
        self.optimum_weights = None
        self.optimum = self.optimize_portfolio()

    def get_data(self):
        dfs = []
        for i in self.stock_list:
            df = get_stock_data(i, self.start_date, self.end_date, format="c")
            df.columns = [i]
            dfs.append(df)
        data = pd.concat(dfs, axis=1)
        data.index.name = "DATE"
        return data

    def calculate_portfolio_returns(self, weights):
        # annualization of returns = 252
        portfolio_returns = np.sum(self.returns.mean() * weights) * 252
        if self.verbose:
            print("Expected Portfolio Return:", portfolio_returns)
        return portfolio_returns

    def calculate_portfolio_risk(self, weights):
        # variance = risk or volatility
        portfolio_risk = np.sqrt(
            np.dot(weights.T, np.dot(self.returns.cov() * 252, weights))
        )
        if self.verbose:
            print("Expected Risk:", portfolio_risk)
        return portfolio_risk

    def generate_portfolios(self, N=10000):
        preturns = []
        pvariances = []
        for _ in range(N):
            weights = np.random.random(len(self.stock_list))
            weights /= np.sum(weights)
            preturns.append(self.calculate_portfolio_returns(weights))
            pvariances.append(self.calculate_portfolio_risk(weights))
        return np.array(preturns), np.array(pvariances)

    def calculate_statistics(self, weights):
        portfolio_return = self.calculate_portfolio_returns(weights)
        portfolio_risk = self.calculate_portfolio_risk(weights)
        sharpe_ratio = portfolio_return / portfolio_risk
        return [portfolio_return, portfolio_risk, sharpe_ratio]

    def min_func_sharpe(self, weights):
        # we want to maximize sharpe ratio = minimize the negative of it
        return -self.calculate_statistics(weights)[2]

    def optimize_portfolio(self):
        constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in range(len(self.stock_list)))
        init_weights = (
            self.random_weights
            if self.optimum_weights is None
            else self.optimum_weights
        )
        optimum = optimization.minimize(
            fun=self.min_func_sharpe,
            x0=init_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if optimum.success:
            self.optimum_weights = optimum["x"].round(3)
            self.print_optimal_portfolio()
            return optimum
        else:
            print("Optimization failed. Try different init_weights.")

    def print_optimal_portfolio(self):
        print("Optimal weights:", self.optimum_weights)
        print(
            "Expected return, volatility and Sharpe ratio:",
            self.calculate_statistics(self.optimum_weights),
        )

    def plot_portfolio(self, optimal=True, **kwargs):
        fig = plt.figure(figsize=(10, 6))
        preturns, pvariances = self.generate_portfolios(**kwargs)
        plt.scatter(pvariances, preturns, c=preturns / pvariances, marker="o")
        plt.grid(True)
        plt.xlabel("Expected Volatility")
        plt.ylabel("Expected Return")
        plt.colorbar(label="Sharpe Ratio")
        if optimal:
            stats = self.calculate_statistics(self.optimum_weights)
            plt.plot(stats[1], stats[0], "r*", markersize=20.0)
        return fig
