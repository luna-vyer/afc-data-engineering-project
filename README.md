This project implements a data engineering pipeline for AFC (Armoric Fried Chicken).

## Objectives
- Ingest sales data (CSV)
- Collect marketing feedback data (JSON via API)
- Process and analyze customer sentiment
- Provide sales and marketing dashboards

## Push data
To push data, use this script: https://github.com/Prjprj/api_pusher.
Change `#endpoint_url = http://localhost:8080/afc/api` to `endpoint_url = http://localhost:8000/feedback` in the configg.ini file.



To start the API, use `uvicorn src.api.main:app --reload` from the project root.