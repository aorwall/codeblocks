

## EpicSplitter

16 chunks

#### Split 1
151 tokens, line: 1 - 25

```python
"""Spectral biclustering algorithms."""

from abc import ABCMeta, abstractmethod

import numpy as np
from numbers import Integral

from scipy.linalg import norm
from scipy.sparse import dia_matrix, issparse
from scipy.sparse.linalg import eigsh, svds

from . import KMeans, MiniBatchKMeans
from ..base import BaseEstimator, BiclusterMixin
from ..utils import check_random_state
from ..utils import check_scalar

from ..utils.extmath import make_nonnegative, randomized_svd, safe_sparse_dot

from ..utils.validation import assert_all_finite
from ..utils._param_validation import Interval, StrOptions


__all__ = ["SpectralCoclustering", "SpectralBiclustering"]
```



#### Split 2
212 tokens, line: 28 - 46

```python
def _scale_normalize(X):
    """Normalize ``X`` by scaling rows and columns independently.

    Returns the normalized matrix and the row and column scaling
    factors.
    """
    X = make_nonnegative(X)
    row_diag = np.asarray(1.0 / np.sqrt(X.sum(axis=1))).squeeze()
    col_diag = np.asarray(1.0 / np.sqrt(X.sum(axis=0))).squeeze()
    row_diag = np.where(np.isnan(row_diag), 0, row_diag)
    col_diag = np.where(np.isnan(col_diag), 0, col_diag)
    if issparse(X):
        n_rows, n_cols = X.shape
        r = dia_matrix((row_diag, [0]), shape=(n_rows, n_rows))
        c = dia_matrix((col_diag, [0]), shape=(n_cols, n_cols))
        an = r * X * c
    else:
        an = row_diag[:, np.newaxis] * X * col_diag
    return an, row_diag, col_diag
```



#### Split 3
168 tokens, line: 49 - 67

```python
def _bistochastic_normalize(X, max_iter=1000, tol=1e-5):
    """Normalize rows and columns of ``X`` simultaneously so that all
    rows sum to one constant and all columns sum to a different
    constant.
    """
    # According to paper, this can also be done more efficiently with
    # deviation reduction and balancing algorithms.
    X = make_nonnegative(X)
    X_scaled = X
    for _ in range(max_iter):
        X_new, _, _ = _scale_normalize(X_scaled)
        if issparse(X):
            dist = norm(X_scaled.data - X.data)
        else:
            dist = norm(X_scaled - X_new)
        X_scaled = X_new
        if dist is not None and dist < tol:
            break
    return X_scaled
```



#### Split 4
126 tokens, line: 70 - 83

```python
def _log_normalize(X):
    """Normalize ``X`` according to Kluger's log-interactions scheme."""
    X = make_nonnegative(X, min_value=1)
    if issparse(X):
        raise ValueError(
            "Cannot compute log of a sparse matrix,"
            " because log(x) diverges to -infinity as x"
            " goes to 0."
        )
    L = np.log(X)
    row_avg = L.mean(axis=1)[:, np.newaxis]
    col_avg = L.mean(axis=0)
    avg = L.mean()
    return L - row_avg - col_avg + avg
```



#### Split 5
286 tokens, line: 86 - 119

```python
class BaseSpectral(BiclusterMixin, BaseEstimator, metaclass=ABCMeta):
    """Base class for spectral biclustering."""

    _parameter_constraints: dict = {
        "svd_method": [StrOptions({"randomized", "arpack"})],
        "n_svd_vecs": [Interval(Integral, 0, None, closed="left"), None],
        "mini_batch": ["boolean"],
        "init": [StrOptions({"k-means++", "random"}), np.ndarray],
        "n_init": [Interval(Integral, 1, None, closed="left")],
        "random_state": ["random_state"],
    }

    @abstractmethod
    def __init__(
        self,
        n_clusters=3,
        svd_method="randomized",
        n_svd_vecs=None,
        mini_batch=False,
        init="k-means++",
        n_init=10,
        random_state=None,
    ):
        self.n_clusters = n_clusters
        self.svd_method = svd_method
        self.n_svd_vecs = n_svd_vecs
        self.mini_batch = mini_batch
        self.init = init
        self.n_init = n_init
        self.random_state = random_state

    @abstractmethod
    def _check_parameters(self, n_samples):
        """Validate parameters depending on the input data."""
```



#### Split 6
144 tokens, line: 121 - 142

