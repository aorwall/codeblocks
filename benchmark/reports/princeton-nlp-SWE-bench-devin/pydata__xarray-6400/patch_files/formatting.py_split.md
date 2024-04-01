

## EpicSplitter

25 chunks

#### Split 1
295 tokens, line: 1 - 41

```python
"""String formatting routines for __repr__.
"""
import contextlib
import functools
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import chain, zip_longest
from typing import Collection, Hashable, Optional

import numpy as np
import pandas as pd
from pandas.errors import OutOfBoundsDatetime

from .duck_array_ops import array_equiv
from .indexing import MemoryCachedArray
from .options import OPTIONS, _get_boolean_with_default
from .pycompat import dask_array_type, sparse_array_type
from .utils import is_duck_array


def pretty_print(x, numchars: int):
    """Given an object `x`, call `str(x)` and format the returned string so
    that it is numchars long, padding with trailing spaces or truncating with
    ellipses as necessary
    """
    s = maybe_truncate(x, numchars)
    return s + " " * max(numchars - len(s), 0)


def maybe_truncate(obj, maxlen=500):
    s = str(obj)
    if len(s) > maxlen:
        s = s[: (maxlen - 3)] + "..."
    return s


def wrap_indent(text, start="", length=None):
    if length is None:
        length = len(start)
    indent = "\n" + " " * length
    return start + indent.join(x for x in text.splitlines())
```



#### Split 2
140 tokens, line: 44 - 54

```python
def _get_indexer_at_least_n_items(shape, n_desired, from_end):
    assert 0 < n_desired <= np.prod(shape)
    cum_items = np.cumprod(shape[::-1])
    n_steps = np.argmax(cum_items >= n_desired)
    stop = int(np.ceil(float(n_desired) / np.r_[1, cum_items][n_steps]))
    indexer = (
        ((-1 if from_end else 0),) * (len(shape) - 1 - n_steps)
        + ((slice(-stop, None) if from_end else slice(stop)),)
        + (slice(None),) * n_steps
    )
    return indexer
```



#### Split 3
203 tokens, line: 57 - 73

```python
def first_n_items(array, n_desired):
    """Returns the first n_desired items of an array"""
    # Unfortunately, we can't just do array.flat[:n_desired] here because it
    # might not be a numpy.ndarray. Moreover, access to elements of the array
    # could be very expensive (e.g. if it's only available over DAP), so go out
    # of our way to get them in a single call to __getitem__ using only slices.
    if n_desired < 1:
        raise ValueError("must request at least one item")

    if array.size == 0:
        # work around for https://github.com/numpy/numpy/issues/5195
        return []

    if n_desired < array.size:
        indexer = _get_indexer_at_least_n_items(array.shape, n_desired, from_end=False)
        array = array[indexer]
    return np.asarray(array).flat[:n_desired]
```



#### Split 4
175 tokens, line: 76 - 88

```python
def last_n_items(array, n_desired):
    """Returns the last n_desired items of an array"""
    # Unfortunately, we can't just do array.flat[-n_desired:] here because it
    # might not be a numpy.ndarray. Moreover, access to elements of the array
    # could be very expensive (e.g. if it's only available over DAP), so go out
    # of our way to get them in a single call to __getitem__ using only slices.
    if (n_desired == 0) or (array.size == 0):
        return []

    if n_desired < array.size:
        indexer = _get_indexer_at_least_n_items(array.shape, n_desired, from_end=True)
        array = array[indexer]
    return np.asarray(array).flat[-n_desired:]
```



#### Split 5
153 tokens, line: 91 - 108

```python
def last_item(array):
    """Returns the last item of an array in a list or an empty list."""
    if array.size == 0:
        # work around for https://github.com/numpy/numpy/issues/5195
        return []

    indexer = (slice(-1, None),) * array.ndim
    return np.ravel(np.asarray(array[indexer])).tolist()


def calc_max_rows_first(max_rows: int) -> int:
    """Calculate the first rows to maintain the max number of rows."""
    return max_rows // 2 + max_rows % 2


def calc_max_rows_last(max_rows: int) -> int:
    """Calculate the last rows to maintain the max number of rows."""
    return max_rows // 2
```



