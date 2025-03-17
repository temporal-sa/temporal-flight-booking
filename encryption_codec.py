import base64
import os
from typing import Iterable, List
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec

# Encryption Key (should be securely stored in production)
default_key = b"sa-rocks!sa-rocks!sa-rocks!yeah!"
default_key_id = "c2EtZGVtby1rZXk="


class EncryptionCodec(PayloadCodec):
    """Encrypts workflow/activity payloads using AES-GCM encryption."""

    def __init__(self, key_id: str = default_key_id, key: bytes = default_key) -> None:
        super().__init__()
        self.key_id = key_id
        self.encryptor = AESGCM(key)

    async def encode(self, payloads: Iterable[Payload]) -> List[Payload]:
        """Encrypt all payloads."""
        return [
            Payload(
                metadata={
                    "encoding": b"binary/encrypted",
                    "encryption-key-id": self.key_id.encode(),
                },
                data=self.encrypt(p.SerializeToString()),
            )
            for p in payloads
        ]

    async def decode(self, payloads: Iterable[Payload]) -> List[Payload]:
        """Decrypt all payloads."""
        ret: List[Payload] = []
        for p in payloads:
            if p.metadata.get("encoding", b"").decode() != "binary/encrypted":
                ret.append(p)
                continue
            key_id = p.metadata.get("encryption-key-id", b"").decode()
            if key_id != self.key_id:
                raise ValueError(
                    f"Unrecognized key ID {key_id}. Current key ID is {self.key_id}."
                )
            ret.append(Payload.FromString(self.decrypt(p.data)))
        return ret

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-GCM."""
        nonce = os.urandom(12)  # 12-byte nonce for AES-GCM
        return nonce + self.encryptor.encrypt(nonce, data, None)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data using AES-GCM."""
        return self.encryptor.decrypt(data[:12], data[12:], None)