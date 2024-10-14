from typing import Literal

from db.db import db


def set_user_subjects(user_id: str, package: Literal["default"] = "default"):
    """
    Running this script will enroll the user to a the default subject package

    Attribute:
        user_id (str): the id of the user
        package (Literal["default"]): the package of lessons the user to be enrolled to, default is "default"
    """

    default_package = [
        (
            "Project Management",
            "learn about being a good PM, agile, waterfall & hybrid",
            True,
            [
                "A_Guide_to_the_Project_Management_Body_of_Knowledge_PMBOK_Project_Management_Institute_7_2021_Project_Management_Institute.pdf"
            ],
        ),
        (
            "Southeast Asia Economy",
            "In the study of Southeast Asia, Politics and Uneven Development under Hyperglobalisation, comparative politics and orthodox economics.",
            True,
            ["The_Political_Economy_of_Southeast_Asia__Politics_and_Uneven.pdf"],
        ),
        (
            "Spanish History",
            "Interesting Stories, Spanish History & Random Facts About Spain.",
            True,
            ["The_Great_Book_of_Spain__Interesting_Stories,_Spanish.pdf"],
        ),
    ]

    db.clear_user_subjects(user_id=user_id)

    # add the new subject if not exist
    res = db.get_all_subjects_info()

    # set subject package
    if package == "default":
        for subject in default_package:
            if subject[0] not in [r["subject_name"] for r in res]:
                db.add_subject_info(*subject)

            db.add_user_subject(user_id=user_id, subject=subject[0])

    return db.get_all_subjects_info()
