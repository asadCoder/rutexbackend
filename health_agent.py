"""
This agent can ask a question to the AI model agent and display the answer.
"""
from uagents import Agent, Context, Model

AGENT_MAILBOX_KEY = "bda4ea99-565a-4e71-80ef-508573ada912"
GOOGLE_FIT_AGENT_ADDRESS = "agent1qtlrw0pv7mgaz324j6euxka66knmxnch8grzfsuj6gd68zp5fvhr2m98ez0"
STARTER_AGENT_ADDRESS = "agent1qdw67s95esk0zwn8qxf0ln22e8zah9rqfrqqa4qyda7mjtpf3hsw640wuwr"



HealthAgent = Agent(
    name="HealthAgent",
    port=8007,
    seed="HealthAgent secret phrase",
    # endpoint=["http://127.0.0.1:8007/submit"],
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)


class Message(Model):
    message: str

class Request(Model):
    text: str


class Error(Model):
    text: str


    
class JSONResponse(Model):
    response: dict  


@HealthAgent.on_message(model=Request)
async def handle_data(ctx: Context, sender: str,  msg: Request):
    """Log response from AI Model Agent """
    ctx.logger.info(f"Got response from {sender}: {msg.text}")

    #Noete: this agent does not block this agent (yet?), the child nodes sends the stats to the starter_agent
    if msg.text == 'getStepsNeeded':
        ctx.logger.info("Getting needed steps")
        await ctx.send(GOOGLE_FIT_AGENT_ADDRESS, Request(text="getNeededSteps"))


    
		

@HealthAgent.on_message(model=Error)
async def handle_error(ctx: Context, sender: str, error: Error):
    """log error from AI Model Agent"""
    ctx.logger.info(f"Got error from AI model agent: {error}")

	    
@HealthAgent.on_interval(60)
async def interval_task(ctx: Context):
    print("I, health, am alive", HealthAgent.address)


if __name__ == "__main__":
    HealthAgent.run()
    