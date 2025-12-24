# secret_storage.py
#
# Copyright 2025 Nokse <nokse@posteo.com>
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or (at
# your option) any later version.
#
# This file is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import json
import platform
from typing import Any, Dict, Tuple

import tidalapi

import logging
logger = logging.getLogger(__name__)

# Platform-specific imports
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    
    # Windows Credential Manager API
    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2
    
    class CREDENTIAL_ATTRIBUTE(ctypes.Structure):
        _fields_ = [
            ("Keyword", wintypes.LPWSTR),
            ("Flags", wintypes.DWORD),
            ("ValueSize", wintypes.DWORD),
            ("Value", ctypes.POINTER(ctypes.c_byte)),
        ]
    
    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.POINTER(CREDENTIAL_ATTRIBUTE)),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]
    
    advapi32 = ctypes.windll.advapi32
    advapi32.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    advapi32.CredReadW.restype = wintypes.BOOL
    advapi32.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
    advapi32.CredWriteW.restype = wintypes.BOOL
    advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi32.CredDeleteW.restype = wintypes.BOOL
    advapi32.CredFree.argtypes = [ctypes.c_void_p]
    advapi32.CredFree.restype = None
else:
    from gi.repository import Secret


class SecretStore:
    def __init__(self, session: tidalapi.Session) -> None:
        super().__init__()

        logger.info("initializing secret store")

        self.version = "0.0"
        self.session: tidalapi.Session = session
        self.token_dictionary: Dict[str, str] = {}
        self.key: str = "high-tide-login"

        if IS_WINDOWS:
            self._init_windows()
        else:
            self._init_linux()

    def _init_windows(self) -> None:
        """Initialize secret store on Windows using Credential Manager."""
        try:
            password = self._windows_read_credential()
            if password:
                json_data = json.loads(password)
                self.token_dictionary = json_data
        except Exception:
            logger.exception("Failed to load secret store, resetting")
            self.token_dictionary = {}

    def _init_linux(self) -> None:
        """Initialize secret store on Linux using libsecret."""
        self.attributes: Dict[str, Secret.SchemaAttributeType] = {
            "version": Secret.SchemaAttributeType.STRING
        }

        self.schema = Secret.Schema.new(
            "io.github.nokse22.high-tide", Secret.SchemaFlags.NONE, self.attributes
        )

        # Ensure the Login keyring is unlocked (https://github.com/Nokse22/high-tide/issues/97)
        if True:
            service = Secret.Service.get_sync(Secret.ServiceFlags.NONE)
            if service:
                collection = Secret.Collection.for_alias_sync(
                    service, Secret.COLLECTION_DEFAULT, Secret.CollectionFlags.NONE
                )
                if collection and collection.get_locked():
                    logger.info("Collection is locked, attempting to unlock")
                    service.unlock_sync([collection])

        password = Secret.password_lookup_sync(self.schema, {}, None)
        try:
            if password:
                json_data = json.loads(password)
                self.token_dictionary = json_data
        except Exception:
            logger.exception("Failed to load secret store, resetting")
            self.token_dictionary = {}

    def _windows_read_credential(self) -> str | None:
        """Read a credential from Windows Credential Manager."""
        cred_ptr = ctypes.POINTER(CREDENTIAL)()
        if advapi32.CredReadW(self.key, CRED_TYPE_GENERIC, 0, ctypes.byref(cred_ptr)):
            try:
                cred = cred_ptr.contents
                if cred.CredentialBlobSize > 0:
                    password_bytes = bytes(cred.CredentialBlob[:cred.CredentialBlobSize])
                    return password_bytes.decode("utf-16-le")
            finally:
                advapi32.CredFree(cred_ptr)
        return None

    def _windows_write_credential(self, password: str) -> bool:
        """Write a credential to Windows Credential Manager."""
        password_bytes = password.encode("utf-16-le")
        blob_size = len(password_bytes)
        blob = (ctypes.c_byte * blob_size).from_buffer_copy(password_bytes)
        
        cred = CREDENTIAL()
        cred.Flags = 0
        cred.Type = CRED_TYPE_GENERIC
        cred.TargetName = self.key
        cred.CredentialBlobSize = blob_size
        cred.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_byte))
        cred.Persist = CRED_PERSIST_LOCAL_MACHINE
        cred.UserName = "high-tide"
        
        return bool(advapi32.CredWriteW(ctypes.byref(cred), 0))

    def _windows_delete_credential(self) -> bool:
        """Delete a credential from Windows Credential Manager."""
        return bool(advapi32.CredDeleteW(self.key, CRED_TYPE_GENERIC, 0))

    def has_credentials(self) -> bool:
        """Check if valid credentials are stored.

        Returns:
            bool: True if all required tokens are present, False otherwise
        """
        required_keys = ["token-type", "access-token", "refresh-token"]
        return all(key in self.token_dictionary for key in required_keys)

    def get(self) -> Tuple[str, str, str]:
        """Get the stored authentication tokens.

        Returns:
            tuple: A tuple containing (token_type, access_token, refresh_token)
        """
        return (
            self.token_dictionary["token-type"],
            self.token_dictionary["access-token"],
            self.token_dictionary["refresh-token"],
        )

    def clear(self) -> None:
        """Clear all stored authentication tokens from memory and keyring.

        Removes tokens from the internal dictionary and deletes them from
        the system keyring/secret storage.
        """
        self.token_dictionary.clear()

        if IS_WINDOWS:
            self._windows_delete_credential()
        else:
            Secret.password_clear_sync(self.schema, {}, None)

    def save(self) -> None:
        """Save the current session tokens to secure storage.

        Stores the session's token_type, access_token, and refresh_token
        in the system keyring for persistent authentication.
        """
        token_type: str = self.session.token_type
        access_token: str = self.session.access_token
        refresh_token: str = self.session.refresh_token
        expiry_time: Any = self.session.expiry_time

        self.token_dictionary = {
            "token-type": token_type,
            "access-token": access_token,
            "refresh-token": refresh_token,
            "expiry-time": str(expiry_time),
        }

        json_data: str = json.dumps(self.token_dictionary)

        if IS_WINDOWS:
            if not self._windows_write_credential(json_data):
                logger.error("Failed to save credentials to Windows Credential Manager")
        else:
            Secret.password_store_sync(
                self.schema, {}, Secret.COLLECTION_DEFAULT, self.key, json_data, None
            )
