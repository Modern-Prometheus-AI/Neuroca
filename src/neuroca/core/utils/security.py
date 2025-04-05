"""
Security Utilities for NeuroCognitive Architecture (NCA)

This module provides comprehensive security utilities for the NCA system, including:
- Cryptographic functions (encryption, decryption, hashing)
- Secure token generation and validation
- Password management (hashing, verification)
- Input sanitization and validation
- Rate limiting utilities
- Security logging

All implementations follow industry best practices and use well-established
cryptographic libraries to ensure maximum security.

Usage:
    from neuroca.core.utils.security import (
        encrypt_data, decrypt_data, hash_password, verify_password,
        generate_token, validate_token, sanitize_input
    )

    # Encrypt sensitive data
    encrypted = encrypt_data("sensitive information", encryption_key)
    
    # Hash passwords securely
    hashed_pw = hash_password("user_password")
    
    # Verify passwords
    is_valid = verify_password("user_password", hashed_pw)
    
    # Generate secure tokens
    token = generate_token({"user_id": 123}, expires_in=3600)
"""

import base64
import binascii
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import string
import time
from datetime import datetime
from typing import Any, Optional, Union

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logger
logger = logging.getLogger(__name__)

# Constants
TOKEN_EXPIRY_DEFAULT = 3600  # Default token expiry in seconds (1 hour)
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
SALT_SIZE = 16
KEY_LENGTH = 32
ITERATIONS = 100000  # PBKDF2 iterations (NIST recommendation)
FERNET_TTL = 3600  # Time-to-live for Fernet tokens (1 hour)


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class EncryptionError(SecurityError):
    """Exception raised for encryption/decryption errors."""
    pass


class TokenError(SecurityError):
    """Exception raised for token generation/validation errors."""
    pass


class PasswordError(SecurityError):
    """Exception raised for password-related errors."""
    pass


class InputValidationError(SecurityError):
    """Exception raised for input validation errors."""
    pass


