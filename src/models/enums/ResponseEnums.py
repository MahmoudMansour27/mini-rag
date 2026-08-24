from enum import Enum

class ResponseSignal(Enum):
    FILE_VALIDATED_SUCCESS = "file_validate_successfully"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"

    # ------ Processing Signals ------
    UNSPORRTED_FILE_TYPE = "Unsupported file type"
    PROCESSING_SUCCESS = "File processed successfully"
    PROCESSING_FAILED = "File processing failed"

    # ------ Assets Operations ------
    NO_FILES_ERROR = "not_found_files"
    FILE_ID_ERROR = "no_file_found_with_this_id"