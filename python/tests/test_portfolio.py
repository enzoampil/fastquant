# import inspect
# from matplotlib.figure import Figure
# from matplotlib.axes import Axes
# from fastquant import Portfolio

# stock_list = ["MEG", "MAXS", "JFC", "ALI"]


# def test_portfolio_init():
#     global p
#     p = Portfolio(stock_list)
#     # assert inspect.isclass(p)


# def test_portfolio_data_query():
#     axs = p.data.plot(subplots=True, figsize=(15, 10))
#     assert isinstance(axs[0], Axes)


# def test_optimization():
#     fig = p.plot_portfolio(N=1000)
#     assert isinstance(fig, Figure)
