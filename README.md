# BMED4702 SQL Python AI and FHIR Labs

## Two executable laboratories with MIMIC-IV Demo 2.2

This package uses authentic deidentified data from the official MIMIC-IV Clinical Database Demo v2.2. Lab 1 covers SQL, Python, provenance, and guarded natural-language querying. Lab 2 converts the same real creatinine series to HL7 FHIR R4 Observation resources. These are engineering exercises; they do not support diagnosis, treatment, prevalence, or model-performance claims.

## Learning outcomes

After the lab, a student can:

1. convert selected official `.csv.gz` tables into a local SQLite database;
2. connect PyCharm to the same database used by Python;
3. execute a parameterized SQL query for one creatinine time series;
4. verify the result in Python and create a chart;
5. record data, query, code, and output provenance;
6. use an optional AI narrator without treating generated text as evidence;
7. reject unsafe generated SQL before execution;
8. map source identifiers, times, terminology, quantities, and provenance to FHIR R4.

## Files

```text
BMED4702_SQL_Python_AI_FHIR_Labs/
|-- data/
|   |-- mimic_demo.sqlite              prepared classroom database
|   |-- official_metadata/             PhysioNet license, README, checksums
|   `-- README.md
|-- output/                             generated CSV, PNG, JSON, and provenance
|-- examples/nl_sql_questions.txt       accepted and rejected prompt examples
|-- sql/
|   |-- 01_table_counts.sql
|   |-- 02_creatinine_timeline.sql
|   `-- 03_wrong_and_correct_join.sql
|-- src/
|   |-- ai_explain.py
|   |-- build_sqlite.py
|   |-- db.py
|   |-- fhir_observation.py
|   |-- lab_creatinine.py
|   |-- provenance.py
|   `-- safe_nl_sql.py
|-- tests/                              SQL, security, and FHIR checks
|-- .env.example
|-- requirements.txt
|-- run_lab.py
|-- run_safe_nl_sql.py
`-- run_fhir_lab.py
```

## PyCharm setup

1. Extract this folder and open it as a PyCharm project.
2. Select **File > Settings > Project > Python Interpreter**.
3. Create a virtual environment using Python 3.11 or later.
4. Open the PyCharm terminal and run:

```bash
python -m pip install -r requirements.txt
python run_lab.py
```

The program reads `data/mimic_demo.sqlite`, runs the SQL file, writes a CSV, creates a PNG chart, computes a JSON evidence summary, and records a provenance manifest.

Run all automated checks with `python -m unittest discover -s tests -v`.

## Two ways to use SQL in PyCharm

### Method A: SQL through Python

Python includes the `sqlite3` module. No database server or separate SQLite installation is required.

```python
import sqlite3

with sqlite3.connect("data/mimic_demo.sqlite") as con:
    rows = con.execute(
        "SELECT COUNT(*) FROM labevents WHERE itemid = ?",
        (50912,),
    ).fetchone()
```

The `?` placeholder keeps values separate from SQL text. This prevents accidental quoting errors and is the correct basis for safe parameterized queries.

### Method B: PyCharm Pro Database tool window

JetBrains documents the Database settings as a PyCharm Pro feature. If the
**Database** tool window is absent, use Method A; the Python lab is complete and
does not depend on the Pro interface. DB Browser for SQLite is an optional free
visual alternative.

1. Open **View > Tool Windows > Database**.
2. Select **New > Data Source > SQLite**.
3. Choose `data/mimic_demo.sqlite` as the database file.
4. Download the SQLite driver if PyCharm requests it.
5. Test the connection.
6. Right-click the data source and open a new query console.
7. Paste `sql/02_creatinine_timeline.sql`, replace the named parameters with values for manual execution, and run it.

The SQL console and Python point to the same file. Python automates the analysis. The SQL console helps students inspect tables, columns, and intermediate results.

## Rebuild SQLite from the official download

The included prepared database contains four teaching tables. To reproduce it from the official download:

```bash
python -m src.build_sqlite \
  "C:/path/to/mimic-iv-clinical-database-demo-2.2" \
  --output data/mimic_demo_rebuilt.sqlite
```

The source directory must contain:

```text
hosp/patients.csv.gz
hosp/admissions.csv.gz
hosp/d_labitems.csv.gz
hosp/labevents.csv.gz
```

The builder streams compressed CSV rows into SQLite, creates indexes, and verifies the four expected row counts.

## Creatinine lab question

For deidentified subject `10035631` during admission `29276678`:

- retrieve numeric creatinine events (`itemid=50912`);
- keep chart time and store time separate;
- compute availability lag in minutes;
- retain the reference range and source flag;
- preserve one output row per laboratory event;
- summarize the series without making a diagnosis.

Expected engineering facts:

- 36 numeric creatinine rows;
- observed range 1.0 to 5.3 mg/dL;
- 31 rows carry the source flag `abnormal`;
- average availability lag is approximately 90.14 minutes.

