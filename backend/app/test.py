
from agents.tools.tavily_tool import tavily_search
from agents.tools.flight_tool import search_flights
from agents.graph import run_travel_agent
# res = tavily_search("Best hotels in india")

# print(res)

# res = search_flights("The best flight from delhi to tokyo")
# print(res)

user_input = input("Enter travel request : ")

response = run_travel_agent(
  user_input=user_input ,
  thread_id= "test_user"
)

print("\nFinal Response : \n")
print(response["answer"])

