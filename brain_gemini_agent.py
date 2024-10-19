"""
This agent can respond to plain text questions with data from an AI model and convert it into a machine readable format.
"""
from uagents import Agent, Context, Model
import requests
import json
import google.generativeai as genai

 
BrainGemini = Agent(
   name="BrainGemini",
   port=8001,
   seed="ReceiverAgent secret phrase",
   endpoint=["http://127.0.0.1:8001/submit"],
)

api_key = "AIzaSyAMOD8ikp9oSEK57ckFk2XFDPtULPm_jPw"

genai.configure(api_key=api_key)


# Define the generation config
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

# Initialize the Generative Model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    # generation_config=generation_config,
    generation_config={"response_mime_type": "application/json"},
    system_instruction="You are a helpful assistant for providing multimodal routes. I would like you to return the route in proper JSON format with double quotes for keys and string values, and where each subroute is a jSON object. \n{\nroute1Info : \n{\ntotalTime: int,\ndistance: \"total distance in km\"\ndescription: \"One liner describing route\",\nexpression:  \"Describes the sequential order of the modes of transport taken and the number if transit (e.g walking | transit | driving | bicycling),\nefficiency: \"time saved\",\neffectiveness: \"CO2 emissions approx only for driving; otherwise leave as null\",\nhealth: \"total calories burned; otherwise leave as null\"\n},\nroute1: [\n    {\n        start: \"Starting location full address, as it is on google maps\",\n        end: \"Destination location full address, as it is on google maps\",\n        timeTaken: \"Duration of this segment (e.g., '10 mins', '25 mins')\",\n        modeOfTransport: \"The mode of transport for this segment (options: 'driving', 'walking', 'bicycling', 'transit')\",\n        nameOfTransport: \"For public transit, provide the name or number of the transport (e.g., 'Bus 22', 'Line 1 Subway'); otherwise leave as an empty string\",\n        calories: \"Estimated calories burned for this segment (if applicable, e.g., for walking or cycling); otherwise leave as null\",\n        gasUsed: \"Estimated gas used in liters (if applicable, e.g., for driving); otherwise leave as null\",\n        totalCost: \"Cost incurred for this segment (e.g., ticket prices, tolls, fuel cost); leave as null if not applicable\"\n    }\n]}\n\nDon't turn the keys into strings, don't include any other text. \n",
)



class Request(Model):
    text: str


class Error(Model):
    text: str


class Data(Model):
    value: float
    unit: str
    timestamp: str
    confidence: float
    source: str
    notes: str

class JSONResponse(Model):
    response: dict  


def get_base_route(context: str, prompt: str, max_tokens: int = 1024):
    """Send a prompt and context to the AI model and return the content of the completion"""
    response = model.generate_content(prompt)
    route_data = json.loads(response.text)
    # print(json.dumps(route_data))

    return Request(text=str(json.dumps(route_data)))
    

@BrainGemini.on_message(model=Request)
async def handle_request(ctx: Context, sender: str, request: Request):
    """Message handler for data requests sent to this agent"""
    ctx.logger.info(f"Got request from {sender}: {request.text}")
    response = get_base_route(ctx, request.text)
    await ctx.send(sender, response)
    
@BrainGemini.on_interval(15)
async def interval_task(ctx: Context):
    try:
        print("I, brain, am alive", BrainGemini.address)
    except AttributeError:
        print("BrainGemini does not have an 'address' attribute.")

		
if __name__ == "__main__":
    BrainGemini.run()
    