```python
class BaseSpectral(BiclusterMixin, BaseEstimator, metaclass=ABCMeta):

    def fit(self, X, y=None):
        """Create a biclustering for X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        y : Ignored
            Not used, present for API consistency by convention.

        Returns
        -------
        self : object
            SpectralBiclustering instance.
        """
        self._validate_params()

        X = self._validate_data(X, accept_sparse="csr", dtype=np.float64)
        self._check_parameters(X.shape[0])
        self._fit(X)
        return self
```



#### Split 7
421 tokens, line: 144 - 179

```python
class BaseSpectral(BiclusterMixin, BaseEstimator, metaclass=ABCMeta):

    def _svd(self, array, n_components, n_discard):
        """Returns first `n_components` left and right singular
        vectors u and v, discarding the first `n_discard`.
        """
        if self.svd_method == "randomized":
            kwargs = {}
            if self.n_svd_vecs is not None:
                kwargs["n_oversamples"] = self.n_svd_vecs
            u, _, vt = randomized_svd(
                array, n_components, random_state=self.random_state, **kwargs
            )

        elif self.svd_method == "arpack":
            u, _, vt = svds(array, k=n_components, ncv=self.n_svd_vecs)
            if np.any(np.isnan(vt)):
                # some eigenvalues of A * A.T are negative, causing
                # sqrt() to be np.nan. This causes some vectors in vt
                # to be np.nan.
                A = safe_sparse_dot(array.T, array)
                random_state = check_random_state(self.random_state)
                # initialize with [-1,1] as in ARPACK
                v0 = random_state.uniform(-1, 1, A.shape[0])
                _, v = eigsh(A, ncv=self.n_svd_vecs, v0=v0)
                vt = v.T
            if np.any(np.isnan(u)):
                A = safe_sparse_dot(array, array.T)
                random_state = check_random_state(self.random_state)
                # initialize with [-1,1] as in ARPACK
                v0 = random_state.uniform(-1, 1, A.shape[0])
                _, u = eigsh(A, ncv=self.n_svd_vecs, v0=v0)

        assert_all_finite(u)
        assert_all_finite(vt)
        u = u[:, n_discard:]
        vt = vt[n_discard:]
        return u, vt.T
```



#### Split 8
129 tokens, line: 181 - 199

```python
class BaseSpectral(BiclusterMixin, BaseEstimator, metaclass=ABCMeta):

    def _k_means(self, data, n_clusters):
        if self.mini_batch:
            model = MiniBatchKMeans(
                n_clusters,
                init=self.init,
                n_init=self.n_init,
                random_state=self.random_state,
            )
        else:
            model = KMeans(
                n_clusters,
                init=self.init,
                n_init=self.n_init,
                random_state=self.random_state,
            )
        model.fit(data)
        centroid = model.cluster_centers_
        labels = model.labels_
        return centroid, labels
```



#### Split 9
145 tokens, line: 201 - 212

```python
class BaseSpectral(BiclusterMixin, BaseEstimator, metaclass=ABCMeta):

    def _more_tags(self):
        return {
            "_xfail_checks": {
                "check_estimators_dtypes": "raises nan error",
                "check_fit2d_1sample": "_scale_normalize fails",
                "check_fit2d_1feature": "raises apply_along_axis error",
                "check_estimator_sparse_data": "does not fail gracefully",
                "check_methods_subset_invariance": "empty array passed inside",
                "check_dont_overwrite_parameters": "empty array passed inside",
                "check_fit2d_predict1d": "empty array passed inside",
            }
        }
```



#### Split 10
1043 tokens, line: 215 - 323

