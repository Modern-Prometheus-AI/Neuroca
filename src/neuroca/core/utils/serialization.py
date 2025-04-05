"""
Serialization Utilities for NeuroCognitive Architecture

This module provides comprehensive serialization and deserialization utilities for the NCA system.
It supports various data formats (JSON, Pickle, MessagePack, etc.) with configurable options
for security, compression, and versioning.

The module implements:
1. Safe serialization/deserialization with proper error handling
2. Format conversion utilities
3. Custom serializers for complex NCA-specific objects
4. Versioned serialization for backward compatibility
5. Compression options for efficient storage and transmission

Usage Examples:
    # Basic JSON serialization
    data = {"key": "value", "nested": {"data": [1, 2, 3]}}
    serialized = serialize(data)
    deserialized = deserialize(serialized)
    
    # Serializing with specific format and compression
    serialized = serialize(complex_object, format="pickle", compress=True)
    
    # Versioned serialization for backward compatibility
    serialized = serialize_versioned(data, version="1.2")
    deserialized = deserialize_versioned(serialized)
"""

import base64
import gzip
import hashlib
import io
import json
import logging
import os
import pickle
import zlib
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import msgpack
import numpy as np
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure module logger
logger = logging.getLogger(__name__)


class SerializationFormat(Enum):
    """Supported serialization formats."""
    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    CUSTOM = "custom"


class CompressionMethod(Enum):
    """Supported compression methods."""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"


class SerializationError(Exception):
    """Base exception for serialization errors."""
    pass


class DeserializationError(Exception):
    """Base exception for deserialization errors."""
    pass


class UnsupportedFormatError(SerializationError):
    """Exception raised when an unsupported format is requested."""
    pass


class VersionMismatchError(DeserializationError):
    """Exception raised when version mismatch occurs during deserialization."""
    pass


class SecurityError(DeserializationError):
    """Exception raised for security-related issues."""
    pass


def _get_encryption_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Generate an encryption key from a password using PBKDF2.
    
    Args:
        password: The password to derive the key from
        salt: Optional salt bytes, generated if not provided
        
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def _encrypt_data(data: bytes, password: str) -> dict[str, bytes]:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: Bytes to encrypt
        password: Password for encryption
        
    Returns:
        Dictionary containing encrypted data and metadata
    """
    key, salt = _get_encryption_key(password)
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)
    
    return {
        "data": encrypted_data,
        "salt": salt,
        "method": b"fernet"
    }


def _decrypt_data(encrypted_package: dict[str, bytes], password: str) -> bytes:
    """
    Decrypt data using the appropriate method.
    
    Args:
        encrypted_package: Dictionary containing encrypted data and metadata
        password: Password for decryption
        
    Returns:
        Decrypted bytes
    """
    if encrypted_package.get("method") != b"fernet":
        raise SecurityError(f"Unsupported encryption method: {encrypted_package.get('method')}")
    
    key, _ = _get_encryption_key(password, encrypted_package["salt"])
    fernet = Fernet(key)
    
    try:
        return fernet.decrypt(encrypted_package["data"])
    except Exception as e:
        raise SecurityError(f"Decryption failed: {str(e)}")


def _compress_data(data: bytes, method: CompressionMethod = CompressionMethod.GZIP) -> bytes:
    """
    Compress data using the specified method.
    
    Args:
        data: Bytes to compress
        method: Compression method to use
        
    Returns:
        Compressed bytes
    """
    if method == CompressionMethod.NONE:
        return data
    elif method == CompressionMethod.GZIP:
        return gzip.compress(data)
    elif method == CompressionMethod.ZLIB:
        return zlib.compress(data)
    else:
        raise ValueError(f"Unsupported compression method: {method}")


def _decompress_data(data: bytes, method: CompressionMethod = CompressionMethod.GZIP) -> bytes:
    """
    Decompress data using the specified method.
    
    Args:
        data: Compressed bytes
        method: Compression method used
        
    Returns:
        Decompressed bytes
    """
    if method == CompressionMethod.NONE:
        return data
    elif method == CompressionMethod.GZIP:
        return gzip.decompress(data)
    elif method == CompressionMethod.ZLIB:
        return zlib.decompress(data)
    else:
        raise ValueError(f"Unsupported decompression method: {method}")


def _serialize_numpy(obj: np.ndarray) -> dict[str, Any]:
    """
    Serialize a NumPy array to a dictionary.
    
    Args:
        obj: NumPy array to serialize
        
    Returns:
        Dictionary representation of the array
    """
    buffer = io.BytesIO()
    np.save(buffer, obj, allow_pickle=False)
    buffer.seek(0)
    
    return {
        "__numpy__": True,
        "data": base64.b64encode(buffer.read()).decode('ascii'),
        "dtype": str(obj.dtype),
        "shape": obj.shape
    }


def _deserialize_numpy(data: dict[str, Any]) -> np.ndarray:
    """
    Deserialize a NumPy array from a dictionary.
    
    Args:
        data: Dictionary representation of a NumPy array
        
    Returns:
        Reconstructed NumPy array
    """
    buffer = io.BytesIO(base64.b64decode(data["data"]))
    return np.load(buffer, allow_pickle=False)


def _serialize_datetime(obj: datetime) -> dict[str, Any]:
    """
    Serialize a datetime object to a dictionary.
    
    Args:
        obj: Datetime object to serialize
        
    Returns:
        Dictionary representation of the datetime
    """
    return {
        "__datetime__": True,
        "data": obj.isoformat()
    }


def _deserialize_datetime(data: dict[str, Any]) -> datetime:
    """
    Deserialize a datetime object from a dictionary.
    
    Args:
        data: Dictionary representation of a datetime
        
    Returns:
        Reconstructed datetime object
    """
    return datetime.fromisoformat(data["data"])


class NCAJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for NCA-specific types."""
    
    def default(self, obj: Any) -> Any:
        """
        Encode special types to JSON-compatible formats.
        
        Args:
            obj: Object to encode
            
        Returns:
            JSON-compatible representation
        """
        if isinstance(obj, np.ndarray):
            return _serialize_numpy(obj)
        elif isinstance(obj, datetime):
            return _serialize_datetime(obj)
        elif isinstance(obj, Enum):
            return {"__enum__": True, "name": obj.__class__.__name__, "value": obj.value}
        elif isinstance(obj, set):
            return {"__set__": True, "items": list(obj)}
        elif isinstance(obj, bytes):
            return {"__bytes__": True, "data": base64.b64encode(obj).decode('ascii')}
        elif isinstance(obj, Path):
            return {"__path__": True, "data": str(obj)}
        elif hasattr(obj, "__serialize__") and callable(obj.__serialize__):
            return obj.__serialize__()
        
        return super().default(obj)


