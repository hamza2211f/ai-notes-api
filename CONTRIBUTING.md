# Contributing

Thanks for considering a contribution!

## Set up dev
1. Python 3.11 recommended
2. `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. `cp .env.example .env` and fill values
5. Start Postgres locally and create the database in `.env`

## Conventions
- Black/PEP8 style (run `black .` if you use it)
- Small PRs, clear commit messages
- Add/keep/update docstrings

## Tests (coming soon)
- `pytest -q`
