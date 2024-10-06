import uuid


def test_add_subject_info(db):
    """Test inserting and querying subject_info with new fields."""
    subject_name = "Mathematics"
    subject_description = "Study of numbers and shapes"
    use_datasource = True
    tags = ["algebra", "geometry"]
    subject_id = db.add_subject_info(
        subject_name=subject_name,
        subject_description=subject_description,
        use_datasource=use_datasource,
        tags=tags,
    )
    # Query the subject by ID
    subject_info = db.get_subject_info_by_id(subject_id)
    assert subject_info is not None
    assert subject_info["subject_name"] == subject_name
    assert subject_info["subject_description"] == subject_description
    assert subject_info["use_datasource"] == use_datasource
    assert subject_info["tags"] == tags
    # Check that subject_key is a valid UUID
    assert uuid.UUID(subject_info["subject_key"])


def test_get_subject_info_by_subject_key(db):
    """Test retrieving subject_info by subject_key."""
    subject_name = "Physics"
    subject_description = "Study of matter and energy"
    use_datasource = False
    tags = ["mechanics", "thermodynamics"]
    subject_id = db.add_subject_info(
        subject_name=subject_name,
        subject_description=subject_description,
        use_datasource=use_datasource,
        tags=tags,
    )
    # Get subject_info by ID to retrieve the subject_key
    subject_info = db.get_subject_info_by_id(subject_id)
    subject_key = subject_info["subject_key"]
    # Retrieve by subject_key
    subject_info_by_key = db.get_subject_info_by_subject_key(subject_key)
    assert subject_info_by_key is not None
    assert subject_info_by_key["id"] == subject_id
    assert subject_info_by_key["subject_name"] == subject_name
    assert subject_info_by_key["subject_description"] == subject_description
    assert subject_info_by_key["use_datasource"] == use_datasource
    assert subject_info_by_key["tags"] == tags


def test_get_all_subjects_info(db):
    """Test retrieving all subjects info."""
    # Clear any existing subjects
    db.conn.execute("DELETE FROM subject_info")
    # Add multiple subjects
    db.add_subject_info(
        subject_name="Math",
        subject_description="Numbers",
        use_datasource=True,
        tags=["algebra"],
    )
    db.add_subject_info(
        subject_name="Biology",
        subject_description="Life sciences",
        use_datasource=False,
        tags=["cells", "organisms"],
    )
    subjects = db.get_all_subjects_info()
    assert len(subjects) == 2


def test_update_subject_info_by_id(db):
    """Test updating subject_info by ID."""
    subject_name = "Chemistry"
    subject_description = "Study of substances"
    use_datasource = True
    tags = ["organic", "inorganic"]
    subject_id = db.add_subject_info(
        subject_name=subject_name,
        subject_description=subject_description,
        use_datasource=use_datasource,
        tags=tags,
    )
    # Update the subject_info
    new_description = "Study of chemicals"
    new_tags = ["analytical", "physical"]
    db.update_subject_info_by_id(
        subject_id, subject_description=new_description, tags=new_tags
    )
    # Retrieve and check
    updated_info = db.get_subject_info_by_id(subject_id)
    assert updated_info["subject_description"] == new_description
    assert updated_info["tags"] == new_tags


def test_delete_subject_info_by_id(db):
    """Test deleting subject_info by ID."""
    subject_name = "Astronomy"
    subject_description = "Study of celestial objects"
    use_datasource = False
    tags = ["stars", "planets"]
    subject_id = db.add_subject_info(
        subject_name=subject_name,
        subject_description=subject_description,
        use_datasource=use_datasource,
        tags=tags,
    )
    # Delete the subject_info
    db.delete_subject_info_by_id(subject_id)
    # Attempt to retrieve
    deleted_info = db.get_subject_info_by_id(subject_id)
    assert deleted_info is None