```python
class SpectralCoclustering(BaseSpectral):
    """Spectral Co-Clustering algorithm (Dhillon, 2001).

    Clusters rows and columns of an array `X` to solve the relaxed
    normalized cut of the bipartite graph created from `X` as follows:
    the edge between row vertex `i` and column vertex `j` has weight
    `X[i, j]`.

    The resulting bicluster structure is block-diagonal, since each
    row and each column belongs to exactly one bicluster.

    Supports sparse matrices, as long as they are nonnegative.

    Read more in the :ref:`User Guide <spectral_coclustering>`.

    Parameters
    ----------
    n_clusters : int, default=3
        The number of biclusters to find.

    svd_method : {'randomized', 'arpack'}, default='randomized'
        Selects the algorithm for finding singular vectors. May be
        'randomized' or 'arpack'. If 'randomized', use
        :func:`sklearn.utils.extmath.randomized_svd`, which may be faster
        for large matrices. If 'arpack', use
        :func:`scipy.sparse.linalg.svds`, which is more accurate, but
        possibly slower in some cases.

    n_svd_vecs : int, default=None
        Number of vectors to use in calculating the SVD. Corresponds
        to `ncv` when `svd_method=arpack` and `n_oversamples` when
        `svd_method` is 'randomized`.

    mini_batch : bool, default=False
        Whether to use mini-batch k-means, which is faster but may get
        different results.

    init : {'k-means++', 'random'}, or ndarray of shape \
            (n_clusters, n_features), default='k-means++'
        Method for initialization of k-means algorithm; defaults to
        'k-means++'.

    n_init : int, default=10
        Number of random initializations that are tried with the
        k-means algorithm.

        If mini-batch k-means is used, the best initialization is
        chosen and the algorithm runs once. Otherwise, the algorithm
        is run for each initialization and the best solution chosen.

    random_state : int, RandomState instance, default=None
        Used for randomizing the singular value decomposition and the k-means
        initialization. Use an int to make the randomness deterministic.
        See :term:`Glossary <random_state>`.

    Attributes
    ----------
    rows_ : array-like of shape (n_row_clusters, n_rows)
        Results of the clustering. `rows[i, r]` is True if
        cluster `i` contains row `r`. Available only after calling ``fit``.

    columns_ : array-like of shape (n_column_clusters, n_columns)
        Results of the clustering, like `rows`.

    row_labels_ : array-like of shape (n_rows,)
        The bicluster label of each row.

    column_labels_ : array-like of shape (n_cols,)
        The bicluster label of each column.

    biclusters_ : tuple of two ndarrays
        The tuple contains the `rows_` and `columns_` arrays.

    n_features_in_ : int
        Number of features seen during :term:`fit`.

        .. versionadded:: 0.24

    feature_names_in_ : ndarray of shape (`n_features_in_`,)
        Names of features seen during :term:`fit`. Defined only when `X`
        has feature names that are all strings.

        .. versionadded:: 1.0

    See Also
    --------
    SpectralBiclustering : Partitions rows and columns under the assumption
        that the data has an underlying checkerboard structure.

    References
    ----------
    * :doi:`Dhillon, Inderjit S, 2001. Co-clustering documents and words using
      bipartite spectral graph partitioning.
      <10.1145/502512.502550>`

    Examples
    --------
    >>> from sklearn.cluster import SpectralCoclustering
    >>> import numpy as np
    >>> X = np.array([[1, 1], [2, 1], [1, 0],
    ...               [4, 7], [3, 5], [3, 6]])
    >>> clustering = SpectralCoclustering(n_clusters=2, random_state=0).fit(X)
    >>> clustering.row_labels_ #doctest: +SKIP
    array([0, 1, 1, 0, 0, 0], dtype=int32)
    >>> clustering.column_labels_ #doctest: +SKIP
    array([0, 0], dtype=int32)
    >>> clustering
    SpectralCoclustering(n_clusters=2, random_state=0)
    """
```



#### Split 11
190 tokens, line: 325 - 350

```python
class SpectralCoclustering(BaseSpectral):

    _parameter_constraints: dict = {
        **BaseSpectral._parameter_constraints,
        "n_clusters": [Interval(Integral, 1, None, closed="left")],
    }

    def __init__(
        self,
        n_clusters=3,
        *,
        svd_method="randomized",
        n_svd_vecs=None,
        mini_batch=False,
        init="k-means++",
        n_init=10,
        random_state=None,
    ):
        super().__init__(
            n_clusters, svd_method, n_svd_vecs, mini_batch, init, n_init, random_state
        )

    def _check_parameters(self, n_samples):
        if self.n_clusters > n_samples:
            raise ValueError(
                f"n_clusters should be <= n_samples={n_samples}. Got"
                f" {self.n_clusters} instead."
            )
```



#### Split 12
188 tokens, line: 352 - 367

```python
class SpectralCoclustering(BaseSpectral):

    def _fit(self, X):
        normalized_data, row_diag, col_diag = _scale_normalize(X)
        n_sv = 1 + int(np.ceil(np.log2(self.n_clusters)))
        u, v = self._svd(normalized_data, n_sv, n_discard=1)
        z = np.vstack((row_diag[:, np.newaxis] * u, col_diag[:, np.newaxis] * v))

        _, labels = self._k_means(z, self.n_clusters)

        n_rows = X.shape[0]
        self.row_labels_ = labels[:n_rows]
        self.column_labels_ = labels[n_rows:]

        self.rows_ = np.vstack([self.row_labels_ == c for c in range(self.n_clusters)])
        self.columns_ = np.vstack(
            [self.column_labels_ == c for c in range(self.n_clusters)]
        )
```



#### Split 13
239 tokens, line: 370 - 522

```python
class SpectralBiclustering(BaseSpectral):

    _parameter_constraints: dict = {
        **BaseSpectral._parameter_constraints,
        "n_clusters": [Interval(Integral, 1, None, closed="left"), tuple],
        "method": [StrOptions({"bistochastic", "scale", "log"})],
        "n_components": [Interval(Integral, 1, None, closed="left")],
        "n_best": [Interval(Integral, 1, None, closed="left")],
    }

    def __init__(
        self,
        n_clusters=3,
        *,
        method="bistochastic",
        n_components=6,
        n_best=3,
        svd_method="randomized",
        n_svd_vecs=None,
        mini_batch=False,
        init="k-means++",
        n_init=10,
        random_state=None,
    ):
        super().__init__(
            n_clusters, svd_method, n_svd_vecs, mini_batch, init, n_init, random_state
        )
        self.method = method
        self.n_components = n_components
        self.n_best = n_best
```



#### Split 14
286 tokens, line: 524 - 561

```python
class SpectralBiclustering(BaseSpectral):

    def _check_parameters(self, n_samples):
        if isinstance(self.n_clusters, Integral):
            if self.n_clusters > n_samples:
                raise ValueError(
                    f"n_clusters should be <= n_samples={n_samples}. Got"
                    f" {self.n_clusters} instead."
                )
        else:  # tuple
            try:
                n_row_clusters, n_column_clusters = self.n_clusters
                check_scalar(
                    n_row_clusters,
                    "n_row_clusters",
                    target_type=Integral,
                    min_val=1,
                    max_val=n_samples,
                )
                check_scalar(
                    n_column_clusters,
                    "n_column_clusters",
                    target_type=Integral,
                    min_val=1,
                    max_val=n_samples,
                )
            except (ValueError, TypeError) as e:
                raise ValueError(
                    "Incorrect parameter n_clusters has value:"
                    f" {self.n_clusters}. It should either be a single integer"
                    " or an iterable with two integers:"
                    " (n_row_clusters, n_column_clusters)"
                    " And the values are should be in the"
                    " range: (1, n_samples)"
                ) from e

        if self.n_best > self.n_components:
            raise ValueError(
                f"n_best={self.n_best} must be <= n_components={self.n_components}."
            )
```



#### Split 15
348 tokens, line: 563 - 604

```python
class SpectralBiclustering(BaseSpectral):

    def _fit(self, X):
        n_sv = self.n_components
        if self.method == "bistochastic":
            normalized_data = _bistochastic_normalize(X)
            n_sv += 1
        elif self.method == "scale":
            normalized_data, _, _ = _scale_normalize(X)
            n_sv += 1
        elif self.method == "log":
            normalized_data = _log_normalize(X)
        n_discard = 0 if self.method == "log" else 1
        u, v = self._svd(normalized_data, n_sv, n_discard)
        ut = u.T
        vt = v.T

        try:
            n_row_clusters, n_col_clusters = self.n_clusters
        except TypeError:
            n_row_clusters = n_col_clusters = self.n_clusters

        best_ut = self._fit_best_piecewise(ut, self.n_best, n_row_clusters)

        best_vt = self._fit_best_piecewise(vt, self.n_best, n_col_clusters)

        self.row_labels_ = self._project_and_cluster(X, best_vt.T, n_row_clusters)

        self.column_labels_ = self._project_and_cluster(X.T, best_ut.T, n_col_clusters)

        self.rows_ = np.vstack(
            [
                self.row_labels_ == label
                for label in range(n_row_clusters)
                for _ in range(n_col_clusters)
            ]
        )
        self.columns_ = np.vstack(
            [
                self.column_labels_ == label
                for _ in range(n_row_clusters)
                for label in range(n_col_clusters)
            ]
        )
```



#### Split 16
231 tokens, line: 606 - 629

```python
class SpectralBiclustering(BaseSpectral):

    def _fit_best_piecewise(self, vectors, n_best, n_clusters):
        """Find the ``n_best`` vectors that are best approximated by piecewise
        constant vectors.

        The piecewise vectors are found by k-means; the best is chosen
        according to Euclidean distance.

        """

        def make_piecewise(v):
            centroid, labels = self._k_means(v.reshape(-1, 1), n_clusters)
            return centroid[labels].ravel()

        piecewise_vectors = np.apply_along_axis(make_piecewise, axis=1, arr=vectors)
        dists = np.apply_along_axis(norm, axis=1, arr=(vectors - piecewise_vectors))
        result = vectors[np.argsort(dists)[:n_best]]
        return result

    def _project_and_cluster(self, data, vectors, n_clusters):
        """Project ``data`` to ``vectors`` and cluster the result."""
        projected = safe_sparse_dot(data, vectors)
        _, labels = self._k_means(projected, n_clusters)
        return labels
```
