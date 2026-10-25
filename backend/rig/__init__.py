"""SceneRig: canonical rig contracts, GLB reader and validator."""

from .archetypes import (
    ARCHETYPES,
    Archetype,
    archetype_by_name,
    archetypes_payload,
    infer_archetype,
    map_bones,
    normalize_bone,
)
from .bake import bake_clip
from .compile import compile_rig
from .validate import Report, validate_glb, validate_manifest, validate_path

__all__ = [
    "ARCHETYPES",
    "Archetype",
    "Report",
    "bake_clip",
    "compile_rig",
    "archetype_by_name",
    "archetypes_payload",
    "infer_archetype",
    "map_bones",
    "normalize_bone",
    "validate_glb",
    "validate_manifest",
    "validate_path",
]