#### Split 6
246 tokens, line: 111 - 145

```python
def format_timestamp(t):
    """Cast given object to a Timestamp and return a nicely formatted string"""
    # Timestamp is only valid for 1678 to 2262
    try:
        datetime_str = str(pd.Timestamp(t))
    except OutOfBoundsDatetime:
        datetime_str = str(t)

    try:
        date_str, time_str = datetime_str.split()
    except ValueError:
        # catch NaT and others that don't split nicely
        return datetime_str
    else:
        if time_str == "00:00:00":
            return date_str
        else:
            return f"{date_str}T{time_str}"


def format_timedelta(t, timedelta_format=None):
    """Cast given object to a Timestamp and return a nicely formatted string"""
    timedelta_str = str(pd.Timedelta(t))
    try:
        days_str, time_str = timedelta_str.split(" days ")
    except ValueError:
        # catch NaT and others that don't split nicely
        return timedelta_str
    else:
        if timedelta_format == "date":
            return days_str + " days"
        elif timedelta_format == "time":
            return time_str
        else:
            return timedelta_str
```



#### Split 7
130 tokens, line: 148 - 159

```python
def format_item(x, timedelta_format=None, quote_strings=True):
    """Returns a succinct summary of an object as a string"""
    if isinstance(x, (np.datetime64, datetime)):
        return format_timestamp(x)
    if isinstance(x, (np.timedelta64, timedelta)):
        return format_timedelta(x, timedelta_format=timedelta_format)
    elif isinstance(x, (str, bytes)):
        return repr(x) if quote_strings else x
    elif hasattr(x, "dtype") and np.issubdtype(x.dtype, np.floating):
        return f"{x.item():.4}"
    else:
        return str(x)
```



#### Split 8
175 tokens, line: 162 - 177

```python
def format_items(x):
    """Returns a succinct summaries of all items in a sequence as strings"""
    x = np.asarray(x)
    timedelta_format = "datetime"
    if np.issubdtype(x.dtype, np.timedelta64):
        x = np.asarray(x, dtype="timedelta64[ns]")
        day_part = x[~pd.isnull(x)].astype("timedelta64[D]").astype("timedelta64[ns]")
        time_needed = x[~pd.isnull(x)] != day_part
        day_needed = day_part != np.timedelta64(0, "ns")
        if np.logical_not(day_needed).all():
            timedelta_format = "time"
        elif np.logical_not(time_needed).all():
            timedelta_format = "date"

    formatted = [format_item(xi, timedelta_format) for xi in x]
    return formatted
```



#### Split 9
529 tokens, line: 180 - 228

```python
def format_array_flat(array, max_width: int):
    """Return a formatted string for as many items in the flattened version of
    array that will fit within max_width characters.
    """
    # every item will take up at least two characters, but we always want to
    # print at least first and last items
    max_possibly_relevant = min(
        max(array.size, 1), max(int(np.ceil(max_width / 2.0)), 2)
    )
    relevant_front_items = format_items(
        first_n_items(array, (max_possibly_relevant + 1) // 2)
    )
    relevant_back_items = format_items(last_n_items(array, max_possibly_relevant // 2))
    # interleave relevant front and back items:
    #     [a, b, c] and [y, z] -> [a, z, b, y, c]
    relevant_items = sum(
        zip_longest(relevant_front_items, reversed(relevant_back_items)), ()
    )[:max_possibly_relevant]

    cum_len = np.cumsum([len(s) + 1 for s in relevant_items]) - 1
    if (array.size > 2) and (
        (max_possibly_relevant < array.size) or (cum_len > max_width).any()
    ):
        padding = " ... "
        max_len = max(int(np.argmax(cum_len + len(padding) - 1 > max_width)), 2)
        count = min(array.size, max_len)
    else:
        count = array.size
        padding = "" if (count <= 1) else " "

    num_front = (count + 1) // 2
    num_back = count - num_front
    # note that num_back is 0 <--> array.size is 0 or 1
    #                         <--> relevant_back_items is []
    pprint_str = "".join(
        [
            " ".join(relevant_front_items[:num_front]),
            padding,
            " ".join(relevant_back_items[-num_back:]),
        ]
    )

    # As a final check, if it's still too long even with the limit in values,
    # replace the end with an ellipsis
    # NB: this will still returns a full 3-character ellipsis when max_width < 3
    if len(pprint_str) > max_width:
        pprint_str = pprint_str[: max(max_width - 3, 0)] + "..."

    return pprint_str
```



