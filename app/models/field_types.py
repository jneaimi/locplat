"""Field type definitions for LocPlat Translation Service"""

from enum import Enum


class FieldType(Enum):
    """Enumeration of supported field types for translation processing."""
    TEXT = "text"
    WYSIWYG = "wysiwyg"
    TEXTAREA = "textarea"
    STRING = "string"
    RELATION = "relation"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class DirectusTranslationPattern(Enum):
    """Enumeration of Directus translation patterns."""
    COLLECTION_TRANSLATIONS = "collection_translations"
    LANGUAGE_COLLECTIONS = "language_collections"
    CUSTOM = "custom"


class ContentProcessingStrategy(Enum):
    """Enumeration of content processing strategies."""
    SIMPLE = "simple"
    PRESERVE_HTML = "preserve_html"
    EXTRACT_TEXT = "extract_text"
    BATCH = "batch"
    STRUCTURED = "structured"


# Supported languages for RTL processing
RTL_LANGUAGES = ['ar', 'he', 'fa', 'ur']

# Default field type mappings for common Directus field types
DIRECTUS_FIELD_TYPE_MAPPING = {
    'string': FieldType.STRING,
    'text': FieldType.TEXT,
    'textarea': FieldType.TEXTAREA,
    'wysiwyg': FieldType.WYSIWYG,
    'markdown': FieldType.MARKDOWN,
    'json': FieldType.JSON,
    'o2m': FieldType.RELATION,
    'm2o': FieldType.RELATION,
    'm2m': FieldType.RELATION,
    'm2a': FieldType.RELATION,
}


def is_rtl_language(language_code: str) -> bool:
    """Check if a language uses RTL text direction."""
    return language_code.lower() in RTL_LANGUAGES


def get_field_type_from_directus(directus_type: str) -> FieldType:
    """Map Directus field type to our FieldType enum."""
    return DIRECTUS_FIELD_TYPE_MAPPING.get(directus_type, FieldType.STRING)
