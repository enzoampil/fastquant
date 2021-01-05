---
id: walk_forward_data_split
title: walk_forward_data_split
---

# Example

To import: `from fastquant.utils.data_split import walk_forward_split`

Example:
Initialize time series with size of 100

## Default Parameters
```
>>> X = np.random.random(100)
>>> for train_indices, test_indices in walk_forward_split(X):
        print("TRAIN:",len(train_indices), train_indices)
        print("TEST: ", len(test_indices) ,test_indices)
        print()
```

```
TRAIN: 57 [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
 48 49 50 51 52 53 54 55 56]
TEST:  15 [57 58 59 60 61 62 63 64 65 66 67 68 69 70 71]

TRAIN: 57 [15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38
 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62
 63 64 65 66 67 68 69 70 71]
TEST:  15 [72 73 74 75 76 77 78 79 80 81 82 83 84 85 86]

TRAIN: 57 [30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77
 78 79 80 81 82 83 84 85 86]
TEST:  13 [87 88 89 90 91 92 93 94 95 96 97 98 99]
```
Gives the output of 3 sets (default is `n_splits=3`) of training and test indices with the proportion of 80:20 proportion (default is `train_size=0.80`) for the training and testing indices


## Specific Training Size and Number of Splits
```
>>> X = np.random.random(100)
>>> for train_indices, test_indices in walk_forward_split(X, train_size=25, n_splits=2):
        print("TRAIN:",len(train_indices), train_indices)
        print("TEST: ", len(test_indices) ,test_indices)
        print()
```

```
TRAIN: 25 [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24]
TEST:  38 [25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48
 49 50 51 52 53 54 55 56 57 58 59 60 61 62]

TRAIN: 25 [38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61
 62]
TEST:  37 [63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86
 87 88 89 90 91 92 93 94 95 96 97 98 99]
```
When `train_size` and `n_splits` are specifed, the size of the test indices will adjust.


## Specific Training and Testing Sizes
```
>>> X = np.random.random(100)
>>> for train_indices, test_indices in walk_forward_split(X, train_size=50, test_size=10):
        print("TRAIN:",len(train_indices), train_indices)
        print("TEST: ", len(test_indices) ,test_indices)
        print()
```

```
TRAIN: 50 [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
 48 49]
TEST:  10 [50 51 52 53 54 55 56 57 58 59]

TRAIN: 50 [10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33
 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57
 58 59]
TEST:  10 [60 61 62 63 64 65 66 67 68 69]

TRAIN: 50 [20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43
 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67
 68 69]
TEST:  10 [70 71 72 73 74 75 76 77 78 79]

TRAIN: 50 [30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77
 78 79]
TEST:  10 [80 81 82 83 84 85 86 87 88 89]

TRAIN: 50 [40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63
 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87
 88 89]
TEST:  10 [90 91 92 93 94 95 96 97 98 99]

```
When `train_size` and `test_size` are specifed, the number of splits (`n_splits`) changes to utilize the entire dataset


## Sliding vs Expanding modes
```
>>> X = np.random.random(100)
>>> for train_indices, test_indices in walk_forward_split(X, mode='expanding'):
        print("TRAIN:",len(train_indices), train_indices)
        print("TEST: ", len(test_indices) ,test_indices)
        print()
```

```
TRAIN: 57 [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
 48 49 50 51 52 53 54 55 56]
TEST:  15 [57 58 59 60 61 62 63 64 65 66 67 68 69 70 71]

TRAIN: 72 [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71]
TEST:  15 [72 73 74 75 76 77 78 79 80 81 82 83 84 85 86]

TRAIN: 87 [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71
 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86]
TEST:  13 [87 88 89 90 91 92 93 94 95 96 97 98 99]
```
When `mode` is set to `expanding`, the training indices will include indices from the previous splits


## Overlap with training data

There may be cases that you might want to some data from training added to the test data. 
In this case, you can set the size of the data which will be added to the test indices

```
>>> X = np.random.random(100)
>>> for train_indices, test_indices in walk_forward_split(X, training_overlap_size=5):
        print("TRAIN:",len(train_indices), train_indices)
        print("TEST: ", len(test_indices) ,test_indices)
        print()
```

```
TRAIN: 57 [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
 48 49 50 51 52 53 54 55 56]
TEST:  20 [52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71]

TRAIN: 57 [15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38
 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62
 63 64 65 66 67 68 69 70 71]
TEST:  20 [67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86]

TRAIN: 57 [30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53
 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77
 78 79 80 81 82 83 84 85 86]
TEST:  18 [82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99]

```