#### Split 10
203 tokens, line: 231 - 257

```python
_KNOWN_TYPE_REPRS = {np.ndarray: "np.ndarray"}
with contextlib.suppress(ImportError):
    import sparse

    _KNOWN_TYPE_REPRS[sparse.COO] = "sparse.COO"


def inline_dask_repr(array):
    """Similar to dask.array.DataArray.__repr__, but without
    redundant information that's already printed by the repr
    function of the xarray wrapper.
    """
    assert isinstance(array, dask_array_type), array

    chunksize = tuple(c[0] for c in array.chunks)

    if hasattr(array, "_meta"):
        meta = array._meta
        if type(meta) in _KNOWN_TYPE_REPRS:
            meta_repr = _KNOWN_TYPE_REPRS[type(meta)]
        else:
            meta_repr = type(meta).__name__
        meta_string = f", meta={meta_repr}"
    else:
        meta_string = ""

    return f"dask.array<chunksize={chunksize}{meta_string}>"
```



#### Split 11
221 tokens, line: 260 - 282

```python
def inline_sparse_repr(array):
    """Similar to sparse.COO.__repr__, but without the redundant shape/dtype."""
    assert isinstance(array, sparse_array_type), array
    return "<{}: nnz={:d}, fill_value={!s}>".format(
        type(array).__name__, array.nnz, array.fill_value
    )


def inline_variable_array_repr(var, max_width):
    """Build a one-line summary of a variable's data."""
    if hasattr(var._data, "_repr_inline_"):
        return var._data._repr_inline_(max_width)
    elif var._in_memory:
        return format_array_flat(var, max_width)
    elif isinstance(var._data, dask_array_type):
        return inline_dask_repr(var.data)
    elif isinstance(var._data, sparse_array_type):
        return inline_sparse_repr(var.data)
    elif hasattr(var._data, "__array_function__"):
        return maybe_truncate(repr(var._data).replace("\n", " "), max_width)
    else:
        # internal xarray array type
        return "..."
```



#### Split 12
231 tokens, line: 285 - 310

```python
def summarize_variable(
    name: Hashable, var, col_width: int, max_width: int = None, is_index: bool = False
):
    """Summarize a variable in one line, e.g., for the Dataset.__repr__."""
    variable = getattr(var, "variable", var)

    if max_width is None:
        max_width_options = OPTIONS["display_width"]
        if not isinstance(max_width_options, int):
            raise TypeError(f"`max_width` value of `{max_width}` is not a valid int")
        else:
            max_width = max_width_options

    marker = "*" if is_index else " "
    first_col = pretty_print(f"  {marker} {name} ", col_width)

    if variable.dims:
        dims_str = "({}) ".format(", ".join(map(str, variable.dims)))
    else:
        dims_str = ""
    front_str = f"{first_col}{dims_str}{variable.dtype} "

    values_width = max_width - len(front_str)
    values_str = inline_variable_array_repr(variable, values_width)

    return front_str + values_str
```



#### Split 13
211 tokens, line: 313 - 331

