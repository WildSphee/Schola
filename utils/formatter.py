def subject_code_from_subject_name(name: str) -> str:
    """
    Running this will turn the subject name to the subject code
    Usually turns all the space into underscore
    """

    return name.replace(" ", "_")
