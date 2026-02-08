# MediSmart
A smart, user-friendly medicine ordering website with personalization, discounts, reminders, and an AI-powered assistant (non-diagnostic).

## Quick Start (OTP Login Demo)
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the Flask app:
   ```bash
   python run.py
   ```
3. Open `http://localhost:5000` and request an OTP.
   - OTP is **simulated** and logged to the server console.
   - OTP expires in 30 seconds.
   - Maximum of 3 verification attempts per OTP.

## Folder Structure
```
MediSmart/
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── db.py
│   ├── static/
│   │   └── css/
│   │       └── styles.css
│   └── templates/
│       ├── dashboard.html
│       └── login.html
├── run.py
├── requirements.txt
└── README.md
```

## Safety Notice
This system does not provide medical diagnosis or prescriptions. Always consult a licensed doctor for medical advice.