```python
def summarize_attr(key, value, col_width=None):
    """Summary for __repr__ - use ``X.attrs[key]`` for full value."""
    # Indent key and add ':', then right-pad if col_width is not None
    k_str = f"    {key}:"
    if col_width is not None:
        k_str = pretty_print(k_str, col_width)
    # Replace tabs and newlines, so we print on one line in known width
    v_str = str(value).replace("\t", "\\t").replace("\n", "\\n")
    # Finally, truncate to the desired display width
    return maybe_truncate(f"{k_str} {v_str}", OPTIONS["display_width"])


EMPTY_REPR = "    *empty*"


def _calculate_col_width(col_items):
    max_name_length = max(len(str(s)) for s in col_items) if col_items else 0
    col_width = max(max_name_length, 7) + 6
    return col_width
```



#### Split 14
346 tokens, line: 334 - 377

```python
def _mapping_repr(
    mapping,
    title,
    summarizer,
    expand_option_name,
    col_width=None,
    max_rows=None,
    indexes=None,
):
    if col_width is None:
        col_width = _calculate_col_width(mapping)

    summarizer_kwargs = defaultdict(dict)
    if indexes is not None:
        summarizer_kwargs = {k: {"is_index": k in indexes} for k in mapping}

    summary = [f"{title}:"]
    if mapping:
        len_mapping = len(mapping)
        if not _get_boolean_with_default(expand_option_name, default=True):
            summary = [f"{summary[0]} ({len_mapping})"]
        elif max_rows is not None and len_mapping > max_rows:
            summary = [f"{summary[0]} ({max_rows}/{len_mapping})"]
            first_rows = calc_max_rows_first(max_rows)
            keys = list(mapping.keys())
            summary += [
                summarizer(k, mapping[k], col_width, **summarizer_kwargs[k])
                for k in keys[:first_rows]
            ]
            if max_rows > 1:
                last_rows = calc_max_rows_last(max_rows)
                summary += [pretty_print("    ...", col_width) + " ..."]
                summary += [
                    summarizer(k, mapping[k], col_width, **summarizer_kwargs[k])
                    for k in keys[-last_rows:]
                ]
        else:
            summary += [
                summarizer(k, v, col_width, **summarizer_kwargs[k])
                for k, v in mapping.items()
            ]
    else:
        summary += [EMPTY_REPR]
    return "\n".join(summary)
```



#### Split 15
247 tokens, line: 380 - 422

```python
data_vars_repr = functools.partial(
    _mapping_repr,
    title="Data variables",
    summarizer=summarize_variable,
    expand_option_name="display_expand_data_vars",
)


attrs_repr = functools.partial(
    _mapping_repr,
    title="Attributes",
    summarizer=summarize_attr,
    expand_option_name="display_expand_attrs",
)


def coords_repr(coords, col_width=None, max_rows=None):
    if col_width is None:
        col_width = _calculate_col_width(coords)
    return _mapping_repr(
        coords,
        title="Coordinates",
        summarizer=summarize_variable,
        expand_option_name="display_expand_coords",
        col_width=col_width,
        indexes=coords.xindexes,
        max_rows=max_rows,
    )


def indexes_repr(indexes):
    summary = ["Indexes:"]
    if indexes:
        for k, v in indexes.items():
            summary.append(wrap_indent(repr(v), f"{k}: "))
    else:
        summary += [EMPTY_REPR]
    return "\n".join(summary)


def dim_summary(obj):
    elements = [f"{k}: {v}" for k, v in obj.sizes.items()]
    return ", ".join(elements)
```



#### Split 16
436 tokens, line: 425 - 477

