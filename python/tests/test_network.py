from matplotlib.figure import Figure
import pandas as pd
from fastquant import Network

nw = Network(symbol="JFC", start_date="2020-01-01", end_date="2020-04-01", metric="b")


def test_network_init():
    assert isinstance(nw.price_corr, pd.DataFrame)


def test_network_plots():
    fig = nw.plot_network()
    assert isinstance(fig, Figure)

    fig = nw.plot_corr_company()
    assert isinstance(fig, Figure)
