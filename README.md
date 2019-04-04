# c1assessmenttool

To run the service (from within this directory):
1. Install Dependencies: `python3 -m pip install requests django`
2. Migrate database: `python3 manage.py migrate`
3. Run server: `python3 manage.py runserver`

To run test script against running server (assumes service is running locally on port 8000:
`python3 test_script.py`
