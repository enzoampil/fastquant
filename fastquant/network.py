#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28, 2020

@author: jpdeleon
"""
# Import standard library
import itertools
from datetime import datetime
from pathlib import Path

# Import modules
import matplotlib.pyplot as pl
import numpy as np
import pandas as pd
import networkx as nx

# Import from package
from fastquant import get_pse_data_cache, DATA_PATH

pl.style.use("fivethirtyeight")
CALENDAR_FORMAT = "%m-%d-%Y"
TODAY = datetime.now().date().strftime(CALENDAR_FORMAT)

__all__ = ["Network"]


class Network:
    """
    Parameters
    ----------
    symbol : str
        phisix company symbol (optional)
    metric : str
            distance metrics:
            bonnano=distinguishes between a + or a - correlated pair of stocks;
            bonnano=does not distinguish
    n_companies : str
        top n companies correlated to symbol to consider
    """

    def __init__(
        self,
        symbol=None,
        start_date="1-1-2020",
        end_date=None,
        metric="bonnano",
        n_companies=5,
        verbose=True,
        clobber=False,
        update_cache=False,
    ):
        self.symbol = None if symbol is None else symbol.upper()
        self.start_date = start_date
        self.end_date = TODAY if end_date is None else end_date
        self.stock_data = None
        self.verbose = verbose
        self.clobber = clobber
        self.n_companies = n_companies
        self.update_cache = update_cache
        self.data_cache = get_pse_data_cache(
            update=self.update_cache, verbose=False
        )
        self.company_table = self.load_company_table()
        self.price_corr = self.compute_corr()
        self.metric = metric.lower()
        self.dist, self.labs = self.build_distance_matrix()
        self.MST = self.build_minimum_spanning_tree()
        self.populate_graph_attribute()

    def load_company_table(self):
        fp = Path(DATA_PATH, "stock_table.csv")
        table = pd.read_csv(fp)
        self.company_table = table
        return table

    def compute_corr(
        self,
        symbol=None,
        n_companies=None,
        start_date=None,
        end_date=None,
        data_type="close",
    ):
        """
        symbol : str
            company symbol
        n_companies : int
            top n postively and bottom n negatively correlated companies to symbol
        """
        symbol = self.symbol if symbol is None else symbol
        n_companies = self.n_companies if n_companies is None else n_companies

        start_date = self.start_date if start_date is None else start_date
        end_date = self.end_date if end_date is None else end_date

        df = self.data_cache
        # filter date
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        # choose only close column
        df = df.xs(data_type, level=1, axis=1)
        # remove columns with NaNs
        df.dropna(axis=1, inplace=True)
        # compute correlation
        if symbol is not None:
            rank = df.corr()[symbol].sort_values(ascending=True)
            top = rank.tail(n_companies)
            top = list(top.index)
            bottom = rank.head(n_companies)
            bottom = list(bottom.index)
            chosen = list(itertools.chain.from_iterable([top, bottom]))
            idx = df.corr().index.isin(chosen)
            price_corr = df.corr().loc[idx, chosen]
        else:
            price_corr = df.corr()
        return price_corr

    def build_distance_matrix(self, metric=None):
        """
        metric : str
            bonnano=distinguishes between a + or a - correlated pair of stocks;
            bonnano=does not distinguish
        """
        metric = self.metric if metric is None else metric.lower()

        if (metric == "bonnano") | (metric == "b"):
            dist = np.sqrt(2 * (1 - self.price_corr))
            labs = list(dist.index)
        elif (metric == "mktstk") | (metric == "m"):
            dist = 1 - abs(self.price_corr)
            labs = list(dist.index)
        else:
            raise ValueError("Use bonnano or mktstk")
        return dist, labs

    def build_minimum_spanning_tree(self, dist=None):
        """"""
        dist = self.dist if dist is None else dist

        G = nx.from_numpy_matrix(dist.values)
        MST = nx.minimum_spanning_tree(G)
        return MST

    def plot_corr_matrix(self, figsize=(10, 10)):
        """"""
        try:
            import seaborn as sb
        except Exception:
            raise ModuleNotFoundError("pip install seaborn")

        ## Generate a mask for the upper triangle
        mask = np.zeros_like(self.price_corr, dtype=np.bool)
        mask[np.triu_indices_from(mask)] = True

        ## Set up the matplotlib figure
        fig, ax = pl.subplots(figsize=figsize)

        ## Generate a custom diverging colormap
        # cmap = sb.diverging_palette(220, 10, as_cmap=True)

        ## Draw the heatmap with the mask and correct aspect ratio
        fig = sb.heatmap(
            self.price_corr,
            mask=mask,
            vmax=0.3,  # cmap=cmap,
            square=True,
            xticklabels=2,
            yticklabels=2,
            linewidths=0.5,
            cbar_kws={"shrink": 0.5},
            ax=ax,
        )
        return fig

    def plot_corr_company(
        self,
        symbol=None,
        symbol2=None,
        positive=True,
        rescale=True,
        data_type="close",
    ):
        """
        plot company with highest positive/negative correlation with symbol
        """
        symbol = self.symbol if symbol is None else symbol
        assert symbol is not None, "Provide symbol"

        df = self.data_cache
        # filter date
        df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
        # choose only close column
        df = df.xs(data_type, level=1, axis=1)
        # remove columns with NaNs
        df.dropna(axis=1, inplace=True)

        rank = self.price_corr[symbol].sort_values(ascending=True)

        fig, ax = pl.subplots(1, 2, figsize=(10, 5))

        if positive:
            # positively correlated
            if symbol2 is None:
                symbol2 = (
                    rank.index[-2]
                    if rank.index[-1] == symbol
                    else rank.index[-1]
                )
        else:
            # negatively correlated
            if symbol2 is None:
                symbol2 = rank.index[0]

        if rescale:
            d1 = df[symbol] / df[symbol].max()
            d2 = df[symbol2] / df[symbol2].max()
            _ = d1.plot(ax=ax[0], label=symbol)
            d2.apply(lambda x: x).plot(ax=ax[0], label=symbol2)
        else:
            _ = df[symbol].plot(ax=ax[0], label=symbol)
            df[symbol2].plot(ax=ax[0], label=symbol2)
        pl.setp(ax[0], ylabel="rescaled {} price".format(data_type))
        ax[0].legend()

        ax[1].plot(df[symbol], df[symbol2], "o")
        label = " {} price".format(data_type)
        pl.setp(ax[1], xlabel=symbol + label, ylabel=symbol2 + label)
        return fig

    def map_sector_to_color(self, MST, dtype="int"):
        """"""
        sector_dict = nx.get_node_attributes(MST, "sector")
        sectors = pd.Series(sector_dict)
        codes = sectors.astype("category").cat.codes
        if dtype == "int":
            return codes.values
        elif dtype == "cint":
            return ["C" + str(n) for n in codes.values]
        elif dtype == "str":
            return sectors.values
        elif dtype == "cat":
            # {int: str} mapping
            d = dict(enumerate(sectors.astype("category").cat.categories))
            # {str: int} mapping (reverse)
            d = {v: k for k, v in d.items()}
            return d

    def populate_graph_attribute(self):
        """"""
        for node in self.MST.nodes():
            sector = self.company_table[
                self.company_table["Stock Symbol"] == self.labs[node]
            ].Sector.iloc[0]
            self.MST.nodes[node]["sector"] = sector
            self.MST.nodes[node]["label"] = self.labs[node]
        return None

    def plot_network(
        self, MST=None, iterations=50, figsize=(10, 10)  # cmap="Set1",
    ):
        """
        Note: each instance may show different network structure
        """
        MST = self.MST if MST is None else MST

        fig = pl.figure(figsize=figsize, constrained_layout=True)

        nx.draw_networkx(
            MST,
            pos=nx.spring_layout(MST, iterations=iterations),
            labels=nx.get_node_attributes(MST, "label"),
            node_color=self.map_sector_to_color(MST, dtype="cint"),
            # cmap=pl.get_cmap(cmap),
            font_color="k",
        )
        # hack legend
        ColorLegend = self.map_sector_to_color(MST, dtype="cat")
        # values = self.map_sector_to_color(MST, dtype='int')
        # cNorm  = mpl.colors.Normalize(vmin=0, vmax=max(values))
        # scalarMap = mpl.cm.ScalarMappable(norm=cNorm, cmap=pl.get_cmap(cmap))
        for label in ColorLegend:
            pl.plot(
                [0],
                [0],
                "o",
                color="C{}".format(ColorLegend[label]),
                # color=scalarMap.to_rgba(ColorLegend[label]),
                label=label,
            )
        # fig.set_facecolor('w')
        pl.legend()
        return fig


if __name__ == "__main__":
    n = Network()
    # n = Network(symbol='JFC')
    fig = n.plot_network()
    pl.show()
