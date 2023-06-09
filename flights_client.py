from temporalio.client import Client, TLSConfig
from temporalio.runtime import PrometheusConfig, Runtime, TelemetryConfig
import temporalio.converter
from encryption_codec import EncryptionCodec
import dataclasses
from typing import Optional
import os

def init_runtime_with_prometheus(port: int) -> Runtime:
    return Runtime(
        telemetry=TelemetryConfig(
            metrics=PrometheusConfig(bind_address=f"0.0.0.0:{port}")
        )
    )

async def get_client()-> Client:

    if (
        os.getenv("TEMPORAL_MTLS_TLS_CERT")
        and os.getenv("TEMPORAL_MTLS_TLS_KEY") is not None
    ):
        server_root_ca_cert: Optional[bytes] = None
        with open(os.getenv("TEMPORAL_MTLS_TLS_CERT"), "rb") as f:
            client_cert = f.read()

        with open(os.getenv("TEMPORAL_MTLS_TLS_KEY"), "rb") as f:
            client_key = f.read()

        # Start client
        client = await Client.connect(
            os.getenv("TEMPORAL_HOST_URL"),
            namespace=os.getenv("TEMPORAL_NAMESPACE"),
            tls=TLSConfig(
                server_root_ca_cert=server_root_ca_cert,
                client_cert=client_cert,
                client_private_key=client_key,
            ),
            data_converter=dataclasses.replace(
                temporalio.converter.default(), payload_codec=EncryptionCodec()
            ),            
        )
    else:
        client = await Client.connect(
            "localhost:7233",
        )

    return client    

async def get_worker_client()-> Client:
    runtime = init_runtime_with_prometheus(os.getenv("TEMPORAL_WORKER_METRICS_PORT"))

    if (
        os.getenv("TEMPORAL_MTLS_TLS_CERT")
        and os.getenv("TEMPORAL_MTLS_TLS_KEY") is not None
    ):
        server_root_ca_cert: Optional[bytes] = None
        with open(os.getenv("TEMPORAL_MTLS_TLS_CERT"), "rb") as f:
            client_cert = f.read()

        with open(os.getenv("TEMPORAL_MTLS_TLS_KEY"), "rb") as f:
            client_key = f.read()

        # Start client
        client = await Client.connect(
            os.getenv("TEMPORAL_HOST_URL"),
            runtime=runtime,
            namespace=os.getenv("TEMPORAL_NAMESPACE"),
            tls=TLSConfig(
                server_root_ca_cert=server_root_ca_cert,
                client_cert=client_cert,
                client_private_key=client_key,
            ),
            data_converter=dataclasses.replace(
                temporalio.converter.default(), payload_codec=EncryptionCodec()
            ),             
        )
    else:
        client = await Client.connect(
            "localhost:7233",
            runtime=runtime,
        )

    return client    