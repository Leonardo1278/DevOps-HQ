from enum import StrEnum


class ProjectStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PLANNING = "PLANNING"
    PAUSED = "PAUSED"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class ProjectHealth(StrEnum):
    GOOD = "GOOD"
    WATCH = "WATCH"
    RISK = "RISK"
    BLOCKED = "BLOCKED"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TaskStatus(StrEnum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    CANCELED = "CANCELED"


class IdeaStatus(StrEnum):
    INBOX = "INBOX"
    EVALUATING = "EVALUATING"
    BACKLOG = "BACKLOG"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONVERTED = "CONVERTED"


class Impact(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Effort(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InboxType(StrEnum):
    NOTE = "NOTE"
    TASK = "TASK"
    IDEA = "IDEA"
    LINK = "LINK"
    UNKNOWN = "UNKNOWN"


class ProcessingStatus(StrEnum):
    PENDING = "PENDING"
    CLASSIFIED = "CLASSIFIED"
    CONVERTED = "CONVERTED"


class ConvertTarget(StrEnum):
    TASK = "task"
    IDEA = "idea"
    NOTE = "note"


class ActivityAction(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    ARCHIVED = "archived"
    DELETED = "deleted"
    COMPLETED = "completed"
    CONVERTED = "converted"
    CLASSIFIED = "classified"


class DocumentSource(StrEnum):
    S3 = "S3"
    URL = "URL"


class ClientStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"


class CredentialKind(StrEnum):
    AWS = "AWS"
    DATABASE = "DATABASE"
    API = "API"
    HOSTING = "HOSTING"
    OTHER = "OTHER"
