import math
import numpy as np
from sklearn.utils.validation import _num_samples


def walk_forward_split(
    X,
    train_size=0.80,
    test_size=None,
    n_splits=3,
    mode="sliding",
    training_overlap_size=0,
):
    """
    Split the time series data into multiple sets(or "splits") of training/optimization indices and testing indices.
    Each split contains training indices and test indices that are sequential.
    This is based on sckit-learn's `sklearn.model_selection.TimeSeriesSplit` module.

    Usage can be:
    - Fixed input size, fixed test size
    >>> walk_forward_split(X, train_size=20, test_size=20)

    - Fized input size, fixed number of splits
    >>> for train_index, test_index in walk_forward_split(X, train_size=20, n_splits=3)

    - Training size proportion, fixed number of splits
    >>> walk_forward_split(X, train_size=0.5, n_splits=3)

    Parameters
    -----
    X : array-like of shape (n_samples, n_features)
    train_size : float or int
        Minimum samples for the training data, if float is given, it will set the ratio between training size and testing size.
        When train_size is an integer, either n_splits or test_size is required
    test_size : int (default: None)
        Number of samples in test data. Ignored if train_size is float
    n_splits: int (default : 3)
        Number of splits to generate. Ignored if number of training data and testing data is specified
    mode : str {"sliding", "expanding"} (default : "sliding")
        Whether the training data size is fixed ("sliding") or the training data always starts at the begining ("expanding")
    training_overlap_size : int, (default:0)
        Number of items from the training indices to add to the test indices. This is unaffected by the `test_size` parameter.
        Note that increasing the data added from the training data to the test data increases data leakage.

    Returns
    -------
    train_ix, test_ix : tuple (generator)
        indices of the training data and the testing data

    Example

    >>> X = np.arange(100)
    >>> for train_index, test_index in walk_forward_split(X, train_size=20, test_size=20,mode='expanding'):
        print("\nTRAIN:",train_index.shape, train_index, "\nTEST: ", test_index.shape ,test_index)
    ```
    TRAIN: (20,) [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19]
    TEST:  (20,) [20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39]

    TRAIN: (40,) [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
    24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39]
    TEST:  (20,) [40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59]

    TRAIN: (60,) [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
    24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
    48 49 50 51 52 53 54 55 56 57 58 59]
    TEST:  (20,) [60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79]

    TRAIN: (80,) [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
    24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
    48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71
    72 73 74 75 76 77 78 79]
    TEST:  (20,) [80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99]

    """
    n_samples = _num_samples(X)
    indices = np.arange(n_samples)

    if type(train_size) == float and n_splits is not None:

        # Determine number of folds based on train_size and n_split
        window_folds = (
            max(train_size, 1 - train_size) // min(train_size, 1 - train_size)
        ) + 1
        test_folds = window_folds * (1 - train_size)
        train_folds = window_folds - test_folds
        total_folds = train_folds + test_folds * n_splits

        fold_size = n_samples / total_folds  # size of the fold wrt n_samples
        window_size = math.ceil(fold_size * window_folds)

        train_size = int(train_size * window_size)
        test_size = window_size - train_size

    if test_size is None and type(train_size) != float:
        test_size = math.ceil((n_samples - train_size) / n_splits)

    if test_size < 1 or train_size < 1:
        raise ValueError("Not enough data. Adjust training size or n_split")

    for test_start in range(train_size, n_samples, test_size):
        if mode == "sliding":
            train_ix = indices[test_start - train_size : test_start]
            test_ix = indices[
                test_start - training_overlap_size : test_start + test_size
            ]
        elif mode == "expanding":
            train_ix = indices[:test_start]
            test_ix = indices[
                test_start - training_overlap_size : test_start + test_size
            ]

        yield train_ix, test_ix
