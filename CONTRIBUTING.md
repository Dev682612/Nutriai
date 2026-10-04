# Contributing

Thanks for helping improve NutriAI. Keep changes focused, describe user-visible behavior, and avoid committing generated or licensed data.

## Development setup

Use Python 3.10 or newer. Create and activate a virtual environment, then install the project dependencies as shown in the [README](README.md#quick-start).

## Before opening a change

Run the unit tests:

```powershell
python -m unittest discover -s tests -v
```

For API or dashboard changes, also start the app with `python -m uvicorn api.main:app --reload` and check the affected workflow in the browser and `/docs`.

## Keep out of commits

- Food-101 downloads and other images or datasets.
- Trained model checkpoints and downloaded pretrained weights.
- SQLite databases, application logs, virtual environments, and cache files.
- Credentials, `.env` files, and private user data.

Food-101 image rights remain with their respective owners. Review the dataset agreement and obtain any permissions required for your use.