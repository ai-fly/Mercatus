import os
from langchain_mcp_adapters.client import MultiServerMCPClient


current_dir = os.path.dirname(os.path.abspath(__file__))
FILES_OUTPUT_DIR = os.path.join(current_dir, "..", "..", "artifacts", "files")


mcp_servers = MultiServerMCPClient(
    {
        "file_mcp_server": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", FILES_OUTPUT_DIR],
            "transport": "stdio",
        }
    }
)