## Provenance in this lab

Provenance records how an output came into existence. The manifest links:

- the database file and its SHA-256 hash;
- the SQL file and query hash;
- the parameter values;
- the Python script and interpreter version;
- generated CSV, PNG, and JSON files with their hashes;
- start and end times for the analysis activity.

This lets another person answer: Which data version, query, code, parameters, and software produced this chart?

A hash supports identity and change detection. It does not prove that the query or clinical interpretation is correct.

## Optional AI narrator

`src/ai_explain.py` receives only the aggregate evidence summary. It does not receive patient identifiers, admission identifiers, or row-level events.

Without configuration, the lab writes a deterministic explanation. To enable the optional API path:

1. Copy `.env.example` to `.env`.
2. Set `AI_ENABLED=true`, `OPENAI_API_KEY`, and an available `OPENAI_MODEL`.
3. Run `python run_lab.py` again.

The program rejects generated text that introduces unsupported numeric claims. The SQL output, tests, and provenance manifest remain authoritative.

## Guarded natural language to SQL

The default mode uses deterministic question templates, so no network service is needed:

```bash
python run_safe_nl_sql.py "How many admissions are in the demo?"
python run_safe_nl_sql.py \
  "Show the creatinine timeline for subject 10035631 and admission 29276678"
```

The execution boundary combines a read-only database URI, SQLite `query_only`,
single-statement validation, a default-deny SQLite authorizer, table/column/function
allowlists, a row limit, a progress timeout, and an audit record. SQL comments,
DDL, DML, PRAGMA, ATTACH, multiple statements, unapproved functions, and unapproved
columns are rejected. The decision and query hash are written to
`output/query_audit.json`.

To experiment with model-generated candidate SQL, install `requirements-ai.txt`,
set `AI_SQL_ENABLED=true`, and configure the same API variables used by the narrator.
The model receives the approved schema and question, not patient rows. Generated SQL
is still subject to every local control above.

## Lab 2 FHIR Observation conversion

Run:

```bash
python run_fhir_lab.py --timezone-offset +00:00
```

MIMIC timestamps do not contain a timezone. The selected serialization offset is
therefore recorded as an explicit teaching assumption together with the original
source timestamp.

The command writes:

- `fhir_creatinine_bundle.json`: Patient, Encounter, Device, 36 Observations, and Provenance;
- `fhir_observation_example.json`: one readable example;
- `fhir_mapping_report.csv`: source-to-FHIR decisions;
- `fhir_validation_report.json`: executable checks and warnings.

Mapping decisions include:

- `fluid=Blood` uses LOINC `38483-4`, rather than the narrower serum/plasma code `2160-0`;
- `mg/dL` uses the UCUM code system;
- `charttime` maps to `effectiveDateTime`, while `storetime` maps to `issued`;
- `Observation.status=unknown` because the source table does not provide a FHIR result status;
- the source `abnormal` flag maps to interpretation code `A`;
- FHIR Provenance targets all generated Observations and records the database hash and converter.

## Where React and TypeScript fit

React and TypeScript are an optional interface layer after the verified Python
evidence and API layers. The browser must not open the SQLite file or execute
generated SQL. A future FastAPI service exposes limited typed endpoints; React
renders the chart, evidence, provenance, FHIR Observation, and guarded-query status.

React and TypeScript are installed as project-local npm dependencies. Only Node.js
must be installed on computers that will run the frontend. Students completing only
the SQL and Python lab do not need Node.js. See `REACT_TYPESCRIPT_SETUP_TR.md` for the
installation decision table and commands.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests check table counts, row grain, real expected values, join inflation, SQL security rejections, FHIR mappings, Observation count, and Provenance coverage.

## Core references

- Johnson AEW et al. MIMIC-IV. *Scientific Data*. 2023. DOI: 10.1038/s41597-022-01899-x.
- Johnson AEW et al. MIMIC-IV Clinical Database Demo v2.2. PhysioNet. DOI: 10.13026/dp1f-ex47.
- Johnson AEW et al. The MIMIC Code Repository. *JAMIA*. 2018. DOI: 10.1093/jamia/ocx084.
- Lee G et al. EHRSQL. *NeurIPS Datasets and Benchmarks*. 2022.
- Shi W et al. EHRAgent. *EMNLP*. 2024. DOI: 10.18653/v1/2024.emnlp-main.1245.
- Lekadir K et al. FUTURE-AI. *BMJ*. 2025. DOI: 10.1136/bmj-2024-081554.
- HL7 International. *FHIR R4 Observation and Provenance resources*. Version 4.0.1.
- Regenstrief Institute. LOINC 38483-4, *Creatinine [Mass/volume] in Blood*.
- UCUM. *The Unified Code for Units of Measure*.
