from backtrader.indicators import (
    BBands,
    BollingerBands,
    MACD,
    MACDHisto,
    MACDHistogram,
    Envelope,
    Ichimoku,
    ADXR,
    AverageDirectionalMovementIndexRating,
)
import re


# Some indicators contain multiple "lines" instead of just one
# From source code `lines` attribute of the indacator
# https://github.com/mementum/backtrader/tree/master/backtrader/indicators
MULTI_LINE_INDICATORS = [
    (
        AverageDirectionalMovementIndexRating,
        (
            "adx",
            "adxr",
        ),
    ),
    (
        ADXR,
        (
            "adx",
            "adxr",
        ),
    ),
    (
        BollingerBands,
        (
            "mid",
            "top",
            "bot",
        ),
    ),
    (
        BBands,
        (
            "mid",
            "top",
            "bot",
        ),
    ),
    (
        Envelope,
        (
            "top",
            "bot",
        ),
    ),
    (
        MACD,
        (
            "macd",
            "signal",
        ),
    ),
    (
        MACDHistogram,
        (
            "macd",
            "signal",
            "histo",
        ),
    ),
    (
        MACDHisto,
        (
            "macd",
            "signal",
            "histo",
        ),
    ),
    (
        Ichimoku,
        (
            "tenkan_sen",
            "kijun_sen",
            "senkou_span_a",
            "senkou_span_b",
            "chikou_span",
        ),
    ),
]


indicator_regex = re.compile("[a-zA-Z0-9.]+")


def get_indicators_as_dict(strat_run, multi_line_indicators):
    """
    Returns the indicators used for the strategy run
    """

    if multi_line_indicators is not None:
        multi_line_ind = multi_line_indicators
    else:
        multi_line_ind = MULTI_LINE_INDICATORS

    indicators = strat_run.getindicators()
    indicators_dict = dict()
    for i, ind in enumerate(indicators):
        indicator_name = (
            ind.plotlabel() if hasattr(ind, "plotlabel") else "indicator{}".format(i)
        )

        # Check if indicator contains multiple lines
        line_names = get_line_names(ind, multi_line_ind)
        if len(line_names) > 1:
            for lx, line_name in enumerate(line_names):
                key = rename_indicator(indicator_name, line_name)
                indicators_dict[key] = ind.lines[lx].array

        else:
            key = rename_indicator(indicator_name)
            indicators_dict[key] = ind.lines[0].array

    return indicators_dict


def get_line_names(indicator, multi_line_ind):

    for indicator_class, line_names in multi_line_ind:
        # Check the type/class # isinstance doesnt work on subclasses correctly
        if type(indicator) == indicator_class:
            return line_names
    return ()


def rename_indicator(name, line_name=None):
    # Changes the name to <indicator>_<line>_<param1>_<param2>
    tokens = indicator_regex.findall(name)
    if line_name:
        tokens = [tokens[0], line_name] + (tokens[1:] if len(tokens) > 1 else [])
    return "_".join(tokens)
