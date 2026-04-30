"""自定义异常。"""
from __future__ import annotations


class AppException(Exception):
    """业务异常基类。"""

    status_code: int = 400

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppException):
    status_code = 404


class ValidationError(AppException):
    status_code = 422


class FileTooLargeError(AppException):
    status_code = 413


class UnsupportedFileTypeError(AppException):
    status_code = 415


class EmbeddingError(AppException):
    status_code = 500


class LLMError(AppException):
    status_code = 502


class VectorStoreError(AppException):
    status_code = 500
