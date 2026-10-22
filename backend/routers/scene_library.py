from fastapi import APIRouter, HTTPException

from ..scene_library import (
    get_environment,
    get_object,
    get_template,
    list_environments,
    list_objects,
    list_templates,
)

router = APIRouter(prefix="/scene-library", tags=["scene-library"])


@router.get("/templates")
def read_templates():
    return list_templates()


@router.get("/templates/{slug}")
def read_template(slug: str):
    t = get_template(slug)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.get("/environments")
def read_environments():
    return list_environments()


@router.get("/environments/{slug}")
def read_environment(slug: str):
    e = get_environment(slug)
    if not e:
        raise HTTPException(status_code=404, detail="Environment not found")
    return e


@router.get("/objects")
def read_objects():
    return list_objects()


@router.get("/objects/{slug}")
def read_object(slug: str):
    o = get_object(slug)
    if not o:
        raise HTTPException(status_code=404, detail="Object not found")
    return o
