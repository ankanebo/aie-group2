from __future__ import annotations

from io import BytesIO
from time import perf_counter
from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .core import compute_quality_flags, missing_table, summarize_dataset
from . import __version__

app = FastAPI(
    title="eda-cli API",
    description="HTTP-сервис качества датасетов поверх eda-cli",
    version=__version__,
)


class DatasetShape(BaseModel):
    n_rows: int = Field(..., ge=0)
    n_cols: int = Field(..., ge=0)


class QualityRequest(BaseModel):
    n_rows: int = Field(..., ge=0)
    n_cols: int = Field(..., ge=0)
    max_missing_share: float = Field(..., ge=0.0, le=1.0)
    numeric_cols: int = Field(..., ge=0)
    categorical_cols: int = Field(..., ge=0)


class QualityResponse(BaseModel):
    ok_for_model: bool
    quality_score: float
    message: str
    latency_ms: float
    flags: Dict[str, Any]
    dataset_shape: DatasetShape


def _read_upload_csv(file: UploadFile) -> pd.DataFrame:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Пустое имя файла")
    try:
        content = file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Пустой CSV-файл")
        return pd.read_csv(BytesIO(content))
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Не удалось прочитать CSV: {exc}") from exc


def _quality_response_from_df(df: pd.DataFrame, latency_ms: float) -> QualityResponse:
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)
    quality_score = float(flags.get("quality_score", 0.0))
    ok_for_model = quality_score >= 0.6 and not flags.get("too_many_missing", False)
    message = "ok" if ok_for_model else "dataset may be problematic"

    return QualityResponse(
        ok_for_model=ok_for_model,
        quality_score=quality_score,
        message=message,
        latency_ms=latency_ms,
        flags=flags,
        dataset_shape=DatasetShape(n_rows=summary.n_rows, n_cols=summary.n_cols),
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "eda-cli", "version": __version__}


@app.post("/quality", response_model=QualityResponse)
def quality(req: QualityRequest) -> QualityResponse:
    start = perf_counter()

    score = 1.0
    score -= req.max_missing_share
    if req.n_rows < 100:
        score -= 0.2
    if req.n_cols > 100:
        score -= 0.1
    if req.numeric_cols == 0:
        score -= 0.1
    if req.categorical_cols == 0:
        score -= 0.05

    score = max(0.0, min(1.0, score))
    flags = {
        "too_few_rows": req.n_rows < 100,
        "too_many_columns": req.n_cols > 100,
        "max_missing_share": req.max_missing_share,
    }
    ok_for_model = score >= 0.6 and req.max_missing_share <= 0.5
    message = "ok" if ok_for_model else "dataset may be problematic"
    latency_ms = (perf_counter() - start) * 1000

    return QualityResponse(
        ok_for_model=ok_for_model,
        quality_score=score,
        message=message,
        latency_ms=latency_ms,
        flags=flags,
        dataset_shape=DatasetShape(n_rows=req.n_rows, n_cols=req.n_cols),
    )


@app.post("/quality-from-csv", response_model=QualityResponse)
def quality_from_csv(file: UploadFile = File(...)) -> QualityResponse:
    start = perf_counter()
    df = _read_upload_csv(file)
    latency_ms = (perf_counter() - start) * 1000
    return _quality_response_from_df(df, latency_ms)


@app.post("/quality-flags-from-csv")
def quality_flags_from_csv(file: UploadFile = File(...)) -> Dict[str, Dict[str, Any]]:
    df = _read_upload_csv(file)
    summary = summarize_dataset(df)
    missing_df = missing_table(df)
    flags = compute_quality_flags(summary, missing_df, df)
    return {"flags": flags}
