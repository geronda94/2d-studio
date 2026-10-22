from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from ..scene_library import (
    compatibility_matrix,
    get_environment,
    get_object,
    get_template,
    list_environments,
    list_objects,
    list_templates,
    objects_for_environment,
    validate_composition,
)

router = APIRouter(prefix="/scene-library", tags=["scene-library"])


class CompositionRequest(BaseModel):
    environment: str
    objects: List[str] = []


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


@router.get("/environments/{slug}/objects")
def read_environment_objects(slug: str):
    if not get_environment(slug):
        raise HTTPException(status_code=404, detail="Environment not found")
    return objects_for_environment(slug)


@router.get("/objects")
def read_objects(environment: Optional[str] = None):
    if environment:
        if not get_environment(environment):
            raise HTTPException(status_code=404, detail="Environment not found")
        return objects_for_environment(environment)
    return list_objects()


@router.get("/objects/{slug}")
def read_object(slug: str):
    o = get_object(slug)
    if not o:
        raise HTTPException(status_code=404, detail="Object not found")
    return o


@router.get("/compatibility")
def read_compatibility():
    return compatibility_matrix()


@router.post("/validate-composition")
def validate(body: CompositionRequest):
    return validate_composition(body.environment, body.objects)