def _json_object_hook(data: dict[str, Any]) -> Any:
    """
    Custom object hook for JSON deserialization.
    
    Args:
        data: Dictionary to process
        
    Returns:
        Reconstructed object or original dictionary
    """
    if "__numpy__" in data:
        return _deserialize_numpy(data)
    elif "__datetime__" in data:
        return _deserialize_datetime(data)
    elif "__enum__" in data:
        # This is a simplified approach; in production, you'd need a registry
        # of enum classes or a more sophisticated mechanism
        for enum_class in Enum.__subclasses__():
            if enum_class.__name__ == data["name"]:
                return enum_class(data["value"])
        logger.warning(f"Could not find enum class {data['name']}")
        return data
    elif "__set__" in data:
        return set(data["items"])
    elif "__bytes__" in data:
        return base64.b64decode(data["data"])
    elif "__path__" in data:
        return Path(data["data"])
    
    return data


def serialize(
    obj: Any,
    format: Union[str, SerializationFormat] = SerializationFormat.JSON,
    compress: bool = False,
    compression_method: CompressionMethod = CompressionMethod.GZIP,
    encrypt: bool = False,
    password: Optional[str] = None,
    **kwargs
) -> bytes:
    """
    Serialize an object to bytes using the specified format and options.
    
    Args:
        obj: Object to serialize
        format: Serialization format to use
        compress: Whether to compress the serialized data
        compression_method: Method to use for compression
        encrypt: Whether to encrypt the serialized data
        password: Password for encryption (required if encrypt=True)
        **kwargs: Additional format-specific options
        
    Returns:
        Serialized bytes
        
    Raises:
        SerializationError: If serialization fails
        UnsupportedFormatError: If the requested format is not supported
        ValueError: If encryption is requested without a password
    """
    if isinstance(format, str):
        try:
            format = SerializationFormat(format)
        except ValueError:
            raise UnsupportedFormatError(f"Unsupported serialization format: {format}")
    
    if encrypt and not password:
        raise ValueError("Password is required for encryption")
    
    try:
        # Serialize the object to bytes
        if format == SerializationFormat.JSON:
            serialized = json.dumps(obj, cls=NCAJSONEncoder, **kwargs).encode('utf-8')
        elif format == SerializationFormat.PICKLE:
            serialized = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL, **kwargs)
        elif format == SerializationFormat.MSGPACK:
            serialized = msgpack.packb(obj, use_bin_type=True, **kwargs)
        elif format == SerializationFormat.CUSTOM:
            if not hasattr(obj, "__serialize__") or not callable(obj.__serialize__):
                raise SerializationError("Object does not support custom serialization")
            serialized = obj.__serialize__()
            if not isinstance(serialized, bytes):
                serialized = json.dumps(serialized).encode('utf-8')
        else:
            raise UnsupportedFormatError(f"Unsupported serialization format: {format}")
        
        # Add format information
        metadata = {
            "format": format.value,
            "compressed": compress,
            "encrypted": encrypt,
            "checksum": hashlib.sha256(serialized).hexdigest()
        }
        
        if compress:
            metadata["compression_method"] = compression_method.value
            serialized = _compress_data(serialized, compression_method)
        
        if encrypt:
            encrypted_package = _encrypt_data(serialized, password)
            serialized = msgpack.packb({
                "metadata": metadata,
                "encrypted_data": encrypted_package
            })
        else:
            serialized = msgpack.packb({
                "metadata": metadata,
                "data": serialized
            })
        
        return serialized
    
    except Exception as e:
        logger.error(f"Serialization error: {str(e)}", exc_info=True)
        raise SerializationError(f"Failed to serialize object: {str(e)}") from e


