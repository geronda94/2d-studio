from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, Table, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import datetime
from .database import Base

folder_presentation = Table(
    'folder_presentation',
    Base.metadata,
    Column('folder_id', Integer, ForeignKey('folders.id'), primary_key=True),
    Column('presentation_id', Integer, ForeignKey('presentations.id'), primary_key=True)
)

component_category = Table(
    'component_category',
    Base.metadata,
    Column('component_id', Integer, ForeignKey('components.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    # True = витрина библиотеки палитр (виден всем); обычные проекты приватны по умолчанию
    is_template = Column(Boolean, default=False)
    # Вариант отрисовки по умолчанию для новых презентаций (переназначается в настройках, UX-4)
    default_variant = Column(String, nullable=True)
    # Slug проекта-источника палитры (для revert и бейджа происхождения, STUDIO)
    palette_source = Column(String, nullable=True)
    # Владение (мульти-тенант, OWNERSHIP): NULL = системный (шаблоны/админ).
    # Шаблоны (is_template) — общие для всех; owner_id задан — личная тема/проект, приватны.
    owner_id = Column(Integer, nullable=True, index=True)
    # Оптимистичная блокировка (ENTERPRISE Ф2): +1 на контентную мутацию
    version = Column(Integer, default=0)
    # Происхождение форка: id проекта-родителя (lineage тем)
    parent_id = Column(Integer, nullable=True)
    # Бриф проекта (AI_PLATFORM Ф3): знание проекта для агента —
    # {about, audience, tone, must[], forbidden[], voice}
    brief = Column(JSON, nullable=True)
    # Конфиг проекта (BRAND KIT): brand-ассеты, контакты и дефолты компонентов —
    # {brand:{logo,qr_code,name}, contacts:{telegram,site,...}, defaults:{<Component>:{...}}, voice, bgm}
    config = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    folders = relationship("Folder", back_populates="project", cascade="all, delete-orphan")


class DesignToken(Base):
    """Дизайн-токены темы (Фаза 2). Иерархия: global (project_id=None) → project → presentation → slide."""
    __tablename__ = "design_tokens"
    id = Column(Integer, primary_key=True, index=True)
    # Уровни скоупа: чем меньше NULL-уровней, тем выше приоритет.
    # global: все NULL; project: project_id задан; presentation: +presentation_id; slide: +slide_id.
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    presentation_id = Column(Integer, ForeignKey("presentations.id"), nullable=True)
    slide_id = Column(Integer, ForeignKey("slides.id"), nullable=True)
    token_key = Column(String, index=True)  # "bg-base", "brand-blue", "text-primary", "font-heading", ...
    token_type = Column(String)  # color, font_family, gradient, shadow, radius, effect
    value = Column(String)
    # True = создан пользователем через библиотеку (можно удалять); False = дефолт из сидов (только правка значения, удаление запрещено)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False)

class User(Base):
    """Пользователь платформы (AUTH_PLAN Ф1). Открытая регистрация."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)  # хранится в lower-case
    password_hash = Column(String)  # scrypt$n$r$p$salt$hash (stdlib hashlib.scrypt)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superadmin = Column(Boolean, default=False)
    # ENTERPRISE Ф3: технический аккаунт (бот). Не логинится, только API-ключи.
    is_bot = Column(Boolean, default=False)
    owner_user_id = Column(Integer, nullable=True)  # человек-владелец бота
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)


class UserSession(Base):
    """Сессия браузерного логина (AUTH_PLAN Ф1). В БД только sha256 токена."""
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token_hash = Column(String, index=True)
    csrf_token = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime, nullable=True)
    user_agent = Column(String, nullable=True)
    ip = Column(String, nullable=True)


class ProjectMember(Base):
    """Смежная таблица доступа к проекту (AUTH_PLAN Ф2): 1 запись = 1 связка проект+пользователь.
    Владелец НЕ дублируется здесь — он в projects.owner_id.
    scope_folder_id (nullable) — задел на ограничение прав конкретными папками (NULL = весь проект)."""
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String, default="editor")  # editor | viewer
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    scope_folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ProjectRevision(Base):
    """История/снапшоты проекта (ENTERPRISE Ф2). Источник истины для отката контента.
    `content_hash` — дедуп (не пишем ревизию, если контент не изменился)."""
    __tablename__ = "project_revisions"
    __table_args__ = (UniqueConstraint("project_id", "n", name="uq_project_revisions_project_n"),)
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    n = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    author_user_id = Column(Integer, nullable=True)
    on_behalf_of_user_id = Column(Integer, nullable=True)
    source = Column(String, default="manual")  # manual|autosave|ai|restore|import
    label = Column(String, nullable=True)
    content_hash = Column(String, nullable=True)
    snapshot = Column(JSON, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    is_checkpoint = Column(Boolean, default=True)


class AuditLog(Base):
    """Аудит действий (ENTERPRISE Ф1). Append-only. Пишется в ТОЙ ЖЕ транзакции,
    что и мутация (см. backend/audit.py, before_commit-хук)."""
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    request_id = Column(String, nullable=True, index=True)
    actor_type = Column(String, default="user")  # user | service | system
    actor_user_id = Column(Integer, nullable=True, index=True)
    actor_key_id = Column(Integer, nullable=True)
    on_behalf_of_user_id = Column(Integer, nullable=True, index=True)
    effective_user_id = Column(Integer, nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    presentation_id = Column(Integer, nullable=True)
    slide_id = Column(String, nullable=True)
    action = Column(String, nullable=True)
    method = Column(String, nullable=True)
    path = Column(String, nullable=True)
    status = Column(Integer, nullable=True)
    decision = Column(String, default="allow")  # allow | deny
    deny_reason = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    ai_run_id = Column(String, nullable=True)
    diff = Column(JSON, nullable=True)   # masked
    meta = Column(JSON, nullable=True)   # masked


class IdempotencyKey(Base):
    """Ключ идемпотентности мутаций (ENTERPRISE Ф3/Ф4): повтор команды агента с тем же
    `Idempotency-Key` в рамках одной транзакции отклоняется (409). Ключ коммитится
    вместе с мутацией; при откате — исчезает, повтор разрешён."""
    __tablename__ = "idempotency_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    actor_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)


class AuditOutbox(Base):
    """Исходящие события аудита для внешних sink'ов (SIEM/webhook). Durable."""
    __tablename__ = "audit_outbox"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    payload = Column(JSON, nullable=True)
    delivered_at = Column(DateTime, nullable=True)


class ApiKey(Base):
    """API-ключ агента/пользователя (AI_PLATFORM Ф4). Хранится только хэш.
    При AUTH_MODE=on запросы с `Authorization: Bearer <key>` резолвят owner_id."""
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, index=True)  # sha256 от плейнтекста
    owner_id = Column(Integer, index=True)
    label = Column(String, nullable=True)
    scopes = Column(JSON, nullable=True)  # ["read","write","admin"] — задел
    is_active = Column(Boolean, default=True)
    # ENTERPRISE Ф3: тип ключа и делегирование
    kind = Column(String, default="personal")  # personal | service
    created_by_user_id = Column(Integer, nullable=True)
    project_id = Column(Integer, nullable=True)  # scope на проект (NULL = все)
    can_delegate = Column(Boolean, default=False)  # разрешён X-On-Behalf-Of
    rate_limit = Column(Integer, nullable=True)  # запросов/мин
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BotDelegation(Base):
    """Согласованное делегирование: бот действует ОТ ИМЕНИ subject (ENTERPRISE Ф3).
    Активируется только после approved_by == subject_user_id (consent)."""
    __tablename__ = "bot_delegations"
    id = Column(Integer, primary_key=True, index=True)
    bot_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    subject_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    project_id = Column(Integer, nullable=True)  # NULL = все проекты
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(Integer, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AiRun(Base):
    """Серверный прогон ИИ (ENTERPRISE Ф3): неподделываемый провенанс.
    Мутации агента ссылаются на run_id; сервер валидирует run↔bot↔project↔version."""
    __tablename__ = "ai_runs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, index=True)
    bot_user_id = Column(Integer, nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    agent = Column(String, nullable=True)
    model = Column(String, nullable=True)
    base_version = Column(Integer, nullable=True)
    status = Column(String, default="running")  # running | finished | failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class PresentationRevision(Base):
    """История правок презентации (AI_PLATFORM Ф1). Пишется фоново после успешной
    записи, не блокирует основной путь. ops — что сделали, snapshot — снимок слайдов."""
    __tablename__ = "presentation_revisions"
    id = Column(Integer, primary_key=True, index=True)
    presentation_id = Column(Integer, ForeignKey("presentations.id"), index=True)
    n = Column(Integer)  # порядковый номер ревизии в рамках презентации
    ops = Column(JSON, nullable=True)
    snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class StyleVariant(Base):
    """Варианты отрисовки компонентов (типизация, Фаза 2.3).
    Единый JSON-config описывает, КАК рисуются части компонентов (ноды/айтемы, линии, фон):
    радиусы, тени, тип фона (solid/gradient/blur/transparent), стиль линий и т.д.
    Ссылки на цвета — это ключи токенов темы, чтобы вариант ложился поверх любой палитры."""
    __tablename__ = "style_variants"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)  # "tech", "classic", "industrial", "educational", ...
    name = Column(String)
    description = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    # True = создан пользователем (сид не перезаписывает без --force); False = управляется сидом
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False)


class StylePreset(Base):
    """Вектор стилей (P2): палитра-проект + вариант + правила. ИИ выбирает пресет, а не комбинирует свободно."""
    __tablename__ = "style_presets"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)  # "it2b-tech"
    title = Column(String)
    palette = Column(String, nullable=True)  # slug проекта-палитры ("it2b"/"history"/"derevnya")
    variant = Column(String, nullable=True)  # slug варианта отрисовки
    rules = Column(JSON, nullable=True)  # {"max_accents": 4, "title_em": true}
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False)


