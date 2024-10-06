from db.db import db

subjects = [
    (
        "Project Management",
        "learn about being a good PM, agile, waterfall & hybrid",
        True,
    ),
    (
        "Economy",
        "Learn about the state of a country or region in terms of the production and consumption of goods and services and the supply of money",
        False,
    ),
    (
        "Geography",
        "Geography is a branch of inquiry that focuses on spatial information on Earth. It is an extremely broad topic and can be broken down multiple ways.",
        False,
    ),
]


res = db.get_all_subjects_info()
print(res)

# add the new subject if not exist
for subject in subjects:
    if subject[0] not in [r["subject_name"] for r in res]:
        db.add_subject_info(*subject)

# enrolling the user
user_id = 1624490023
# db.clear_user_subjects(user_id)
db.add_user_subject(user_id=user_id, subject="Economy")
