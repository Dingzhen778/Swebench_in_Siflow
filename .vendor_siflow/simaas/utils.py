import typing
from functools import partial

import anyio
from fastapi.responses import StreamingResponse
from starlette.types import Send, Scope, Receive
from typing_extensions import override



class OverrideStreamResponse(StreamingResponse):
    """
    Override StreamingResponse to support lazy send response status_code and response headers
    """

    @override
    async def stream_response(self, send: Send) -> None:
        first_chunk = True
        async for chunk in self.body_iterator:
            if first_chunk:
                await self.send_request_header(send)
                first_chunk = False
            if not isinstance(chunk, bytes):
                chunk = chunk.encode(self.charset)
            await send({'type': 'http.response.body', 'body': chunk, 'more_body': True})

        if first_chunk:
            await self.send_request_header(send)
        await send({'type': 'http.response.body', 'body': b'', 'more_body': False})

    async def send_request_header(self, send: Send) -> None:
        await send(
            {
                'type': 'http.response.start',
                'status': self.status_code,
                'headers': self.raw_headers,
            }
        )

    @override
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async with anyio.create_task_group() as task_group:
            async def wrap(func: typing.Callable[[], typing.Coroutine]) -> None:
                await func()
                await task_group.cancel_scope.cancel()

            task_group.start_soon(wrap, partial(self.stream_response, send))
            await wrap(partial(self.listen_for_disconnect, receive))

        if self.background is not None:
            await self.background()