def generate_key(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """
    Generate a cryptographic key from a password using PBKDF2.
    
    Args:
        password: The password to derive the key from
        salt: Optional salt bytes. If None, a new random salt is generated
        
    Returns:
        Tuple of (key, salt)
        
    Raises:
        EncryptionError: If key generation fails
    """
    try:
        if salt is None:
            salt = os.urandom(SALT_SIZE)
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_LENGTH,
            salt=salt,
            iterations=ITERATIONS,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    except Exception as e:
        logger.error(f"Key generation failed: {str(e)}")
        raise EncryptionError(f"Failed to generate encryption key: {str(e)}")


def get_fernet_key(key: Union[str, bytes]) -> bytes:
    """
    Convert a key to a valid Fernet key (URL-safe base64-encoded 32-byte key).
    
    Args:
        key: The key as string or bytes
        
    Returns:
        Fernet-compatible key as bytes
        
    Raises:
        EncryptionError: If key conversion fails
    """
    try:
        key_bytes = key.encode('utf-8') if isinstance(key, str) else key
            
        # Ensure key is 32 bytes
        if len(key_bytes) < 32:
            # If key is too short, use SHA-256 to derive a 32-byte key
            key_bytes = hashlib.sha256(key_bytes).digest()
        elif len(key_bytes) > 32:
            # If key is too long, truncate to 32 bytes
            key_bytes = key_bytes[:32]
            
        # Convert to Fernet key format (URL-safe base64-encoded)
        return base64.urlsafe_b64encode(key_bytes)
    except Exception as e:
        logger.error(f"Fernet key conversion failed: {str(e)}")
        raise EncryptionError(f"Failed to create Fernet key: {str(e)}")


def encrypt_data(data: Union[str, bytes, dict], key: Union[str, bytes]) -> str:
    """
    Encrypt data using Fernet symmetric encryption (AES-128-CBC with HMAC).
    
    Args:
        data: The data to encrypt (string, bytes, or dictionary)
        key: The encryption key (string or bytes)
        
    Returns:
        Base64-encoded encrypted data as string
        
    Raises:
        EncryptionError: If encryption fails
    """
    try:
        # Convert data to bytes if needed
        if isinstance(data, dict):
            data_bytes = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
            
        # Get Fernet-compatible key
        fernet_key = get_fernet_key(key)
        cipher = Fernet(fernet_key)
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(data_bytes)
        return encrypted_data.decode('utf-8')
    except Exception as e:
        logger.error(f"Data encryption failed: {str(e)}")
        raise EncryptionError(f"Failed to encrypt data: {str(e)}")


def decrypt_data(encrypted_data: Union[str, bytes], key: Union[str, bytes]) -> Union[str, dict]:
    """
    Decrypt data that was encrypted with encrypt_data.
    
    Args:
        encrypted_data: The encrypted data (string or bytes)
        key: The encryption key (string or bytes)
        
    Returns:
        Decrypted data as string or dictionary (if JSON)
        
    Raises:
        EncryptionError: If decryption fails
    """
    try:
        # Convert encrypted data to bytes if needed
        if isinstance(encrypted_data, str):
            encrypted_bytes = encrypted_data.encode('utf-8')
        else:
            encrypted_bytes = encrypted_data
            
        # Get Fernet-compatible key
        fernet_key = get_fernet_key(key)
        cipher = Fernet(fernet_key)
        
        # Decrypt the data
        decrypted_bytes = cipher.decrypt(encrypted_bytes, ttl=FERNET_TTL)
        decrypted_str = decrypted_bytes.decode('utf-8')
        
        # Try to parse as JSON
        try:
            return json.loads(decrypted_str)
        except json.JSONDecodeError:
            return decrypted_str
    except InvalidToken:
        logger.error("Invalid token or expired token")
        raise EncryptionError("Invalid or expired encrypted data")
    except Exception as e:
        logger.error(f"Data decryption failed: {str(e)}")
        raise EncryptionError(f"Failed to decrypt data: {str(e)}")


def hash_password(password: str) -> str:
    """
    Securely hash a password using bcrypt.
    
    Args:
        password: The plaintext password to hash
        
    Returns:
        Hashed password as string
        
    Raises:
        PasswordError: If password hashing fails or password is invalid
    """
    try:
        # Validate password
        if not password or len(password) < PASSWORD_MIN_LENGTH:
            raise PasswordError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
        if len(password) > PASSWORD_MAX_LENGTH:
            raise PasswordError(f"Password cannot exceed {PASSWORD_MAX_LENGTH} characters")
            
        # Hash the password with bcrypt (includes salt automatically)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
        return hashed.decode('utf-8')
    except PasswordError:
        raise
    except Exception as e:
        logger.error(f"Password hashing failed: {str(e)}")
        raise PasswordError(f"Failed to hash password: {str(e)}")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: The plaintext password to verify
        hashed_password: The hashed password to check against
        
    Returns:
        True if password matches, False otherwise
        
    Raises:
        PasswordError: If password verification fails
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        raise PasswordError(f"Failed to verify password: {str(e)}")


def generate_token(payload: dict[str, Any], secret_key: str, expires_in: int = TOKEN_EXPIRY_DEFAULT) -> str:
    """
    Generate a secure JWT-like token with payload.
    
    Args:
        payload: Dictionary containing data to encode in the token
        secret_key: Secret key for signing the token
        expires_in: Token expiry time in seconds (default: 1 hour)
        
    Returns:
        Secure token as string
        
    Raises:
        TokenError: If token generation fails
    """
    try:
        # Add expiry timestamp to payload
        expiry = int(time.time()) + expires_in
        token_data = {
            **payload,
            "exp": expiry,
            "iat": int(time.time())
        }
        
        # Convert payload to JSON and encode
        payload_bytes = json.dumps(token_data).encode('utf-8')
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')
        
        # Create signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        
        # Combine to form token
        token = f"{payload_b64}.{signature_b64}"
        return token
    except Exception as e:
        logger.error(f"Token generation failed: {str(e)}")
        raise TokenError(f"Failed to generate token: {str(e)}")


def validate_token(token: str, secret_key: str) -> dict[str, Any]:
    """
    Validate and decode a token generated with generate_token.
    
    Args:
        token: The token to validate
        secret_key: Secret key used to sign the token
        
    Returns:
        Decoded payload as dictionary
        
    Raises:
        TokenError: If token is invalid, expired, or validation fails
    """
    try:
        # Split token into parts
        if '.' not in token:
            raise TokenError("Invalid token format")
            
        payload_b64, signature_b64 = token.split('.')
        
        # Verify signature
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            raise TokenError("Invalid token signature")
            
        # Decode payload
        # Add padding if needed
        padding = '=' * (4 - len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes)
        
        # Check expiry
        if 'exp' in payload and payload['exp'] < time.time():
            raise TokenError("Token has expired")
            
        return payload
    except TokenError:
        raise
    except json.JSONDecodeError:
        logger.error("Invalid token payload format")
        raise TokenError("Invalid token payload format")
    except binascii.Error:
        logger.error("Invalid token encoding")
        raise TokenError("Invalid token encoding")
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise TokenError(f"Failed to validate token: {str(e)}")


def generate_random_string(length: int = 32, include_special: bool = True) -> str:
    """
    Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string to generate
        include_special: Whether to include special characters
        
    Returns:
        Random string
        
    Raises:
        SecurityError: If random string generation fails
    """
    try:
        if length < 1:
            raise ValueError("Length must be positive")
            
        # Define character sets
        chars = string.ascii_letters + string.digits
        if include_special:
            chars += string.punctuation
            
        # Generate random string
        return ''.join(secrets.choice(chars) for _ in range(length))
    except Exception as e:
        logger.error(f"Random string generation failed: {str(e)}")
        raise SecurityError(f"Failed to generate random string: {str(e)}")


def sanitize_input(input_str: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_str: The input string to sanitize
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
        
    Raises:
        InputValidationError: If input sanitization fails
    """
    try:
        if not isinstance(input_str, str):
            raise InputValidationError("Input must be a string")
            
        # Basic sanitization
        if not allow_html:
            # Remove HTML tags
            sanitized = re.sub(r'<[^>]*>', '', input_str)
        else:
            sanitized = input_str
            
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', sanitized)
        
        return sanitized
    except Exception as e:
        logger.error(f"Input sanitization failed: {str(e)}")
        raise InputValidationError(f"Failed to sanitize input: {str(e)}")


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    # RFC 5322 compliant regex pattern for email validation
    pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    return bool(re.match(pattern, email))


def secure_compare(a: str, b: str) -> bool:
    """
    Perform a constant-time comparison of two strings to prevent timing attacks.
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal, False otherwise
    """
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


class RateLimiter:
    """
    Simple in-memory rate limiter to prevent brute force attacks.
    
    For production use, consider using a distributed rate limiter with Redis.
    """
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        """
        Initialize the rate limiter.
        
        Args:
            max_attempts: Maximum number of attempts allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = {}  # key -> [(timestamp, count), ...]
        
    def is_rate_limited(self, key: str) -> bool:
        """
        Check if a key is rate limited.
        
        Args:
            key: The key to check (e.g., IP address, username)
            
        Returns:
            True if rate limited, False otherwise
        """
        now = time.time()
        
        # Clean up old entries
        if key in self.attempts:
            self.attempts[key] = [
                (ts, count) for ts, count in self.attempts[key]
                if now - ts < self.window_seconds
            ]
            
        # Count recent attempts
        recent_attempts = sum(count for _, count in self.attempts.get(key, []))
        
        return recent_attempts >= self.max_attempts
        
    def add_attempt(self, key: str) -> None:
        """
        Record an attempt for a key.
        
        Args:
            key: The key to record an attempt for
        """
        now = time.time()
        
        if key not in self.attempts:
            self.attempts[key] = []
            
        self.attempts[key].append((now, 1))


def log_security_event(event_type: str, details: dict[str, Any], severity: str = "INFO") -> None:
    """
    Log a security-related event with standardized format.
    
    Args:
        event_type: Type of security event (e.g., "LOGIN_ATTEMPT", "PASSWORD_RESET")
        details: Dictionary with event details
        severity: Log severity level (INFO, WARNING, ERROR, CRITICAL)
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "severity": severity,
        "details": details
    }
    
    log_message = f"SECURITY_EVENT: {event_type} - {json.dumps(log_data)}"
    
    if severity == "INFO":
        logger.info(log_message)
    elif severity == "WARNING":
        logger.warning(log_message)
    elif severity == "ERROR":
        logger.error(log_message)
    elif severity == "CRITICAL":
        logger.critical(log_message)
    else:
        logger.info(log_message)