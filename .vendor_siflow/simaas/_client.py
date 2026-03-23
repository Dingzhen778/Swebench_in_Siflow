from __future__ import annotations

import os
import time
import random
import string
import hashlib
from typing import Union, Mapping
from dataclasses import dataclass
from typing_extensions import override

import httpx

from . import resources, _exceptions
from ._qs import Querystring
from ._types import (
    NOT_GIVEN,
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
)
from ._utils import is_given
from ._version import __version__
from ._streaming import Stream as Stream
from ._streaming import AsyncStream as AsyncStream
from ._exceptions import APIStatusError
from ._base_client import DEFAULT_MAX_RETRIES, SyncAPIClient

__all__ = [
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "resources",
    "SiMaas",
]


@dataclass
class ClusterInfo:
    name: str
    base_url: str


@dataclass
class RegionInfo:
    region: str
    clusters: dict[str, ClusterInfo]


_region_infos = {
    "ap-southeast": RegionInfo(
        region="ap-southeast",
        clusters={
            "aries": ClusterInfo("aries", "https://console.scitix.ai/smapi"),
            "cks": ClusterInfo("cks", "https://console.scitix-inner.ai/smapi"),
        },
    ),
}


class SiMaas(SyncAPIClient):
    sieval_cases: resources.SiEvalCases
    sieval_datasets: resources.SiEvalDatasets
    sieval_tasks: resources.SiEvalTasks

    def __init__(
        self,
        *,
        region: str = "ap-southeast",
        cluster: str = "aries",
        access_key_id: str | None = None,
        access_key_secret: str | None = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client. See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous simaas client instance."""
        if region not in _region_infos:
            raise ValueError(f"region must be one of {','.join(_region_infos.keys())}")
        if cluster not in _region_infos[region].clusters:
            raise ValueError(f"cluster must be one of {','.join(_region_infos[region].clusters.keys())}")
        self.region, self.cluster = region, cluster
        base_url = _region_infos[region].clusters[cluster].base_url

        if access_key_id is None:
            access_key_id = os.environ.get("SIFLOW_ACCESS_KEY_ID")
        if access_key_id is None:
            raise ValueError(
                "The access_key_id option must be set either by passing access_key_id to the client or by setting the SIFLOW_ACCESS_KEY_ID environment variable"
            )
        if access_key_secret is None:
            access_key_secret = os.environ.get("SIFLOW_ACCESS_KEY_SECRET")
        if access_key_secret is None:
            raise ValueError(
                "The access_key_secret option must be set either by passing access_key_secret to the client or by setting the SIFLOW_ACCESS_KEY_SECRET environment variable"
            )
        self._access_key_id = access_key_id
        self._access_key_secret = access_key_secret

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

        self._default_stream_cls = Stream
        self.sieval_cases = resources.SiEvalCases(self)
        self.sieval_datasets = resources.SiEvalDatasets(self)
        self.sieval_tasks = resources.SiEvalTasks(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = "".join(random.choices(string.digits, k=10))
        plaintext = self._access_key_secret + nonce + timestamp
        signature = hashlib.sha256(plaintext.encode("utf-8")).digest().hex()
        return {
            "Randstr": nonce,
            "X-Region": self.region,
            "X-Cluster": self.cluster,
            "Timestamp": timestamp,
            "AppID": self._access_key_id,
            "Signature": signature,
        }

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        region: str | None = None,
        cluster: str | None = None,
        access_key_id: str | None = None,
        access_key_secret: str | None = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = NOT_GIVEN,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
    ) -> SiMaas:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.

        It should be noted that this does not share the underlying httpx client class which may lead
        to performance issues.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        return self.__class__(
            region=region or self.region,
            cluster=cluster or self.cluster,
            access_key_id=access_key_id or self._access_key_id,
            access_key_secret=access_key_secret or self._access_key_secret,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client or self._client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).task.list(...)
    with_options = copy

    def __del__(self) -> None:
        if not hasattr(self, "_has_custom_http_client") or not hasattr(self, "close"):
            # this can happen if the '__init__' method raised an error
            return

        if self._has_custom_http_client:
            return

        self.close()

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class SiMaasWithRawResponse:
    def __init__(self, client: SiMaas) -> None:
        self.sieval_cases = resources.SiEvalCasesWithRawResponse(client.sieval_cases)
        self.sieval_datasets = resources.SiEvalDatasetsWithRawResponse(client.sieval_datasets)
        self.sieval_tasks = resources.SiEvalTasksWithRawResponse(client.sieval_tasks)