class ComponentType(Base):
    __tablename__ = "component_types"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    name = Column(String)
    
    components = relationship("Component", back_populates="type")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    name = Column(String)
    
    components = relationship(
        "Component",
        secondary=component_category,
        back_populates="categories"
    )

class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    type_id = Column(Integer, ForeignKey('component_types.id'))
    default_payload = Column(JSON, nullable=True)
    payload_schema = Column(JSON, nullable=True)
    example = Column(JSON, nullable=True)
    manifest = Column(String, nullable=True)
    # True = создан пользователем через API (сид не трогает вообще); False = управляется сидом
    is_custom = Column(Boolean, default=False)
    
    type = relationship("ComponentType", back_populates="components")
    categories = relationship(
        "Category",
        secondary=component_category,
        back_populates="components"
    )

class Folder(Base):
    __tablename__ = "folders"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True) # Optional for backward compatibility during migration
    slug = Column(String, unique=True, index=True)
    title = Column(String)
    desc = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    
    presentations = relationship(
        "Presentation",
        secondary=folder_presentation,
        back_populates="folders"
    )
    project = relationship("Project", back_populates="folders")

class Presentation(Base):
    __tablename__ = "presentations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    audio_src = Column(String, nullable=True)
    audio_timeline = Column(JSON, nullable=True)
    variant = Column(String, nullable=True)  # дефолтный вариант отрисовки (если слайд не задал свой)
    style_preset = Column(String, nullable=True)  # slug из style_presets (вектор стилей, P2)
    style_lock = Column(Boolean, default=False)  # True = save слайдов проверяет вектор (422 при выходе)
    chessboard = Column(Boolean, default=False)  # True = фон слайдов slide-bg-{(i%4)+1} (opt-in, UX-5)
    # AUTH_PLAN Ф4: public — просмотр по ссылке всем; private — только владелец/участники.
    visibility = Column(String, default="public")
    # Оптимистичная блокировка (ENTERPRISE Ф2)
    version = Column(Integer, default=0)
    # Slug проекта-источника палитры презентации (presentation-scope override, P-SCOPE)
    palette_source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    slides = relationship("Slide", back_populates="presentation", cascade="all, delete-orphan", order_by="Slide.order_index")
    folders = relationship(
        "Folder",
        secondary=folder_presentation,
        back_populates="presentations"
    )
    media_files = relationship("MediaFile", back_populates="presentation", cascade="all, delete-orphan")

