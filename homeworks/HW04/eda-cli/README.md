# S04 – eda_cli: мини-EDA для CSV + HTTP API

Небольшое CLI-приложение для базового анализа CSV-файлов.
Используется в рамках Семинара 04 курса «Инженерия ИИ».

## Требования

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) установлен в систему

## Инициализация проекта

В корне проекта (S04):

```bash
uv sync
```

Эта команда:

- создаст виртуальное окружение `.venv`;
- установит зависимости из `pyproject.toml`;
- установит сам проект `eda-cli` в окружение.

## Запуск CLI

### Краткий обзор

```bash
uv run eda-cli overview data/example.csv
```

Параметры:

- `--sep` – разделитель (по умолчанию `,`);
- `--encoding` – кодировка (по умолчанию `utf-8`).

### Полный EDA-отчёт

```bash
uv run eda-cli report data/example.csv --out-dir reports
```

Дополнительные параметры отчёта:

- `--max-hist-columns` — сколько числовых колонок строить в гистограммах;
- `--top-k-categories` — сколько top-значений сохранять для категориальных признаков;
- `--title` — заголовок отчёта (первая строка `report.md`);
- `--min-missing-share` — порог доли пропусков для списка «проблемных» колонок.

Пример с параметрами:

```bash
uv run eda-cli report data/example.csv --out-dir reports_example \
  --max-hist-columns 4 --top-k-categories 3 --title "S04 report" --min-missing-share 0.3
```

В результате в каталоге `reports/` появятся:

- `report.md` – основной отчёт в Markdown;
- `summary.csv` – таблица по колонкам;
- `missing.csv` – пропуски по колонкам;
- `correlation.csv` – корреляционная матрица (если есть числовые признаки);
- `top_categories/*.csv` – top-k категорий по строковым признакам;
- `hist_*.png` – гистограммы числовых колонок;
- `missing_matrix.png` – визуализация пропусков;
- `correlation_heatmap.png` – тепловая карта корреляций.

## Тесты

```bash
uv run pytest -q
```

## HTTP API

Запуск сервиса:

```bash
uv run uvicorn eda_cli.api:app --reload --port 8000
```

Эндпоинты:

- `GET /health` — проверка доступности сервиса.
- `POST /quality` — эвристическая оценка качества по агрегированным параметрам.
- `POST /quality-from-csv` — оценка качества на основе CSV-файла.
- `POST /quality-flags-from-csv` — полный набор флагов качества из HW03.

Примеры:

```bash
curl -s http://127.0.0.1:8000/health
```

```bash
curl -s -X POST http://127.0.0.1:8000/quality \
  -H "Content-Type: application/json" \
  -d '{"n_rows": 120, "n_cols": 8, "max_missing_share": 0.1, "numeric_cols": 4, "categorical_cols": 4}'
```

```bash
curl -s -X POST http://127.0.0.1:8000/quality-from-csv \
  -F "file=@data/example.csv"
```

```bash
curl -s -X POST http://127.0.0.1:8000/quality-flags-from-csv \
  -F "file=@data/example.csv"
```
