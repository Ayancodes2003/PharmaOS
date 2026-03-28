# Alembic Migrations

Alembic is configured for PHARMA-OS in Phase 3.

- Runtime configuration is in `alembic.ini`.
- Environment wiring is in `alembic/env.py` and uses `pharma_os.db.target_metadata`.
- Revision template is in `alembic/script.py.mako`.
- Generated revisions are stored in `alembic/versions`.

## Finalization Commands

Run from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
alembic revision --autogenerate -m "phase3_initial_schema"
alembic upgrade head
```

If autogeneration fails, verify:

- `alembic.ini` has `prepend_sys_path = ./src`
- `.env` contains valid PostgreSQL settings
- dependencies `pydantic-settings` and `psycopg2-binary` are installed in the active virtual environment
