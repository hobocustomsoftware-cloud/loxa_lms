import os
from uuid import uuid4


def asset_upload_to(instance, filename: str) -> str:
    """
    /org/<id>/course/<id>/lesson/<id>/asset/<uuid>/source/<safe_name.ext>
    """
    org_id = getattr(getattr(instance, "org", None), "id", None) or "noorg"
    # Walk up relations safely:
    lesson = instance.lesson
    module = lesson.module
    course = module.course
    course_id = getattr(course, "id", "nocourse")
    lesson_id = getattr(lesson, "id", "nolesson")

    name, ext = os.path.splitext(filename)
    safe = name.replace("..","").replace("/", "_")
    uid = uuid4().hex
    return f"org/{org_id}/course/{course_id}/lesson/{lesson_id}/asset/{uid}/source/{safe}{ext}"
