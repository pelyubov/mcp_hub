import contextlib

from fastapi import FastAPI

from tools import search


# Create a combined lifespan to manage both session managers
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(search.mcp.session_manager.run())
        yield
                    
app = FastAPI(lifespan=lifespan)
app.mount("/search", search.mcp.streamable_http_app())



