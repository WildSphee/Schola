"""
This file defines the pipeline names, NOT the display name on the Telegram but how they are referred
to with in the code repo.

If you have to refer to a pipeline, import them like this

```py
from utils.const import QUIZ_PIPELINE
from db.db import db

db.set_user_pipeline(user_id, QUIZ_PIPELINE)
```
"""

QUIZ_PIPELINE = "quiz"
QA_PIPELINE = "qa"
SUBJECT_SELECT_PIPELINE = "subject_select"
DEFAULT_PIPELINE = "default"
CONFIG_PIPELINE = "config"
