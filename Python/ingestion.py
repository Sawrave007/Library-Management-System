import csv
import re
from datetime import datetime
from pathlib import Path

import pyodbc


# ============================================================
# CONFIGURATION
# ============================================================

CLEANED_FOLDER = Path(r"E:\Projects\SQL\Project 2\cleaned")

SERVER = "localhost"
DATABASE = "LibraryDB"
DRIVER = "ODBC Driver 18 for SQL Server"

SCHEMA_NAME = "raw"

# How many data rows to scan per column when guessing types.
# Set to None to scan the entire file (safer, slower on huge files).
SAMPLE_ROWS = 50_000

# Fallback text column sizing
MIN_VARCHAR_LEN = 50
MAX_VARCHAR_LEN = 4000   # beyond this, NVARCHAR(MAX) is used
VARCHAR_BUFFER = 1.3     # pad observed max length by this factor

TRUNCATE_EXISTING = True

# Formats checked (in order) when a column looks like a date/time.
# All values in the column must match the SAME format to qualify —
# this avoids silently misreading ambiguous dates like 01/02/2024.
DATE_FORMATS = [
    ("%Y-%m-%d", "DATE"),
    ("%Y/%m/%d", "DATE"),
    ("%m/%d/%Y", "DATE"),
    ("%d/%m/%Y", "DATE"),
    ("%d-%m-%Y", "DATE"),
    ("%m-%d-%Y", "DATE"),
    ("%Y-%m-%d %H:%M:%S", "DATETIME2"),
    ("%Y-%m-%dT%H:%M:%S", "DATETIME2"),
    ("%m/%d/%Y %H:%M:%S", "DATETIME2"),
    ("%d/%m/%Y %H:%M:%S", "DATETIME2"),
]


# ============================================================
# IDENTIFIER HELPERS
# ============================================================

def sanitize_identifier(name: str) -> str:
    name = name.strip().lstrip("\ufeff")
    name = re.sub(r"\W+", "_", name)
    name = name.strip("_")
    if not name:
        name = "col"
    if name[0].isdigit():
        name = f"_{name}"
    return name.lower()


def dedupe_columns(columns: list[str]) -> list[str]:
    seen = {}
    result = []
    for col in columns:
        if col not in seen:
            seen[col] = 0
            result.append(col)
        else:
            seen[col] += 1
            result.append(f"{col}_{seen[col]}")
    return result


# ============================================================
# TYPE INFERENCE
# ============================================================

INT_RE = re.compile(r"^-?\d+$")
DECIMAL_RE = re.compile(r"^-?\d+\.\d+$")
LEADING_ZERO_RE = re.compile(r"^0\d+$")  # e.g. "00123" -> keep as text


def varchar_length_for(max_len: int) -> str:
    if max_len <= 0:
        max_len = 1
    padded = int(max_len * VARCHAR_BUFFER)
    padded = max(padded, MIN_VARCHAR_LEN)
    if padded > MAX_VARCHAR_LEN:
        return "NVARCHAR(MAX)"
    for step in (50, 100, 255, 500, 1000, 2000, 4000):
        if padded <= step:
            return f"NVARCHAR({step})"
    return "NVARCHAR(MAX)"


def detect_date_type(values: list[str]):
    for fmt, sql_type in DATE_FORMATS:
        try:
            for v in values:
                datetime.strptime(v, fmt)
            return sql_type
        except ValueError:
            continue
    return None


def infer_column_type(values: list[str]) -> str:
    non_null = [v.strip() for v in values if v is not None and v.strip() != ""]

    if not non_null:
        return f"NVARCHAR({MIN_VARCHAR_LEN})"

    max_len = max(len(v) for v in non_null)

    # ---- numeric check ----
    is_numeric = True
    has_fraction = False
    max_int_digits = 0
    max_frac_digits = 0

    for v in non_null:
        if LEADING_ZERO_RE.match(v):
            is_numeric = False
            break
        if INT_RE.match(v):
            digits = v.lstrip("-")
            max_int_digits = max(max_int_digits, len(digits))
        elif DECIMAL_RE.match(v):
            digits, frac = v.lstrip("-").split(".")
            max_int_digits = max(max_int_digits, len(digits))
            max_frac_digits = max(max_frac_digits, len(frac))
            has_fraction = True
        else:
            is_numeric = False
            break

    if is_numeric:
        if not has_fraction:
            try:
                max_abs_val = max(abs(int(v)) for v in non_null)
            except ValueError:
                max_abs_val = 0
            return "BIGINT" if max_abs_val > 2_147_483_647 else "INT"
        else:
            precision = min(max_int_digits + max_frac_digits, 38)
            scale = min(max_frac_digits, precision - 1 if precision > 0 else 0)
            precision = max(precision, scale + 1)
            return f"DECIMAL({precision},{scale})"

    # ---- date / datetime check ----
    date_type = detect_date_type(non_null)
    if date_type:
        return date_type

    # ---- fallback: text ----
    return varchar_length_for(max_len)