def deserialize(
    data: bytes,
    password: Optional[str] = None,
    safe_mode: bool = True,
    **kwargs
) -> Any:
    """
    Deserialize an object from bytes.
    
    Args:
        data: Serialized bytes
        password: Password for decryption (if data is encrypted)
        safe_mode: If True, restricts certain operations for security
        **kwargs: Additional format-specific options
        
    Returns:
        Deserialized object
        
    Raises:
        DeserializationError: If deserialization fails
        SecurityError: If security checks fail
    """
    try:
        # Unpack the serialized data
        package = msgpack.unpackb(data)
        metadata = package.get("metadata", {})
        
        format_name = metadata.get("format", "json")
        try:
            format = SerializationFormat(format_name)
        except ValueError:
            raise UnsupportedFormatError(f"Unsupported serialization format: {format_name}")
        
        # Handle encrypted data
        if metadata.get("encrypted", False):
            if not password:
                raise SecurityError("Password required for decryption")
            
            encrypted_package = package.get("encrypted_data", {})
            serialized = _decrypt_data(encrypted_package, password)
        else:
            serialized = package.get("data", b"")
        
        # Verify checksum
        if "checksum" in metadata:
            calculated_checksum = hashlib.sha256(serialized).hexdigest()
            if calculated_checksum != metadata["checksum"]:
                raise SecurityError("Data integrity check failed: checksum mismatch")
        
        # Handle compression
        if metadata.get("compressed", False):
            compression_method_name = metadata.get("compression_method", "gzip")
            compression_method = CompressionMethod(compression_method_name)
            serialized = _decompress_data(serialized, compression_method)
        
        # Deserialize based on format
        if format == SerializationFormat.JSON:
            result = json.loads(serialized.decode('utf-8'), object_hook=_json_object_hook, **kwargs)
        elif format == SerializationFormat.PICKLE:
            if safe_mode:
                raise SecurityError("Pickle deserialization not allowed in safe mode")
            result = pickle.loads(serialized, **kwargs)
        elif format == SerializationFormat.MSGPACK:
            result = msgpack.unpackb(serialized, raw=False, **kwargs)
        elif format == SerializationFormat.CUSTOM:
            # Custom deserialization would typically require a registry of deserializers
            # This is a simplified approach
            if "custom_deserializer" in kwargs and callable(kwargs["custom_deserializer"]):
                result = kwargs["custom_deserializer"](serialized)
            else:
                # Fallback to JSON
                result = json.loads(serialized.decode('utf-8'), object_hook=_json_object_hook)
        else:
            raise UnsupportedFormatError(f"Unsupported deserialization format: {format}")
        
        return result
    
    except Exception as e:
        logger.error(f"Deserialization error: {str(e)}", exc_info=True)
        if isinstance(e, (SecurityError, UnsupportedFormatError)):
            raise
        raise DeserializationError(f"Failed to deserialize data: {str(e)}") from e


