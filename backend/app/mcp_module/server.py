"""MCP server instance for Endurain."""

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

from mcp_module.auth import EndurainTokenVerifier
import core.config as core_config

mcp_server = FastMCP(
    "Endurain",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    token_verifier=EndurainTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(core_config.ENDURAIN_HOST),
        resource_server_url=AnyHttpUrl(
            core_config.ENDURAIN_HOST
        ),
    ),
)

# Tool/resource/prompt imports — registers decorators
import mcp_module.tools.activities  # noqa: F401
import mcp_module.tools.health  # noqa: F401
import mcp_module.tools.gear  # noqa: F401
import mcp_module.tools.profile  # noqa: F401
