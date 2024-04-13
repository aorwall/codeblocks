import json
import logging
import os
import subprocess
from typing import List

from datasets import load_dataset

from benchmark.utils import diff_details, write_json, diff_file_names
from moatless.retriever import CodeSnippet

logger = logging.getLogger(__name__)


_reports = {}


def instance_report(dir: str, subdir: str) -> dict:
    report_path = os.path.join(dir, subdir, "data.json")
    with open(report_path, "r") as f:
        return json.load(f)


def instance_reports(dir: str) -> list[dict]:
    return [
        instance_report(dir, subdir)
        for subdir in os.listdir(dir)
        if os.path.isdir(os.path.join(dir, subdir))
    ]


def sort_key(data_row):
    text, number = data_row["instance_id"].rsplit("-", 1)
    return text, int(number)


def get_filename(split: str, dataset_name: str):
    return f'{dataset_name.replace("/", "-")}-{split}'


def download(
    split: str = "dev", dataset_name="princeton-nlp/SWE-bench", data_dir: str = None
):
    """Download oracle (patched files) for all rows in split"""

    file_name = get_filename(split, dataset_name)

    global _reports

    if file_name in _reports:
        return _reports[file_name]

    if data_dir:
        file_path = f"{data_dir}/{file_name}.json"
        if os.path.exists(file_path):
            logger.debug(f"File '{file_path}' already exists")
            with open(file_path) as f:
                return json.load(f)
        else:
            logger.debug(f"File '{file_path}' does not exist. Downloading...")

    dataset = load_dataset(dataset_name, split=split)
    result = []
    for row_data in dataset:
        row_data["patch_files"] = diff_file_names(row_data["patch"])
        row_data["test_patch_files"] = diff_file_names(row_data["test_patch"])
        row_data["patch_diff_details"] = diff_details(row_data["patch"])
        result.append(row_data)

    _reports[file_name] = result

    if data_dir:
        write_json(data_dir, file_name, result)

    return result


def get_instance(
    id: str,
    split: str = "test",
    dataset_name="princeton-nlp/SWE-bench",
    data_dir: str = None,
):
    dataset = download(split, dataset_name, data_dir)
    for row in dataset:
        if row["instance_id"] == id:
            return row


def get_instances(
    split: str = "dev", dataset_name="princeton-nlp/SWE-bench", data_dir: str = None
):
    dataset = download(split, dataset_name, data_dir)
    dataset.sort(key=sort_key)
    return dataset


def sort_key(data_row):
    text, number = data_row["instance_id"].rsplit("-", 1)
    return text, int(number)


def get_index_name(row_data: dict):
    return f"{row_data['repo'].replace('/', '_')}__{row_data['instance_id']}"


def display_problem_statement(data: dict):
    from IPython.display import display, Markdown

    display(
        Markdown(
            f"""### Problem statement
{data['problem_statement']}

### Expected patch
```diff
{data['patch']}
```
"""
        )
    )


def display_patches(data: dict, path: str):
    from IPython.display import display, Markdown

    diff = subprocess.run(
        ["git", "diff"], cwd=path, check=True, text=True, capture_output=True
    )
    display(
        Markdown(
            f"""### Expected patch
```diff
{data['patch']}
```

### Generated patch
"""
        )
    )

    if diff.stdout:
        display(
            Markdown(
                f"""```diff
{diff.stdout}
```
"""
            )
        )
    else:
        display(Markdown("_No changes found._"))


def display_code_snippets(data: dict, code_snippets: List[CodeSnippet]):
    import pandas as pd
    from IPython.display import display
    from IPython.core.display import HTML

    snippets_data = []
    context_length = 0

    for snippet in code_snippets:
        context_length += snippet.tokens or 0
        snippets_data.append(
            {
                "File": snippet.file_path,
                "Block": snippet.start_block,
                "Start line": snippet.start_line,
                "End line": snippet.end_line,
                "Context length": context_length,
            }
        )

    df = pd.DataFrame(snippets_data)

    found_files = set(df["File"])
    patch_files_set = set(data["patch_files"])
    all_files_found = patch_files_set.issubset(found_files)

    message = (
        "All expected patch files is referred to in the retrieved code snippets."
        if all_files_found
        else "Some expected path files where not referred to in the code snippets. This means that the instance probably can't be completed."
    )
    display(
        HTML(
            f"<div style='background-color: #f2f2f2; padding: 10px; border-left: 6px solid #ffcc00; margin-bottom: 10px;'>{message}</div>"
        )
    )

    def match_diff(row):
        return row["File"] in data["patch_files"]

    df["diff_covered_or_file_match"] = df.apply(match_diff, axis=1)

    df_filtered = (
        pd.concat([df.head(5), df[df["diff_covered_or_file_match"]], df.tail(5)])
        .drop_duplicates()
        .sort_index()
    )

    if len(df) > len(df_filtered) > 13:
        first_hidden_index = df_filtered.index[5]
        last_shown_index = df_filtered.index[-5]

        placeholder_row = pd.DataFrame(
            [
                {
                    "File": "..." * 3,
                    "Block": "",
                    "Start line": "...",
                    "End line": "...",
                    "Context length": "...",
                    "diff_covered_or_file_match": False,
                }
            ],
            index=[(first_hidden_index + last_shown_index) / 2],
        )

        df_filtered = pd.concat(
            [df_filtered.iloc[:5], placeholder_row, df_filtered.iloc[5:]]
        ).sort_index()

    def apply_highlighting(row):
        styles = ["" for _ in row]
        file_match = row["File"] in data["patch_files"]
        diff_covered = False

        if match_diff:
            file_diffs = (
                data.get("patch_diff_details", {}).get(row["File"], {}).get("diffs", [])
            )
            for diff in file_diffs:
                if (
                    row["Start line"] <= diff["end_line_old"]
                    and row["End line"] >= diff["start_line_old"]
                ):
                    diff_covered = True
                    break

        if diff_covered:
            styles = ["background-color: #4CAF50" for _ in row]
        elif file_match:
            styles = ["background-color: #C8E6C9" for _ in row]

        return styles

    column_styles = {
        "File": "width: 120px; max-width: 350px; overflow: hidden; text-overflow: ellipsis;",
        "Block": "width: 120px; max-width: 350px;",
        "Start line": "width: 80px; max-width: 80px;",
        "End line": "width: 80px; max-width: 80px;",
        "Context length": "width: 80px; max-width: 80px;",
    }
    styled_df = df_filtered.style.apply(apply_highlighting, axis=1).set_table_styles(
        [
            {"selector": f".col{i}", "props": f"{style}"}
            for i, (col, style) in enumerate(column_styles.items())
        ],
        overwrite=False,
    )

    display(styled_df)
