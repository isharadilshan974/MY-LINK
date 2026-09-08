# MY LINK — Next Level

**Social Media → Campaign → Lead → CRM → Analytics → AI → Creator → Revenue**

A Streamlit-first business growth platform built from the MY LINK concept. It includes a polished dashboard, lead CRM, campaign landing pages, source attribution, analytics, local AI-style lead scoring, creator referrals, team workspace, notifications/follow-ups, subscriptions and deployment settings.

## Run locally
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Demo login:
- Email: `demo@mylink.local`
- Password: `demo1234`

## GitHub + Streamlit Cloud
1. Create a GitHub repository and upload `app.py`, `requirements.txt`, `README.md`, and `.streamlit/config.toml`.
2. In Streamlit Community Cloud, select the repository and `app.py` as the main file.
3. For cloud persistence, create a Supabase project and add `SUPABASE_URL` and `SUPABASE_KEY` as Streamlit Secrets. The current app has a local SQLite fallback for testing.

> Note: SQLite on Streamlit Cloud is not durable across app restarts/redeployments. Use Supabase/PostgreSQL for production multi-device data.

## Production integrations
Real social publishing/reading, WhatsApp/SMS sending, payments and external AI are not faked. They require official provider accounts, OAuth/access tokens and secrets. The app is structured so those integrations can be added safely.