```python
def _element_formatter(
    elements: Collection[Hashable],
    col_width: int,
    max_rows: Optional[int] = None,
    delimiter: str = ", ",
) -> str:
    """
    Formats elements for better readability.

    Once it becomes wider than the display width it will create a newline and
    continue indented to col_width.
    Once there are more rows than the maximum displayed rows it will start
    removing rows.

    Parameters
    ----------
    elements : Collection of hashable
        Elements to join together.
    col_width : int
        The width to indent to if a newline has been made.
    max_rows : int, optional
        The maximum number of allowed rows. The default is None.
    delimiter : str, optional
        Delimiter to use between each element. The default is ", ".
    """
    elements_len = len(elements)
    out = [""]
    length_row = 0
    for i, v in enumerate(elements):
        delim = delimiter if i < elements_len - 1 else ""
        v_delim = f"{v}{delim}"
        length_element = len(v_delim)
        length_row += length_element

        # Create a new row if the next elements makes the print wider than
        # the maximum display width:
        if col_width + length_row > OPTIONS["display_width"]:
            out[-1] = out[-1].rstrip()  # Remove trailing whitespace.
            out.append("\n" + pretty_print("", col_width) + v_delim)
            length_row = length_element
        else:
            out[-1] += v_delim

    # If there are too many rows of dimensions trim some away:
    if max_rows and (len(out) > max_rows):
        first_rows = calc_max_rows_first(max_rows)
        last_rows = calc_max_rows_last(max_rows)
        out = (
            out[:first_rows]
            + ["\n" + pretty_print("", col_width) + "..."]
            + (out[-last_rows:] if max_rows > 1 else [])
        )
    return "".join(out)
```



#### Split 17
287 tokens, line: 480 - 515

```python
def dim_summary_limited(obj, col_width: int, max_rows: Optional[int] = None) -> str:
    elements = [f"{k}: {v}" for k, v in obj.sizes.items()]
    return _element_formatter(elements, col_width, max_rows)


def unindexed_dims_repr(dims, coords, max_rows: Optional[int] = None):
    unindexed_dims = [d for d in dims if d not in coords]
    if unindexed_dims:
        dims_start = "Dimensions without coordinates: "
        dims_str = _element_formatter(
            unindexed_dims, col_width=len(dims_start), max_rows=max_rows
        )
        return dims_start + dims_str
    else:
        return None


@contextlib.contextmanager
def set_numpy_options(*args, **kwargs):
    original = np.get_printoptions()
    np.set_printoptions(*args, **kwargs)
    try:
        yield
    finally:
        np.set_printoptions(**original)


def limit_lines(string: str, *, limit: int):
    """
    If the string is more lines than the limit,
    this returns the middle lines replaced by an ellipsis
    """
    lines = string.splitlines()
    if len(lines) > limit:
        string = "\n".join(chain(lines[: limit // 2], ["..."], lines[-limit // 2 :]))
    return string
```



#### Split 18
127 tokens, line: 518 - 532

```python
def short_numpy_repr(array):
    array = np.asarray(array)

    # default to lower precision so a full (abbreviated) line can fit on
    # one line with the default display_width
    options = {"precision": 6, "linewidth": OPTIONS["display_width"], "threshold": 200}
    if array.ndim < 3:
        edgeitems = 3
    elif array.ndim == 3:
        edgeitems = 2
    else:
        edgeitems = 1
    options["edgeitems"] = edgeitems
    with set_numpy_options(**options):
        return repr(array)
```



#### Split 19
118 tokens, line: 535 - 546

```python
def short_data_repr(array):
    """Format "data" for DataArray and Variable."""
    internal_data = getattr(array, "variable", array)._data
    if isinstance(array, np.ndarray):
        return short_numpy_repr(array)
    elif is_duck_array(internal_data):
        return limit_lines(repr(array.data), limit=40)
    elif array._in_memory or array.size < 1e5:
        return short_numpy_repr(array)
    else:
        # internal xarray array type
        return f"[{array.size} values with dtype={array.dtype}]"
```



#### Split 20
304 tokens, line: 549 - 592