def serialize_to_file(
    obj: Any,
    filepath: Union[str, Path],
    format: Union[str, SerializationFormat] = SerializationFormat.JSON,
    compress: bool = True,
    encrypt: bool = False,
    password: Optional[str] = None,
    **kwargs
) -> None:
    """
    Serialize an object and save it to a file.
    
    Args:
        obj: Object to serialize
        filepath: Path to save the serialized data
        format: Serialization format to use
        compress: Whether to compress the serialized data
        encrypt: Whether to encrypt the serialized data
        password: Password for encryption (required if encrypt=True)
        **kwargs: Additional format-specific options
        
    Raises:
        SerializationError: If serialization or file writing fails
    """
    try:
        serialized = serialize(
            obj, 
            format=format, 
            compress=compress, 
            encrypt=encrypt, 
            password=password, 
            **kwargs
        )
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(serialized)
            
        logger.debug(f"Successfully serialized object to {filepath}")
    
    except Exception as e:
        logger.error(f"Failed to serialize to file {filepath}: {str(e)}", exc_info=True)
        raise SerializationError(f"Failed to serialize to file: {str(e)}") from e


def deserialize_from_file(
    filepath: Union[str, Path],
    password: Optional[str] = None,
    safe_mode: bool = True,
    **kwargs
) -> Any:
    """
    Deserialize an object from a file.
    
    Args:
        filepath: Path to the serialized data file
        password: Password for decryption (if data is encrypted)
        safe_mode: If True, restricts certain operations for security
        **kwargs: Additional format-specific options
        
    Returns:
        Deserialized object
        
    Raises:
        DeserializationError: If deserialization or file reading fails
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            serialized = f.read()
        
        return deserialize(serialized, password=password, safe_mode=safe_mode, **kwargs)
    
    except Exception as e:
        logger.error(f"Failed to deserialize from file {filepath}: {str(e)}", exc_info=True)
        if isinstance(e, (SecurityError, UnsupportedFormatError)):
            raise
        raise DeserializationError(f"Failed to deserialize from file: {str(e)}") from e


def serialize_versioned(
    obj: Any,
    version: str,
    **kwargs
) -> bytes:
    """
    Serialize an object with version information.
    
    Args:
        obj: Object to serialize
        version: Version string to include in metadata
        **kwargs: Additional serialization options
        
    Returns:
        Serialized bytes with version information
    """
    # Add version to the object metadata
    obj_with_version = {
        "data": obj,
        "__version__": version,
        "__timestamp__": datetime.utcnow().isoformat()
    }
    
    return serialize(obj_with_version, **kwargs)


def deserialize_versioned(
    data: bytes,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None,
    **kwargs
) -> tuple[Any, str]:
    """
    Deserialize versioned data with version compatibility checks.
    
    Args:
        data: Serialized bytes
        min_version: Minimum acceptable version (optional)
        max_version: Maximum acceptable version (optional)
        **kwargs: Additional deserialization options
        
    Returns:
        Tuple of (deserialized object, version string)
        
    Raises:
        VersionMismatchError: If version constraints are not met
    """
    result = deserialize(data, **kwargs)
    
    if not isinstance(result, dict) or "__version__" not in result:
        raise DeserializationError("Data does not contain version information")
    
    version = result["__version__"]
    
    # Check version constraints
    if min_version and version < min_version:
        raise VersionMismatchError(f"Data version {version} is older than minimum required version {min_version}")
    
    if max_version and version > max_version:
        raise VersionMismatchError(f"Data version {version} is newer than maximum supported version {max_version}")
    
    return result.get("data"), version


def convert_format(
    data: bytes,
    target_format: Union[str, SerializationFormat],
    password: Optional[str] = None,
    new_password: Optional[str] = None,
    **kwargs
) -> bytes:
    """
    Convert serialized data from one format to another.
    
    Args:
        data: Serialized bytes
        target_format: Format to convert to
        password: Password for decryption (if data is encrypted)
        new_password: Password for encryption of the new format (if needed)
        **kwargs: Additional serialization options
        
    Returns:
        Serialized bytes in the target format
    """
    # Deserialize the original data
    obj = deserialize(data, password=password)
    
    # Serialize to the target format
    return serialize(
        obj, 
        format=target_format, 
        encrypt=new_password is not None,
        password=new_password,
        **kwargs
    )


# Register custom serializers for common types
CUSTOM_SERIALIZERS = {
    np.ndarray: _serialize_numpy,
    datetime: _serialize_datetime,
}

# Register custom deserializers for common types
CUSTOM_DESERIALIZERS = {
    "__numpy__": _deserialize_numpy,
    "__datetime__": _deserialize_datetime,
}