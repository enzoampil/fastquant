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
from fastquant.data import get_pse_data_cache
from fastquant.config import DATA_PATH, CALENDAR_FORMAT

TODAY = datetime.now().date().strftime(CALENDAR_FORMAT)

__all__ = ["Network"]


class Network:
    """
    Parameters
    ----------
    symbol : str
        phisix company symbol (optional)
    sector : str
        specific sector
    sigma : float
        outlier rejection threshold (default=None)
    metric : str
            distance metrics:
            bonnano=distinguishes between a + or a - correlated pair of stocks;
            bonnano=does not distinguish
    n_companies : str
        limit to top n companies correlated to symbol (if symbol is given)
    """

    def __init__(
        self,
        symbol=None,
        sector=None,
        start_date="1-1-2020",
        end_date=None,
        metric="bonnano",
        n_companies=5,
        sigma=5,
        exclude_symbols=None,
        interpolation_method="pad",
        indicator="close",
        verbose=True,
        clobber=False,
        update_cache=False,
    ):
        self.symbol = None if symbol is None else symbol.upper()
        self.sector = sector
        self.start_date = start_date
        self.end_date = TODAY if end_date is None else end_date
        self.stock_data = None
        self.verbose = verbose
        self.clobber = clobber
        self.sigma = sigma
        self.exclude_symbols = exclude_symbols
        self.indicator = indicator
        self.interpolation_method = interpolation_method
        self.n_companies = n_companies
        self.update_cache = update_cache
        self.data_cache = get_pse_data_cache(update=self.update_cache, verbose=False)
        self.data = self.data_cache.xs(indicator, level=1, axis=1)
        self.filtered_data = self.filter_data()
        self.company_table = self.load_company_table()
        self.all_sectors = self.company_table.Sector.unique().tolist()
        self.all_subsectors = self.company_table.Subsector.unique().tolist()
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

    def get_sector_of_symbol(self, symbol):
        """get sector or subsector where symbol belongs"""
        info = self.company_table.copy()
        sector = info.loc[info["Stock Symbol"].isin([symbol]), "Sector"].values[0]
        return sector

    def get_symbols_of_a_sector(self, sector, subsector=False, verbose=False):
        """get symbols of members in the sector"""
        info = self.company_table.copy()
        column = "Subsector" if subsector else "Sector"
        sectors_dict = info[["Stock Symbol", column]].groupby(column).groups

        sector_indices = sectors_dict[sector]
        sector_symbols = info.loc[sector_indices, "Stock Symbol"]
        data_availability_indices = self.filtered_data.columns.isin(sector_symbols)
        symbols_with_data = self.filtered_data.columns[
            data_availability_indices
        ].tolist()
        symbols_without_data = sector_symbols[
            ~sector_symbols.isin(symbols_with_data)
        ].tolist()
        if verbose:
            print(
                "Symbols without data in {}:\n{}".format(sector, symbols_without_data)
            )
        return symbols_with_data

    def detrend_data(
        self, df=None, window=5, symbol=None, plot=False, return_trend=False
    ):
        """detrend by dividing its rolling median (robust to outliers)
        Returns flattened (and detrended) data
        """
        if df is None:
            df = self.data.copy()
        # min_periods=1 does not yield NaN
        df_rolling = df.rolling(window=window, min_periods=1).median()

        if plot:
            assert symbol is not None
            label = "rolling mean (w={})".format(window)
            ax = df[symbol].plot(label=symbol)
            df.df_rolling[symbol].plot(ax=ax, label=label)
            ax.legend()
        if return_trend:
            return df / df_rolling, df_rolling
        else:
            return df / df_rolling

    def remove_outliers(self, df=None, sigma=None):
        """remove data sigma away from the mean of pct_change"""
        sigma = self.sigma if sigma is None else sigma

        if df is None:
            df = self.data.copy()
        # df2 = self.detrend_data(df)
        # #idx = (np.abs(stats.zscore(df)) < 3).all(axis=1)
        # idx = df2.apply(lambda x, sigma: abs(x - x.mean()) / x.std() < sigma, sigma=sigma).all(axis=1)
        idx = (df.pct_change() / df.pct_change().std()) < sigma
        symbols_half_original_data = idx.sum() < len(df) // 2
        if symbols_half_original_data.any():
            columns = df.columns[symbols_half_original_data].values
            errmsg = "{}: removed since <1/2 of original data is left after outlier rejection".format(
                columns
            )
            if self.verbose:
                print(errmsg)
            if symbols_half_original_data.sum() > len(df) // 2:
                errmsg = "Less than half of original data is removed"
                raise ValueError(errmsg)
            return df.drop(columns=columns, axis=1)
        else:
            return df[idx]

    def filter_data(
        self,
        df=None,
        symbol=None,
        sector=None,
        sigma=None,
        method=None,
        n_companies=None,
        start_date=None,
        end_date=None,
        indicator="close",
    ):
        """
        extreme outliers are filled as NaN
        """
        symbol = self.symbol if symbol is None else symbol
        sector = self.sector if sector is None else sector
        sigma = self.sigma if sigma is None else sigma
        method = self.interpolation_method if method is None else method
        n_companies = self.n_companies if n_companies is None else n_companies
        start_date = self.start_date if start_date is None else start_date
        end_date = self.end_date if end_date is None else end_date

        if df is None:
            df = self.data_cache.copy()
            # filter date
            df = df[(df.index >= start_date) & (df.index <= end_date)]
            # choose 1 technical indicator
            df = df.xs(self.indicator, level=1, axis=1)
            # remove columns with all NaNs
            df.dropna(how="all", axis=1, inplace=True)
            if self.exclude_symbols is not None:
                idx = df.columns.isin(self.exclude_symbols)
                if self.verbose:
                    print("Removed: {}".format(df.columns[idx].values))
                df = df.loc[:, df.columns[~idx]]
            # update
            self.data = df
        # remove outliers
        if sigma is not None:
            df = self.remove_outliers(df, sigma=sigma)
        # replace some few remaining NaNs with interpolated values
        df.interpolate(method=method, limit=5, inplace=True)
        # remove columns with any remaining NaNs
        # df.dropna(how="any", axis=1, inplace=True)
        return df

    def compute_corr(
        self,
        symbol=None,
        sector=None,
        sigma=None,
        n_companies=None,
        start_date=None,
        end_date=None,
        indicator="close",
    ):
        """
        symbol : str
            company symbol
        n_companies : int
            top n postively and bottom n negatively correlated companies to symbol
        """
        symbol = self.symbol if symbol is None else symbol
        sector = self.sector if sector is None else sector
        sigma = self.sigma if sigma is None else sigma
        n_companies = self.n_companies if n_companies is None else n_companies

        start_date = self.start_date if start_date is None else start_date
        end_date = self.end_date if end_date is None else end_date

        df = self.filtered_data.copy()
        if sector is not None:
            symbols = self.get_symbols_of_a_sector(sector)
            columns = df.columns[df.columns.isin(symbols)]
            df = df.loc[:, columns]

        # remove outliers
        if sigma is not None:
            df = self.remove_outliers(df, sigma=sigma)

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

        G = nx.from_numpy_array(dist.values)
        MST = nx.minimum_spanning_tree(G)
        return MST

    def plot_corr_matrix(self, symbols=None, sector=None, figsize=(10, 10)):
        """"""
        try:
            import seaborn as sb
        except Exception:
            raise ModuleNotFoundError("pip install seaborn")
        sector = self.sector if sector is None else sector

        if symbols is not None:
            errmsg = "symbols should be a list of PSE symbols"
            assert isinstance(symbols, list), errmsg
            price_corr = self.price_corr.loc[symbols, symbols]
        elif sector is not None:
            errmsg = "sector not available"
            assert sector in self.all_sectors, errmsg
            symbols = self.get_symbols_of_a_sector(sector)
            price_corr = self.price_corr.loc[symbols, symbols]
        else:
            price_corr = self.price_corr

        ## Generate a mask for the upper triangle
        mask = np.zeros_like(price_corr, dtype=np.bool)
        mask[np.triu_indices_from(mask)] = True

        ## Set up the matplotlib figure
        fig, ax = pl.subplots(1, 1, figsize=figsize)

        ## Generate a custom diverging colormap
        # cmap = sb.diverging_palette(220, 10, as_cmap=True)

        ## Draw the heatmap with the mask and correct aspect ratio
        fig = sb.heatmap(
            price_corr,
            mask=mask,
            vmax=0.3,  # cmap=cmap,
            square=True,
            xticklabels=2,
            yticklabels=2,
            linewidths=0.5,
            cbar_kws={"shrink": 0.5, "label": "correlation"},
            ax=ax,
        )
        return fig

    def plot_corr_company(
        self,
        symbol=None,
        symbol2=None,
        positive=True,
        rescale=True,
        indicator="close",
    ):
        """
        plot company with highest positive/negative correlation with symbol
        """
        symbol = self.symbol if symbol is None else symbol
        assert symbol is not None, "Provide symbol"

        df = self.filtered_data.copy()

        rank = self.price_corr[symbol].sort_values(ascending=True)

        fig, ax = pl.subplots(1, 2, figsize=(10, 5))

        if positive:
            # positively correlated
            if symbol2 is None:
                symbol2 = rank.index[-2] if rank.index[-1] == symbol else rank.index[-1]

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
        pl.setp(ax[0], ylabel="rescaled {} price".format(indicator))
        ax[0].legend()

        ax[1].plot(df[symbol], df[symbol2], "o")
        label = " {} price".format(indicator)
        pl.setp(ax[1], xlabel=symbol + label, ylabel=symbol2 + label)
        return fig

    def map_sector_to_color(self, MST, dtype="int", use_subsector=False):
        """"""
        grouping = "subsector" if use_subsector else "sector"

        sector_dict = nx.get_node_attributes(MST, grouping)
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
            subsector = self.company_table[
                self.company_table["Stock Symbol"] == self.labs[node]
            ].Subsector.iloc[0]
            self.MST.nodes[node]["subsector"] = subsector
            self.MST.nodes[node]["label"] = self.labs[node]
        return None

    def plot_network(
        self,
        MST=None,
        show_subsector=False,
        iterations=50,
        figsize=(10, 10),  # cmap="Set1",
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
            node_color=self.map_sector_to_color(
                MST, use_subsector=show_subsector, dtype="cint"
            ),
            # cmap=pl.get_cmap(cmap),
            font_color="k",
        )
        # hack legend
        ColorLegend = self.map_sector_to_color(
            MST, use_subsector=show_subsector, dtype="cat"
        )
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
        if len(ColorLegend) > 1:
            if show_subsector or (self.symbol is not None):
                pl.legend(title="Sub-sector" if show_subsector else "Sector")
        if self.sector is not None:
            fig.suptitle("{} Sector".format(self.sector), y=1.01)
        return fig


if __name__ == "__main__":
    n = Network()
    # n = Network(symbol='JFC')
    fig = n.plot_network()
    pl.show()
