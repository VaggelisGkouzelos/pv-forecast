# ☀️ PV Forecast — Weather-driven ML forecasting for a 500 kW solar park

> 🇬🇷 **[Ελληνική έκδοση →](README.md)** · Code comments are in Greek.

An end-to-end machine learning pipeline that learns how **weather drives the output** of a real 500 kW
photovoltaic park in central Greece (Huawei FusionSolar data), and uses it to:

1. **Forecast** hourly energy production (kWh) for the next days from the weather forecast
2. **Learn from clean data** — hours when the park was curtailed or offline are detected and excluded from training, so the model learns the park's normal behaviour
3. **Report daily** to Telegram, fully automated with **n8n**

---

## 🎯 Key results

| | MAE (kWh/hour) | R² |
|---|---|---|
| Linear regression (irradiance only) — baseline | 35.4 | 0.860 |
| Random Forest (6 weather features) | 24.9 | 0.883 |
| **Random Forest + iterative data cleaning** | **18.7** | **0.943** |

*All models evaluated on the same 71 normal-operation hours of a chronologically held-out week (8–14 Oct 2026; no data leakage).
Cleaning cut the Random Forest error by 25%.*

**Data-quality check validated on reality:** with no labels, the cleaning step flagged **10 and 11 October 2026** as days when the park
produced almost nothing although the weather data showed irradiance of up to ~480 W/m² (on 11 Oct it output a flat
~0.55 kWh every hour). The owner confirmed the park was **offline on both days**.

*Forecast vs. actual on the held-out week (first model, before data cleaning) — the two flat-zero days are the outages:*

![Forecast vs actual](docs/images/apotelesmata_montelou.png)

*Example output — forecast for the next two days with uncertainty band:*

![Next days forecast](docs/images/provlepsi_avrio.png)

---

## 🧠 How it works

```
 Huawei FusionSolar           Open-Meteo API
 (hourly production, kWh)     (irradiance on tilted panel, direct/diffuse,
          │                    temperature, cloud cover)
          └──────────┬─────────┘
                     ▼
        02  Merge & align time windows
                     ▼
        03  Train Random Forest  ◄──┐  Data cleaning (improves the model):
            drop non-normal hours ──┘  out-of-fold predictions (GroupKFold by day),
                     │                 drop curtailed/offline hours (<20% of expected), retrain
                     ▼
        04  Forecast next days (+ uncertainty band from the 300 trees)
                     ▼
        05  Daily report (text)
                     ▼
        n8n runs 02→05 every morning at 07:30  ──►  Telegram
```

### Notable technical decisions
- **Chronological train/test split** — the model always predicts the future from the past.
- **Time alignment** — Open-Meteo values are interval-*ending* averages while FusionSolar rows are
  interval-*starting*; weather is shifted by one hour so both describe the same interval.
- **GroupKFold cross-validation by day** for anomaly flagging, so an hour is never judged by a model
  that has already seen it (or other hours of the same day).
- **Threshold tuning with a sanity check** — a 60% threshold flagged ~30% of hours and implied an
  unrealistic 45% loss (it confused weather-forecast errors with curtailment). A 20% threshold isolates
  true stoppages only.
- **Uncertainty estimation** — 10th–90th percentile of the individual tree predictions.
- **Privacy** — the park's exact location lives only in a local `.env`; the public code uses a rounded location.

### Feature importance (Random Forest, held-out evaluation model)
| Feature | Importance |
|---|---|
| Global tilted irradiance | 36.6% |
| Direct radiation | 27.7% |
| Diffuse radiation | 15.7% |
| Temperature | 12.5% |
| Cloud cover | 4.6% |
| Hour of day | 2.9% |

---

## 📁 Project structure

| File | What it does |
|---|---|
| `config.py` | Shared settings; reads the private `.env` |
| `01_kairos.py` | Downloads weather data and plots irradiance |
| `02_ekpaideusi.py` | Merges production + weather; trains baseline & Random Forest |
| `03_katharismos.py` | Data cleaning: removes curtailed/offline hours and retrains |
| `04_provlepsi.py` | Forecast for the next days with uncertainty band |
| `05_anafora.py` | Writes the short daily report (Greek) |
| `n8n_kathimerina.sh` | Runs the full pipeline (02→05); called by n8n |
| `n8n/pv_forecast_workflow.json` | n8n workflow: schedule → Python → Telegram |

---

## 🚀 Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # put your own coordinates here
# place FusionSolar "Plant Statistics Report by Time" .xlsx files in data/fusionsolar/
python3 02_ekpaideusi.py && python3 03_katharismos.py && python3 04_provlepsi.py && python3 05_anafora.py
```

**Automation:** import `n8n/pv_forecast_workflow.json` into n8n, set the script path, your Telegram
bot credential and chat ID, then publish. (n8n 2.x: enable the *Execute Command* node with the environment variable
`NODES_EXCLUDE="[]"`.)

> The park's production data is private and not included in this repository.

---

## 🗺️ Roadmap
- [x] Weather + production data pipeline
- [x] Random Forest forecasting with data cleaning & uncertainty band
- [x] Daily automation with n8n + Telegram
- [ ] Automatic ingestion of the daily FusionSolar e-mail (Gmail)
- [ ] **AI agent** (LLM) that explains the daily forecast and any unusual day in plain language
- [ ] Cloud deployment (GitHub Actions) so it runs 24/7
- [ ] Longer history (seasonality) and more weather features
- [ ] Error notifications

## 🛠️ Tech stack
Python · pandas · scikit-learn · matplotlib · REST APIs (Open-Meteo) · n8n · Telegram Bot API

## 👤 Author
**Vaggelis Gkouzelos** — Mathematics graduate, MSc student in Advanced Computer Systems (AI & Software Development), University of Piraeus.
