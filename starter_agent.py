"""
This agent can ask a question to the AI model agent and display the answer.
"""
from uagents import Agent, Context, Model
import asyncio
import json


# Global variables to hold the response and event
response_event = asyncio.Event()
responseFromGemini = None

StarterAgent = Agent(
    name="StarterAgent",
    port=8000,
    seed="SenderAgent secret phrase",
    endpoint=["http://127.0.0.1:8000/submit"],
)

# Write your question here
QUESTION = "give me a route from UTSC to union station"

AI_MODEL_AGENT_ADDRESS = "agent1qd8ymq4najh5wycvhvhcw3l5lmkgkvkrqevrs6wpp5ll0khfdq6v2cq6859"


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


# @StarterAgent.on_event("startup")
# async def ask_question(ctx: Context):
#     """Send question to AI Model Agent"""
#     ctx.logger.info(f"Asking question to AI model agent: {QUESTION}")
#     await ctx.send(AI_MODEL_AGENT_ADDRESS, Request(text=QUESTION))

@StarterAgent.on_message(model=Request)
async def handle_data(ctx: Context, sender: str, request: Request):
    global responseFromGemini
    """Log response from AI Model Agent """
    ctx.logger.info(f"Got response from AI model agent: {request}")
    responseFromGemini = json.loads(request.text)
	# Set the event to indicate the response has been received
    response_event.set()

@StarterAgent.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    """log error from AI Model Agent"""
    ctx.logger.info(f"Got error from AI model agent: {error}")


@StarterAgent.on_rest_post("/post/route", Request, JSONResponse)
async def handle_post(ctx: Context, req: Request) -> JSONResponse:
    global response_from_ai_model, response_event
    
    # Access request data properly
    userInput = req.text
    ctx.logger.info(f"Received text: {userInput}")
    
	# Reset the event before sending the request
    response_event.clear()
    
    # Generate the route and create a response
    await ctx.send(AI_MODEL_AGENT_ADDRESS, Request(text=userInput))
    
    await response_event.wait()
    ctx.logger.info(f"Received return to post: {responseFromGemini}")

    return JSONResponse(response=responseFromGemini)
    

	    
@StarterAgent.on_interval(15)
async def interval_task(ctx: Context):
    print("I, starter, am alive", StarterAgent.address)

if __name__ == "__main__":
    StarterAgent.run()
    