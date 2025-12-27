import pandas as pd

from eda_cli.core import compute_quality_flags, missing_table, summarize_dataset


def test_has_constant_columns_flag() -> None:
    df = pd.DataFrame(
        {
            "const_col": [1, 1, 1, 1],
            "var_col": [1, 2, 3, 4],
        }
    )
    summary = summarize_dataset(df)
    miss = missing_table(df)
    flags = compute_quality_flags(summary, miss, df)

    assert flags["has_constant_columns"] is True
    assert "const_col" in flags["constant_columns"]
    assert "var_col" not in flags["constant_columns"]


def test_high_cardinality_categoricals_flag() -> None:
    # 60 уникальных значений -> при пороге 50 должно сработать
    df = pd.DataFrame({"cat": [f"v{i}" for i in range(60)], "x": list(range(60))})
    summary = summarize_dataset(df)
    miss = missing_table(df)
    flags = compute_quality_flags(summary, miss, df, high_cardinality_threshold=50)

    assert flags["has_high_cardinality_categoricals"] is True
    assert "cat" in flags["high_cardinality_columns"]