class MediaFile(Base):
    __tablename__ = "media_files"
    id = Column(Integer, primary_key=True, index=True)
    presentation_id = Column(Integer, ForeignKey("presentations.id"))
    filename = Column(String)
    file_type = Column(String) # 'audio', 'video', 'image'
    file_path = Column(String)
    ai_text = Column(String, nullable=True)
    ai_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    presentation = relationship("Presentation", back_populates="media_files")

class Slide(Base):
    """Timeline item. For SceneEngine a scene is a Slide with component='__scene__'.

    The table name is kept as `slides` for now so the existing player, audio
    timeline and renderer keep working. Scene-specific data lives in explicit
    columns (not hidden in payload). A later migration can rename the table.
    """
    __tablename__ = "slides"
    id = Column(Integer, primary_key=True, index=True)
    presentation_id = Column(Integer, ForeignKey("presentations.id"))
    slide_id = Column(String, unique=True, index=True)
    component = Column(String)
    start_time = Column(Float)
    title = Column(String, nullable=True)
    subtitle = Column(String, nullable=True)
    layout = Column(String, nullable=True)
    order_index = Column(Integer)

    # --- Scene fields -----------------------------------------------------
    kind = Column(String, default="legacy")          # 'scene' | 'legacy'
    duration = Column(Float, nullable=True)          # ms; scene window length
    code = Column(JSON, nullable=True)               # { html, css, js }
    props = Column(JSON, nullable=True)              # editable scene parameters
    props_schema = Column(JSON, nullable=True)       # form schema for props
    track = Column(String, default="main")           # future multi-track
    z_index = Column(Integer, default=0)             # future overlays
    
    presentation = relationship("Presentation", back_populates="slides")
    data = relationship("SlideData", back_populates="slide", uselist=False, cascade="all, delete-orphan")
    events = relationship("DirectorEvent", back_populates="slide", cascade="all, delete-orphan")

class SlideData(Base):
    __tablename__ = "slide_data"
    id = Column(Integer, primary_key=True, index=True)
    slide_id = Column(Integer, ForeignKey("slides.id"))
    payload = Column(JSON)
    
    slide = relationship("Slide", back_populates="data")

class DirectorEvent(Base):
    __tablename__ = "director_events"
    id = Column(Integer, primary_key=True, index=True)
    slide_id = Column(Integer, ForeignKey("slides.id"))
    time = Column(Float)
    action = Column(String, nullable=True)
    event_type = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    
    slide = relationship("Slide", back_populates="events")

class RenderJob(Base):
    __tablename__ = "render_jobs"
    id = Column(Integer, primary_key=True, index=True)
    presentation_id = Column(Integer, ForeignKey("presentations.id"))
    status = Column(String, default="pending") # pending, rendering, completed, failed
    progress = Column(Float, default=0.0)
    settings = Column(JSON, nullable=True)
    file_url = Column(String, nullable=True)
    error_log = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    presentation = relationship("Presentation", backref="render_jobs")
