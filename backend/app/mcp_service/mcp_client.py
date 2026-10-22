import os
import sys 
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel , Field 

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATION_STACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
GEMINI_API_KEY= os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY")

# Automatically find the current project folder.
# This replaces the hard-coded Windows paths
PROJECT_DIR = Path(__file__).resolve().parent
WEATHER_SERVER_PATH = PROJECT_DIR / "weather_server.py"

# Preserve the complete Windows environment when starting
# local stdio MCP servers.
AVIATION_ENV = os.environ.copy()
AVIATION_ENV["AVIATION_STACK_API_KEY"] = (
    AVIATION_STACK_API_KEY or ""
)

WEATHER_ENV = os.environ.copy()
WEATHER_ENV["OPENWEATHER_API_KEY"] = (
    OPENWEATHER_API_KEY or ""
)


# ==========================================
# LLM
# ==========================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
)


# ==========================================
# MCP client configuration
# ==========================================

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": (
                "https://mcp.tavily.com/mcp/"
                f"?tavilyApiKey={TAVILY_API_KEY}"
            )
        },

        "aviationstack": {
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "aviationstack-mcp"
            ],
            "env": AVIATION_ENV
        },

        "weather": {
            "transport": "stdio",

            # Use the same Python environment that runs app.py.
            "command": sys.executable,

            # Automatically use custom_weather_mcp_server.py
            # from the current project directory.
            "args": [
                str(WEATHER_SERVER_PATH)
            ],

            "env": {
                "OPENWEATHER_API_KEY" : str(OPENWEATHER_API_KEY)
            }
        } , 
      "mcpServers": {
          "Aviationstack MCP": {
              "command": "uvx",
              "args": [
                  "aviationstack-mcp"
                  ],
              "env": {
        "AVIATION_STACK_API_KEY": f"{AVIATION_STACK_API_KEY}"
        }
    }
  }
    }
)


# search_tool = None


# async def initialize_mcp():
#     """
#     Initialize only Tavily.

#     Previously this function initialized all MCP servers,
#     so an AviationStack or Weather failure also caused
#     Tavily hotel search to fail.
#     """

#     global search_tool

#     if search_tool is not None:
#         return

#     tools = await client.get_tools(
#         server_name="tavily"
#     )

#     tools_by_name = {
#         tool.name: tool
#         for tool in tools
#     }

#     search_tool = tools_by_name.get(
#         "tavily_search"
#     )

#     if search_tool is None:
#         available_tools = ", ".join(
#             tools_by_name.keys()
#         )

#         raise RuntimeError(
#             "Tavily MCP connected, but the "
#             "'tavily_search' tool was not found. "
#             f"Available tools: "
#             f"{available_tools or 'none'}"
#         )


async def tavily_mcp_search(query : str ):
    tools = await client.get_tools(
        server_name="tavily"
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    search_tool = tools_by_name.get("tavily_search")
    if search_tool is None :
        raise RuntimeError(
            "Tavily MCP connected, but the "
            "'tavily_search' tool was not found. "
        )
    result = await search_tool.ainvoke({ "query" : query })
    return result


async def aviation_mcp_call( tool_name : str , tool_args : dict = None):
    tools = await client.get_tools(server_name="aviationstack")

    aviation_tools = {
        tool.name: tool
        for tool in tools
    }
    if not aviation_tools:
        raise RuntimeError(
            "AviationStack MCP connected but "
            "returned no tools."
        )
    tool = available_tools.get(tool_name)

    if tool is None:
        available_tools = ", ".join(
            sorted(aviation_tools.keys())
        )

        raise ValueError(
            f"AviationStack tool '{tool_name}' "
            "was not found. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )

    result = await tool.ainvoke(
        tool_args or {}
    )
    return result


weather_tool = None
forecast_tool = None


async def initialize_weather_tools():
    global weather_tool
    global forecast_tool

    if (
        weather_tool is not None
        and forecast_tool is not None
    ):
        return

    if not WEATHER_SERVER_PATH.exists():
        raise FileNotFoundError(
            "Weather MCP server file was not found: "
            f"{WEATHER_SERVER_PATH}"
        )

    # Load only Weather.
    # Tavily and AviationStack will not be started.
    tools = await client.get_tools(
        server_name="weather"
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    weather_tool = tools_by_name.get(
        "get_current_weather"
    )

    forecast_tool = tools_by_name.get(
        "get_forecast"
    )

    missing_tools = []

    if weather_tool is None:
        missing_tools.append(
            "get_current_weather"
        )

    if forecast_tool is None:
        missing_tools.append(
            "get_forecast"
        )

    if missing_tools:
        available_tools = ", ".join(
            tools_by_name.keys()
        )

        raise RuntimeError(
            "Missing Weather MCP tools: "
            f"{', '.join(missing_tools)}. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )

async def weather_mcp_search(city: str):
    await initialize_weather_tools()

    result = await weather_tool.ainvoke(
        {
            "city": city
        }
    )

    return result


async def forecast_mcp_search(city: str):
    await initialize_weather_tools()

    result = await forecast_tool.ainvoke(
        {
            "city": city
        }
    )

    return result


class ExtractDestination(BaseModel):
    city : str = Field(description="The destination city/place of the user , extracted from the query"
                       , examples=["Delhi", "Tokyo" , "Mumbai" , "Bengal" , "Canada" , "Turkey" ]
                         )



async def extract_destination(query : str ):
    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """
    destiny_model = llm.with_structured_output(ExtractDestination)
    response = await destiny_model.ainvoke(prompt)
    
    return response.city 



