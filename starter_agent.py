"""
This agent can ask a question to the AI model agent and display the answer.
"""
from uagents import Agent, Context, Model
import asyncio
import json


StarterAgent = Agent(
    name="StarterAgent",
    port=8000,
    seed="SenderAgent secret phrase",
    endpoint=["http://127.0.0.1:8000/submit"],
    mailbox="01feeae0-5cad-4706-a067-4070825e206d"
)


AI_MODEL_AGENT_ADDRESS = "agent1qd8ymq4najh5wycvhvhcw3l5lmkgkvkrqevrs6wpp5ll0khfdq6v2cq6859"
ROUTE_VERIFYER_AGENT_ADDRESS = "agent1qtg6p77ujvm02mrd9lrp4naxppm0aq24vhspg96z3yfwgv5nhe5cvmy6grd"
HEALTH_AGENT_ADDRESS = "agent1q0enqfa6fueh6fz6xt56hm5s5gjrt4exyxvda97dnxxun0wuv4ks52xezvv"

# Global variables to hold the response and event
response_event = asyncio.Event()
responseFromAgent = None

route = None

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

@StarterAgent.on_message(model=Request)
async def handle_data(ctx: Context, sender: str, request: Request):
    global responseFromAgent
    """Log response from AI Model Agent """
    ctx.logger.info(f"Got response from agent: {request}")
    # responseFromAgent = json.loads(request.text)
    responseFromAgent = request.text
	# Set the event to indicate the response has been received
    response_event.set()

@StarterAgent.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    """log error from AI Model Agent"""
    ctx.logger.info(f"Got error from AI model agent: {error}")


@StarterAgent.on_rest_post("/post/route", Request, JSONResponse)
async def handle_post(ctx: Context, req: Request) -> JSONResponse:
    global response_from_ai_model, response_event, route

    # Handle CORS for OPTIONS request
    if req.text is None:  # Assuming OPTIONS requests won't have body
        ctx.response_headers["Access-Control-Allow-Origin"] = "*"  # Allow the specific origin
        # return {"status": 204}  # No Content response
    
    # Access request data properly
    userInput = req.text
    ctx.logger.info(f"Received text: {userInput}")
    
	# Reset the event before sending the request
    response_event.clear()
    
    # Generate the route and create a response
    await ctx.send(AI_MODEL_AGENT_ADDRESS, Request(text=userInput))
    
    await response_event.wait()
    ctx.logger.info(f"Returned from gemini: {responseFromAgent}")

    # verify the route using verifyer agent
    response_event.clear()
    await ctx.send(ROUTE_VERIFYER_AGENT_ADDRESS, Request(text=responseFromAgent))

    await response_event.wait()
    ctx.logger.info(f"Returned from verifier: {responseFromAgent}")
    route = json.loads(responseFromAgent)

    # get health stats...currently we are only getting steps goal for the user
    response_event.clear()
    await ctx.send(HEALTH_AGENT_ADDRESS, Request(text="getStepsNeeded"))

    await response_event.wait()
    ctx.logger.info(f"Returned from health agent: {responseFromAgent}")

    route["StepsNeeded"] = responseFromAgent

    return JSONResponse(response=route)

	    
@StarterAgent.on_interval(60)
async def interval_task(ctx: Context):
    print("I, starter, am alive", StarterAgent.address)

if __name__ == "__main__":
    StarterAgent.run()
    