from agents.state import TravelState 
from agents.tools.flight_tool import search_flights
from agents.tools.tavily_tool import tavily_search 
from langchain.messages import AIMessage , HumanMessage , SystemMessage 
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_service.mcp_client import aviation_mcp_call , tavily_mcp_search , forecast_mcp_search , weather_mcp_search ,extract_destination
import asyncio 

from dotenv import load_dotenv 

load_dotenv()

llm =  ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash-lite"
)


# def flight_agent(state: TravelState):
#     query = state["user_query"]
#     flight_data = search_flights(query)

#     return {
#         "flight_results": flight_data,
#         "messages": [
#             AIMessage(content="Flight results fetched.")
#         ],
#         "llm_calls": state.get("llm_calls", 0) + 1
#     }

# Flight Tool Router Prompt
FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""



# Flight Agent
def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:

        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call(
                "list_airlines"
            )
        )


        print("\nAIRPORTS:", airports)
        print("\nAIRLINES:", airlines)

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000]
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(content=prompt)
        ])

        flight_data = response.content

    except Exception as e:

        flight_data = f"Flight information unavailable: {str(e)}"

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }



def hotel_agent(state: TravelState):
    print("\nINSIDE HOTEL AGENT\n")
    query = f"Best hotels for {state['user_query']}"
    hotel_results = asyncio.run(tavily_mcp_search(query))

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched.")
        ],
        "llm_calls": state.get("llm_calls", 0) + 1
    }





def weather_agent(state: TravelState):
    print("\nINSIDE WEATHER AGENT\n")
    city =   asyncio.run( extract_destination(state["user_query"]) )
    print(city)
    weather_data = asyncio.run(
        weather_mcp_search(city)
    )
    print(weather_data)
    forecast_data = asyncio.run(
        forecast_mcp_search(city)
    )
    return {
        "weather_results": f"""
        Current Weather:
        {weather_data}

        Forecast:
        {forecast_data}
        """,
        "messages": [
            AIMessage(
                content="Weather information fetched"
            )
        ]
    }


def itinerary_agent(state: TravelState):
    print("\nINSIDE ITINERARY AGENT\n")
    prompt = f"""
Create a complete travel itinerary.

User Query:
{state['user_query']}

Flight Results:
{state['flight_results']}

Hotel Results:
{state['hotel_results']}

Weather Results:
{state['weather_results']}

Make the itinerary practical, budget-aware, and easy to follow.
"""

    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content[0]['text'],
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


def final_agent(state: TravelState):
    print("\nINSIDE FINAL AGENT\n")
    final_prompt = f"""
Generate the final travel response for the user.

User Request:
{state['user_query']}

Flights:
{state['flight_results']}

Hotels:
{state['hotel_results']}

Weather:
{state['weather_results']}

Itinerary:
{state['itinerary']}

Format the final answer beautifully using these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Weather Information
5. Day-by-Day Itinerary
6. Estimated Budget
7. Final Recommendations


Important:
- Be clear and practical.
- Mention that live flight API may not provide ticket prices if pricing is unavailable.
- Include weather-based travel advice.
- Keep the response useful for real travel planning.
"""

    response = llm.invoke([
        SystemMessage(content="You are a professional AI travel booking assistant."),
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response.content[0]['text']],
        "llm_calls": state.get("llm_calls", 0) + 1
    }