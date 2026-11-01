# Day 25 — Automated Scholarship Extraction Prototype

## Before you start
1. Back up your existing project.
2. Copy the `src/automation` folder and `tests/test_automation.py` into your existing project root.
3. Do not replace your existing files or insert extracted records into your SQLite database automatically.

## Install dependencies
Run these commands in PowerShell from your existing project root, with your project's virtual environment activated:

```powershell
python -m pip install requests beautifulsoup4 feedparser apscheduler
python -c "import requests, bs4, feedparser; print('Installation successful')"
```

`feedparser` and `apscheduler` are installed for later work; Day 25 only needs `requests` and `beautifulsoup4`.

## Create output folders
```powershell
New-Item -ItemType Directory -Force data/automation/pending_review
New-Item -ItemType Directory -Force data/automation/approved
New-Item -ItemType Directory -Force data/automation/logs
```

## Configure official sources
Open `src/automation/source_registry.py`. The example is the National Scholarship Portal homepage, which may not expose individual scheme details. Add individual official scheme pages only after checking the URL and permitted access. Give each source a unique `source_id`.

## Run tests
From the project root:
```powershell
python -m unittest discover -s tests -v
```
Expected: four tests pass.

## Run the bot
```powershell
python src/automation/run_bot.py
```

Review generated JSON records in `data/automation/pending_review/` and the log at `data/automation/logs/extraction_bot.log`.

## What the statuses mean
- `needs_review`: one or more basic checks found missing data.
- `ready_for_review`: basic fields were detected; a human still must verify the facts.
- `verification_status: pending_review`: every extracted record needs manual checking.
- `possible_duplicate`: a saved record had the same normalized name or URL.

## Limitations
This prototype supports ordinary HTML pages only. It does not parse PDFs, render JavaScript-only pages, independently verify facts, or update the live database. Do not bypass access controls. One failed source should not prevent the remaining sources from being processed.
