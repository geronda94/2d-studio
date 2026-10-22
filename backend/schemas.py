from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import datetime





class DirectorEventBase(BaseModel):
    time: float
    action: Optional[str] = None
    event_type: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class DirectorEventCreate(DirectorEventBase):
    pass

class DirectorEvent(DirectorEventBase):
    id: int
    slide_id: int
    class Config:
        orm_mode = True

class ValidateRequest(BaseModel):
    payload: Dict[str, Any]


class ValidationError(BaseModel):
    path: str
    type: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []


class SlideDataBase(BaseModel):
    payload: Dict[str, Any]

class SlideDataCreate(SlideDataBase):
    pass

class SlideData(SlideDataBase):
    id: int
    slide_id: int
    class Config:
        orm_mode = True

class SlideBase(BaseModel):
    slide_id: str
    component: str
    start_time: float
    title: Optional[str] = None
    subtitle: Optional[str] = None
    layout: Optional[str] = None
    order_index: int

class SlideCreate(SlideBase):
    data: Optional[SlideDataCreate] = None
    events: Optional[List[DirectorEventCreate]] = []

class Slide(SlideBase):
    id: int
    presentation_id: int
    data: Optional[SlideData] = None
    events: List[DirectorEvent] = []
    warnings: List[ValidationError] = []  # style-lint, не из БД (аттачится на save)
    class Config:
        orm_mode = True

class ComponentTypeBase(BaseModel):
    slug: str
    name: str

class ComponentTypeCreate(ComponentTypeBase):
    pass

class ComponentType(ComponentTypeBase):
    id: int
    class Config:
        orm_mode = True

class CategoryBase(BaseModel):
    slug: str
    name: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    class Config:
        orm_mode = True

class ComponentBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    type_id: Optional[int] = None
    default_payload: Optional[Dict[str, Any]] = None
    payload_schema: Optional[Dict[str, Any]] = None
    example: Optional[Dict[str, Any]] = None
    manifest: Optional[str] = None


class ComponentCreate(ComponentBase):
    category_ids: Optional[List[int]] = []

class Component(ComponentBase):
    id: int
    type: Optional[ComponentType] = None
    categories: List[Category] = []
    class Config:
        orm_mode = True

class FolderBase(BaseModel):
    slug: str
    title: str
    desc: Optional[str] = None
    theme: Optional[str] = None
    icon: Optional[str] = None
    project_id: Optional[int] = None
    is_archived: Optional[bool] = False

class FolderCreate(FolderBase):
    pass

class FolderUpdate(BaseModel):
    title: Optional[str] = None
    desc: Optional[str] = None
    theme: Optional[str] = None
    icon: Optional[str] = None
    is_archived: Optional[bool] = None

class MediaFileBase(BaseModel):
    filename: str
    file_type: str
    file_path: str
    ai_text: Optional[str] = None
    ai_settings: Optional[Dict[str, Any]] = None

class MediaFile(MediaFileBase):
    id: int
    presentation_id: int
    class Config:
        orm_mode = True

class GenerateSpeechRequest(BaseModel):
    text: str
    # Поля опциональны: если не заданы — берутся дефолты голоса из конфига проекта
    # (BRAND KIT: config.voice), иначе встроенные значения (см. backend/routers/ai.py).
    voice: Optional[str] = None
    audio_profile: Optional[str] = None
    style: Optional[str] = None
    pace: Optional[str] = None
    tone: Optional[str] = None
    scene: Optional[str] = None
    temperature: Optional[float] = None
    batch_id: Optional[str] = None

class AudioClip(BaseModel):
    id: str
    name: str
    src: str
    start_time: float
    end_time: Optional[float] = None
    media_offset: float = 0.0
    volume: float = 1.0
    muted: bool = False
    type: Optional[str] = None
    ai_settings: Optional[Dict[str, Any]] = None
    playbackRate: Optional[float] = 1.0

class AudioTrack(BaseModel):
    id: str
    type: str # 'voiceover', 'bgm', 'sfx'
    clips: List[AudioClip] = []

class AudioTimeline(BaseModel):
    tracks: List[AudioTrack] = []

class PresentationBase(BaseModel):
    title: str
    audio_src: Optional[str] = None
    audio_timeline: Optional[Dict[str, Any]] = None
    variant: Optional[str] = None
    style_preset: Optional[str] = None
    style_lock: Optional[bool] = False
    chessboard: Optional[bool] = False
    palette_source: Optional[str] = None
    visibility: Optional[str] = "public"  # AUTH_PLAN Ф4: public | private
    version: Optional[int] = 0  # ENTERPRISE Ф2: optimistic locking
    is_archived: Optional[bool] = False

class PresentationCreate(PresentationBase):
    folder_id: Optional[int] = None

class PresentationUpdate(BaseModel):
    title: Optional[str] = None
    audio_src: Optional[str] = None
    audio_timeline: Optional[Dict[str, Any]] = None
    variant: Optional[str] = None
    is_archived: Optional[bool] = None
    chessboard: Optional[bool] = None
    visibility: Optional[str] = None  # public | private (AUTH_PLAN Ф4)
    expected_version: Optional[int] = None  # ENTERPRISE Ф2: 409 при рассинхроне

class Presentation(PresentationBase):
    id: int
    slides: List[Slide] = []
    media_files: List[MediaFile] = []
    class Config:
        orm_mode = True

class Folder(FolderBase):
    id: int
    presentations: List[Presentation] = []
    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    slug: str
    title: str
    description: Optional[str] = None
    is_template: Optional[bool] = False
    default_variant: Optional[str] = None
    palette_source: Optional[str] = None
    owner_id: Optional[int] = None
    parent_id: Optional[int] = None
    brief: Optional[Dict[str, Any]] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    default_variant: Optional[str] = None
