# c1assessmenttool

To run the service (from within this directory):
1. Install Dependencies: `python3 -m pip install requests django`
2. Migrate database: `python3 manage.py migrate`
3. Run server: `python3 manage.py runserver`

To run test script against running server (assumes service is running locally on port 8000:
`python3 test_script.py`


Next steps:
- Add database fields and API functionality to support non-text object upload / retrieval (such as images).
- I added a few to-dos where I would improve on existing logic and/or satisfy additional requirements. I also did not yet populate every database field that I included.
- Better standardize API and DB field names.

Architecture Considerations:
- Use MongoDB instead of a relational database, since the document-based nature of MongoDB records works well with the one-to-many relationships between User, Assessment, Attempts, etc.
- Consider a microservice-based architecture, where Users and Assessments are loosely coupled and handled independently. This would also allow for additional features associated with a User, such as a course or certification.