```python
def array_repr(arr):
    from .variable import Variable

    max_rows = OPTIONS["display_max_rows"]

    # used for DataArray, Variable and IndexVariable
    if hasattr(arr, "name") and arr.name is not None:
        name_str = f"{arr.name!r} "
    else:
        name_str = ""

    if (
        isinstance(arr, Variable)
        or _get_boolean_with_default("display_expand_data", default=True)
        or isinstance(arr.variable._data, MemoryCachedArray)
    ):
        data_repr = short_data_repr(arr)
    else:
        data_repr = inline_variable_array_repr(arr.variable, OPTIONS["display_width"])

    start = f"<xarray.{type(arr).__name__} {name_str}"
    dims = dim_summary_limited(arr, col_width=len(start) + 1, max_rows=max_rows)
    summary = [
        f"{start}({dims})>",
        data_repr,
    ]

    if hasattr(arr, "coords"):
        if arr.coords:
            col_width = _calculate_col_width(arr.coords)
            summary.append(
                coords_repr(arr.coords, col_width=col_width, max_rows=max_rows)
            )

        unindexed_dims_str = unindexed_dims_repr(
            arr.dims, arr.coords, max_rows=max_rows
        )
        if unindexed_dims_str:
            summary.append(unindexed_dims_str)

    if arr.attrs:
        summary.append(attrs_repr(arr.attrs))

    return "\n".join(summary)
```



#### Split 21
252 tokens, line: 595 - 626

```python
def dataset_repr(ds):
    summary = [f"<xarray.{type(ds).__name__}>"]

    col_width = _calculate_col_width(ds.variables)
    max_rows = OPTIONS["display_max_rows"]

    dims_start = pretty_print("Dimensions:", col_width)
    dims_values = dim_summary_limited(ds, col_width=col_width + 1, max_rows=max_rows)
    summary.append(f"{dims_start}({dims_values})")

    if ds.coords:
        summary.append(coords_repr(ds.coords, col_width=col_width, max_rows=max_rows))

    unindexed_dims_str = unindexed_dims_repr(ds.dims, ds.coords, max_rows=max_rows)
    if unindexed_dims_str:
        summary.append(unindexed_dims_str)

    summary.append(data_vars_repr(ds.data_vars, col_width=col_width, max_rows=max_rows))

    if ds.attrs:
        summary.append(attrs_repr(ds.attrs, max_rows=max_rows))

    return "\n".join(summary)


def diff_dim_summary(a, b):
    if a.dims != b.dims:
        return "Differing dimensions:\n    ({}) != ({})".format(
            dim_summary(a), dim_summary(b)
        )
    else:
        return ""
```



#### Split 22
620 tokens, line: 629 - 710

```python
def _diff_mapping_repr(
    a_mapping,
    b_mapping,
    compat,
    title,
    summarizer,
    col_width=None,
    a_indexes=None,
    b_indexes=None,
):
    def extra_items_repr(extra_keys, mapping, ab_side, kwargs):
        extra_repr = [
            summarizer(k, mapping[k], col_width, **kwargs[k]) for k in extra_keys
        ]
        if extra_repr:
            header = f"{title} only on the {ab_side} object:"
            return [header] + extra_repr
        else:
            return []

    a_keys = set(a_mapping)
    b_keys = set(b_mapping)

    summary = []

    diff_items = []

    a_summarizer_kwargs = defaultdict(dict)
    if a_indexes is not None:
        a_summarizer_kwargs = {k: {"is_index": k in a_indexes} for k in a_mapping}
    b_summarizer_kwargs = defaultdict(dict)
    if b_indexes is not None:
        b_summarizer_kwargs = {k: {"is_index": k in b_indexes} for k in b_mapping}

    for k in a_keys & b_keys:
        try:
            # compare xarray variable
            if not callable(compat):
                compatible = getattr(a_mapping[k], compat)(b_mapping[k])
            else:
                compatible = compat(a_mapping[k], b_mapping[k])
            is_variable = True
        except AttributeError:
            # compare attribute value
            if is_duck_array(a_mapping[k]) or is_duck_array(b_mapping[k]):
                compatible = array_equiv(a_mapping[k], b_mapping[k])
            else:
                compatible = a_mapping[k] == b_mapping[k]

            is_variable = False

        if not compatible:
            temp = [
                summarizer(k, a_mapping[k], col_width, **a_summarizer_kwargs[k]),
                summarizer(k, b_mapping[k], col_width, **b_summarizer_kwargs[k]),
            ]

            if compat == "identical" and is_variable:
                attrs_summary = []

                for m in (a_mapping, b_mapping):
                    attr_s = "\n".join(
                        summarize_attr(ak, av) for ak, av in m[k].attrs.items()
                    )
                    attrs_summary.append(attr_s)

                temp = [
                    "\n".join([var_s, attr_s]) if attr_s else var_s
                    for var_s, attr_s in zip(temp, attrs_summary)
                ]

            diff_items += [ab_side + s[1:] for ab_side, s in zip(("L", "R"), temp)]

    if diff_items:
        summary += [f"Differing {title.lower()}:"] + diff_items

    summary += extra_items_repr(a_keys - b_keys, a_mapping, "left", a_summarizer_kwargs)
    summary += extra_items_repr(
        b_keys - a_keys, b_mapping, "right", b_summarizer_kwargs
    )

    return "\n".join(summary)
```