class ProjectCreate(ProjectBase):
    pass

class ProjectCreateRequest(BaseModel):
    """Создание проекта из шаблона палитры (UX-1). slug опционален — сгенерируется из title."""
    title: str
    slug: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = "it2b"  # slug проекта-палитры (it2b/history/derevnya)

class Project(ProjectBase):
    id: int
    folders: List[Folder] = []
    class Config:
        orm_mode = True


# --- Легковесные (summary) схемы: списки без вложенных слайдов/payload ---
# Дерево Project→Folder→Presentation→Slide с payload весит ~1 МБ на 9 проектов
# и ~0.5 МБ на список папок. Для списочных экранов нужны только метаданные.

class PresentationSummary(PresentationBase):
    id: int
    slides_count: Optional[int] = 0
    class Config:
        orm_mode = True


class FolderSummary(FolderBase):
    id: int
    project_slug: Optional[str] = None
    presentations: List[PresentationSummary] = []
    class Config:
        orm_mode = True


class ProjectFolderSummary(FolderBase):
    id: int
    presentations_count: Optional[int] = 0
    class Config:
        orm_mode = True


class ProjectSummary(ProjectBase):
    id: int
    folders: List[ProjectFolderSummary] = []
    class Config:
        orm_mode = True


class DesignTokenBase(BaseModel):
    token_key: str
    token_type: str
    value: str

class DesignTokenCreate(DesignTokenBase):
    presentation_id: Optional[int] = None
    slide_id: Optional[int] = None

class DesignToken(DesignTokenBase):
    id: int
    project_id: Optional[int] = None
    presentation_id: Optional[int] = None
    slide_id: Optional[int] = None
    class Config:
        orm_mode = True

class DesignTokensUpsert(BaseModel):
    """Массовая установка токенов: {token_key: value}. token_type выводится по ключу."""
    tokens: Dict[str, Any]


class StyleVariantBase(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class StyleVariantCreate(StyleVariantBase):
    pass

class StyleVariant(StyleVariantBase):
    id: int
    is_archived: bool = False
    is_custom: bool = False
    class Config:
        orm_mode = True

class StylePresetBase(BaseModel):
    slug: str
    title: str
    palette: Optional[str] = None
    variant: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None

class StylePresetCreate(StylePresetBase):
    pass

class StylePreset(StylePresetBase):
    id: int
    is_custom: bool = False
    is_archived: bool = False
    class Config:
        orm_mode = True

class PresentationStyleUpdate(BaseModel):
    style_preset: Optional[str] = None
    style_lock: Optional[bool] = None

class PaletteCopyRequest(BaseModel):
    from_project: str  # slug проекта-источника (шаблон из витрины или любой проект)

class ProjectVariantApply(BaseModel):
    variant: Optional[str] = None  # null = сбросить к tech-fallback

class ProjectForkRequest(BaseModel):
    title: Optional[str] = None  # заголовок личной копии; по умолчанию «X (моя)»

class ApiKeyCreate(BaseModel):
    owner_id: Optional[int] = None
    label: Optional[str] = None
    scopes: Optional[List[str]] = ["read", "write"]
    # ENTERPRISE Ф3
    kind: Optional[str] = "personal"  # personal | service
    bot_name: Optional[str] = None
    can_delegate: Optional[bool] = False
    project_id: Optional[int] = None
    rate_limit: Optional[int] = None

class ApiKeyOut(BaseModel):
    id: int
    owner_id: Optional[int] = None
    label: Optional[str] = None
    scopes: Optional[List[str]] = None
    is_active: bool = True
    # ENTERPRISE Ф3
    kind: Optional[str] = "personal"
    project_id: Optional[int] = None
    can_delegate: Optional[bool] = False
    created_by_user_id: Optional[int] = None
    class Config:
        orm_mode = True

class ProjectBrief(BaseModel):
    about: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    must: Optional[List[str]] = []
    forbidden: Optional[List[str]] = []
    voice: Optional[str] = None

class TranscriptSegment(BaseModel):
    text: str
    start_ms: float
    end_ms: Optional[float] = None

class GenerateFromAudioRequest(BaseModel):
    segments: Optional[List[TranscriptSegment]] = None  # из /ai/transcribe (text+тайминги)
    apply: bool = False

class GenerateSlidesRequest(BaseModel):
    script: Optional[str] = None          # сценарий/команда человека
    brief: Optional[ProjectBrief] = None  # разовый бриф (иначе берётся из проекта)
    slide_count: Optional[int] = None     # желаемое число слайдов
    apply: bool = False                    # по умолчанию только предложить (review)

class ChangeOp(BaseModel):
    """Одна операция change-set (AI_PLATFORM Ф2)."""
    op: str
    slide_id: Optional[str] = None
    component: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    patch: Optional[Dict[str, Any]] = None
    start_time: Optional[float] = None
    order_index: Optional[int] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    variant: Optional[str] = None
    tokens: Optional[Dict[str, Any]] = None
    from_project: Optional[str] = None
    order: Optional[List[str]] = None

class ChangeSetRequest(BaseModel):
    ops: List[ChangeOp]
    dry_run: bool = True  # по умолчанию ничего не пишем — только проверка и diff

class RenderJobBase(BaseModel):
    presentation_id: int
    settings: Optional[Dict[str, Any]] = None

class RenderJobCreate(RenderJobBase):
    pass

class RenderJob(RenderJobBase):
    id: int
    status: str
    progress: float
    file_url: Optional[str] = None
    error_log: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    class Config:
        orm_mode = True
