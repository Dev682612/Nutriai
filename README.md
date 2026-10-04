# NutriAI

**A local-first nutrition dashboard for meal logging, daily targets, and food image classification.**

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![Database](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)

NutriAI combines a responsive web dashboard with a FastAPI service and a local SQLite food diary. Create a BMI-based daily target, log meals, review calories and macros, set meal reminders, and optionally train a Food-101 image classifier.

> **Project status:** The nutrition planner and manual meal logging work immediately. Food image classification is optional and becomes available after you train a model checkpoint.

## Features

- Responsive dashboard served by the API at `http://127.0.0.1:8000/`.
- BMI and calorie-target estimates with configurable activity and goals.
- Per-serving nutrition lookups and meal logging backed by SQLite.
- Daily calories, macro progress, remaining targets, and meal history.
- Optional Food-101 ResNet50 training and image prediction.
- Local meal reminders through Windows desktop notifications.
- OpenAPI documentation at `/docs` and a health endpoint at `/health`.

## Quick start

Requires Python 3.10 or newer. From the project directory, run these commands in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the dashboard or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API docs. The API creates `data_store/nutriai.sqlite3` on startup. Stop the server with `Ctrl+C`.

To check the local test suite:

```powershell
python -m unittest discover -s tests -v
```

## Food image classification

The image classifier is not bundled with the source. Train it locally to create the checkpoint expected by the API, `models/nutriai_resnet50.pth`:

```powershell
python -m src.train --download --epochs 5 --batch-size 16
```

For a smaller experiment, select a few supported Food-101 classes:

```powershell
python -m src.train --download --classes pizza hamburger fried_rice --epochs 3
```

Training downloads Food-101 (about 5 GB extracted) and the pretrained ResNet50 weights. The backbone is frozen and the classifier head is trained; the best validation checkpoint is saved locally. Training uses CUDA when available, otherwise CPU. On Windows, `--workers 0` is the reliable default.

See [data/README.md](data/README.md) for dataset details. **Do not commit or redistribute downloaded dataset images.** The included Food-101 agreement states that images belong to their respective owners and that use beyond scientific fair use requires permission. Review the dataset's current terms before training or sharing results. Model checkpoints and local datasets are excluded by `.gitignore`.

## API overview

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/` | Serve the dashboard |
| `GET` | `/health` | Report API and model readiness |
| `POST` | `/bmi` | Calculate BMI and save a daily target |
| `POST` | `/log` | Add a known dish to the food diary |
| `GET` | `/summary?user_id=default` | Read today's totals and meal history |
| `POST` | `/predict` | Classify an uploaded image when a checkpoint is available |
| `POST` | `/reminders` | Configure local meal reminders |

Example: create or update the default user's daily plan:

```powershell
$body = @{
	user_id = "default"
	height_cm = 165
	weight_kg = 60
	age = 25
	sex = "female"
	activity_level = "moderate"
	goal = "maintain"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
	-Uri http://127.0.0.1:8000/bmi `
	-ContentType "application/json" `
	-Body $body
```

## Project layout

```text
api/                 FastAPI routes and the dashboard
data/                Dataset instructions; downloaded data stays local
data_store/          SQLite database created at runtime
models/              Locally trained model checkpoints
src/                 BMI, nutrition, tracking, training, and prediction logic
tests/               Standard-library unit tests
requirements.txt     Python runtime dependencies
```

## Privacy and limitations

This project is designed for local development, not public deployment. It has no authentication or user accounts; `user_id` is an identifier, not an access-control boundary. Do not expose the API to the internet or store sensitive personal information in it. The local SQLite database is not encrypted.

Nutrition values are estimates from a small bundled lookup table. BMI and calorie targets are general informational estimates, not medical advice or a substitute for guidance from a qualified professional.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks and contribution guidelines. The Food-101 dataset and image rights remain governed by their original terms; no dataset images are included in this repository.

## License

No software license has been selected for this project yet. The Food-101 dataset has separate terms and is not covered by a future license for this code.