#### Split 23
165 tokens, line: 713 - 745

```python
def diff_coords_repr(a, b, compat, col_width=None):
    return _diff_mapping_repr(
        a,
        b,
        compat,
        "Coordinates",
        summarize_variable,
        col_width=col_width,
        a_indexes=a.indexes,
        b_indexes=b.indexes,
    )


diff_data_vars_repr = functools.partial(
    _diff_mapping_repr, title="Data variables", summarizer=summarize_variable
)


diff_attrs_repr = functools.partial(
    _diff_mapping_repr, title="Attributes", summarizer=summarize_attr
)


def _compat_to_str(compat):
    if callable(compat):
        compat = compat.__name__

    if compat == "equals":
        return "equal"
    elif compat == "allclose":
        return "close"
    else:
        return compat
```



#### Split 24
250 tokens, line: 748 - 779

```python
def diff_array_repr(a, b, compat):
    # used for DataArray, Variable and IndexVariable
    summary = [
        "Left and right {} objects are not {}".format(
            type(a).__name__, _compat_to_str(compat)
        )
    ]

    summary.append(diff_dim_summary(a, b))
    if callable(compat):
        equiv = compat
    else:
        equiv = array_equiv

    if not equiv(a.data, b.data):
        temp = [wrap_indent(short_numpy_repr(obj), start="    ") for obj in (a, b)]
        diff_data_repr = [
            ab_side + "\n" + ab_data_repr
            for ab_side, ab_data_repr in zip(("L", "R"), temp)
        ]
        summary += ["Differing values:"] + diff_data_repr

    if hasattr(a, "coords"):
        col_width = _calculate_col_width(set(a.coords) | set(b.coords))
        summary.append(
            diff_coords_repr(a.coords, b.coords, compat, col_width=col_width)
        )

    if compat == "identical":
        summary.append(diff_attrs_repr(a.attrs, b.attrs, compat))

    return "\n".join(summary)
```



#### Split 25
148 tokens, line: 782 - 801

```python
def diff_dataset_repr(a, b, compat):
    summary = [
        "Left and right {} objects are not {}".format(
            type(a).__name__, _compat_to_str(compat)
        )
    ]

    col_width = _calculate_col_width(set(list(a.variables) + list(b.variables)))

    summary.append(diff_dim_summary(a, b))
    summary.append(diff_coords_repr(a.coords, b.coords, compat, col_width=col_width))
    summary.append(
        diff_data_vars_repr(a.data_vars, b.data_vars, compat, col_width=col_width)
    )

    if compat == "identical":
        summary.append(diff_attrs_repr(a.attrs, b.attrs, compat))

    return "\n".join(summary)
```
