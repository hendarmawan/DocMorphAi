"""Document parsing: uploaded bytes -> canonical :class:`docmorph_schema.Document`."""

from docmorph_converter.convert import convert
from docmorph_converter.validation import (
    SUPPORTED_EXTENSIONS,
    ConversionError,
    UploadRejected,
    detect_format,
)

__all__ = ["SUPPORTED_EXTENSIONS", "ConversionError", "UploadRejected", "convert", "detect_format"]
