from db.db import db

subjects = [
    (
        "Project Management",
        "learn about being a good PM, agile, waterfall & hybrid",
        True,
    ),
    (
        "Southeast Asia Economy",
        "In the study of Southeast Asia, Politics and Uneven Development under Hyperglobalisation, comparative politics and orthodox economics.",
        True,
    ),
    (
        "Spanish History",
        "Interesting Stories, Spanish History & Random Facts About Spain.",
        True,
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
db.clear_user_subjects(user_id=user_id)
db.add_user_subject(user_id=user_id, subject="Southeast Asia Economy")
db.add_user_subject(user_id=user_id, subject="Project Management")
db.add_user_subject(user_id=user_id, subject="Spanish History")