def read_and_infer(csv_path: Path):
    """Returns (columns, sql_types) for a CSV file."""
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        columns = dedupe_columns([sanitize_identifier(c) for c in header])

        col_values = {col: [] for col in columns}
        for i, row in enumerate(reader):
            if SAMPLE_ROWS is not None and i >= SAMPLE_ROWS:
                break
            for col, val in zip(columns, row):
                col_values[col].append(val)

    sql_types = [infer_column_type(col_values[col]) for col in columns]
    return columns, sql_types


def build_create_table_sql(schema: str, table: str, columns: list[str], types: list[str]) -> str:
    col_defs = ",\n            ".join(
        f"[{col}] {sql_type} NULL" for col, sql_type in zip(columns, types)
    )
    return f"""
        CREATE TABLE {schema}.{table} (
            {col_defs}
        )
    """


# ============================================================
# CONNECT TO SQL SERVER
# ============================================================

connection = pyodbc.connect(
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
cursor = connection.cursor()
print("Connected to SQL Server.")


# ============================================================
# CREATE RAW SCHEMA
# ============================================================

cursor.execute(f"""
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = '{SCHEMA_NAME}')
BEGIN
    EXEC('CREATE SCHEMA {SCHEMA_NAME}')
END
""")
connection.commit()
print(f"Schema '{SCHEMA_NAME}' is ready.")


# ============================================================
# DISCOVER CSV FILES
# ============================================================

csv_files = sorted(CLEANED_FOLDER.glob("*.csv"))
if not csv_files:
    print(f"No CSV files found in {CLEANED_FOLDER}")
    cursor.close()
    connection.close()
    raise SystemExit(0)

print(f"Found {len(csv_files)} CSV file(s).")


# ============================================================
# INFER TYPES, CREATE / RESET TABLES
# ============================================================

table_info = {}  # table_name -> (columns, types)

for csv_file in csv_files:
    table_name = sanitize_identifier(csv_file.stem)
    print(f"Scanning {csv_file.name} for column types...")
    columns, sql_types = read_and_infer(csv_file)
    table_info[table_name] = (columns, sql_types)

    for col, t in zip(columns, sql_types):
        print(f"    {col}: {t}")

    cursor.execute(f"""
        SELECT 1
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE s.name = '{SCHEMA_NAME}' AND t.name = '{table_name}'
    """)
    exists = cursor.fetchone() is not None

    if exists:
        # Types can drift between runs (a column that was clean before
        # might now have mixed data) so we always drop + recreate rather
        # than trust an old schema when using typed columns.
        cursor.execute(f"DROP TABLE {SCHEMA_NAME}.{table_name}")
        cursor.execute(build_create_table_sql(SCHEMA_NAME, table_name, columns, sql_types))
        print(f"Recreated {SCHEMA_NAME}.{table_name}")
    else:
        cursor.execute(build_create_table_sql(SCHEMA_NAME, table_name, columns, sql_types))
        print(f"Created table {SCHEMA_NAME}.{table_name}")

    connection.commit()


# ============================================================
# BULK INSERT EACH CSV
# ============================================================

for csv_file in csv_files:
    table_name = sanitize_identifier(csv_file.stem)
    file_path = str(csv_file).replace("'", "''")
    error_file = str(csv_file.with_suffix(".errors.log")).replace("'", "''")

    print(f"Loading {csv_file.name} -> {SCHEMA_NAME}.{table_name} ...")

    try:
        cursor.execute(f"""
            BULK INSERT {SCHEMA_NAME}.{table_name}
            FROM '{file_path}'
            WITH (
                FORMAT = 'CSV',
                FIRSTROW = 2,
                FIELDQUOTE = '"',
                CODEPAGE = '65001',
                MAXERRORS = 50,
                ERRORFILE = '{error_file}',
                TABLOCK
            )
        """)
        connection.commit()
        print(f"Loaded {SCHEMA_NAME}.{table_name}")
    except pyodbc.Error as e:
        print(f"WARNING: issues loading {table_name}: {e}")
        print(f"Check {error_file} for rejected rows (bad type conversions, etc.)")


# ============================================================
# VALIDATE ROW COUNTS
# ============================================================

print("\nRow counts:")
for table_name in table_info:
    cursor.execute(f"SELECT COUNT(*) FROM {SCHEMA_NAME}.{table_name}")
    row_count = cursor.fetchone()[0]
    print(f"{SCHEMA_NAME}.{table_name}: {row_count} rows")


# ============================================================
# CLOSE CONNECTION
# ============================================================

cursor.close()
connection.close()
print("\nIngestion completed successfully.")