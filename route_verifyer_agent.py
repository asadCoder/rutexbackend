from uagents import Agent, Bureau, Context, Model
import requests
import json
import googlemaps
from datetime import datetime


gmaps = googlemaps.Client(key='AIzaSyDmFTRzH4UebgjP7ifLPTpo8WAmC0qXux8')
STARTER_AGENT_ADDRESS = "agent1qdw67s95esk0zwn8qxf0ln22e8zah9rqfrqqa4qyda7mjtpf3hsw640wuwr"


 
RouteVeriferAgent = Agent(
   name="RouteVeriferAgent",
   port=8004,
   seed="RouteVeriferAgent secret phrase",
   endpoint=["http://127.0.0.1:8004/submit"],
)

GoogleDirAgent = Agent(
   name="GoogleDirAgent",
   port=8005,
   seed="GoogleDirAgent recovery phrase",
   endpoint=["http://127.0.0.1:8005/submit"],
)

GoogleDirAgent_address = GoogleDirAgent.address


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


def get_completion(context: str, prompt: str, max_tokens: int = 1024):
    """Send a prompt and context to the AI model and return the content of the completion"""
        

@RouteVeriferAgent.on_message(model=Request)
async def handle_request(ctx: Context, sender: str, request: Request):
    """Message handler for data requests sent to this agent"""
    ctx.logger.info(f"Got request from {sender}: {request.text}")

    #first verify times from google
    await ctx.send(GoogleDirAgent_address, request)


    
    
@RouteVeriferAgent.on_interval(15)
async def interval_task(ctx: Context):
    try:
        print("I, RouteVeriferAgent, am alive", RouteVeriferAgent.address)
        print("I, GoogleDirAgent, am alive", GoogleDirAgent.address)
    except AttributeError:
        print("RouteVeriferAgent does not have an 'address' attribute.")


@GoogleDirAgent.on_message(model=Request)
async def google_dir_message_handler(ctx: Context, sender: str, msg: Request):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")

    ctx.logger.info(f"Before updating: {msg.text}")
    updated_path = update_route_with_directions(json.loads(msg.text))
    ctx.logger.info(f"After updating: {updated_path}")
    await ctx.send(STARTER_AGENT_ADDRESS, Request(text=str(updated_path)))



def update_route_with_directions(route_plan):
    route_info = route_plan.get('route1Info', {})
    route_steps = route_plan.get('route1', [])

    total_distance = 0  # in meters
    total_duration = 0  # in seconds

    updated_steps = []

    for step in route_steps:
        origin = step.get('start')
        destination = step.get('end')
        mode = step.get('modeOfTransport', 'driving')

        if not origin or not destination:
            continue  # Skip if start or end is missing

        now = datetime.now()
        directions_result = gmaps.directions(origin, destination, mode, departure_time=now)
        
        if not directions_result:
            continue  # Skip if API call failed

        # Extract the first route and first leg
        first_route = directions_result[0]  # Get the first route
        first_leg = first_route['legs'][0]  # Get the first leg of that route

        # Extract distance and duration from the leg
        leg_distance = first_leg['distance']['value']  # in meters
        leg_duration = first_leg['duration']['value']  # in seconds

        total_distance += leg_distance
        total_duration += leg_duration

        # Update step with accurate data
        step["timeTaken"] = f"{int(leg_duration / 60)} mins"
        step["distance"] = f"{leg_distance / 1000:.2f} km"

        # Add any additional calculations (e.g., calories, gas used)
        if step["modeOfTransport"] == "walking":
            # Estimate calories burned (approx 50 kcal per km)
            calories = int((leg_distance / 1000) * 50)
            step["calories"] = calories
        elif step["modeOfTransport"] == "bicycling":
            # Estimate calories burned (approx 30 kcal per km)
            calories = int((leg_distance / 1000) * 30)
            step["calories"] = calories
        else:
            step["calories"] = None

        if step["modeOfTransport"] == "driving":
            # Estimate gas used (approx 8 liters per 100 km)
            gas_used = (leg_distance / 1000) * 8 / 100  # liters
            step["gasUsed"] = f"{gas_used:.2f} liters"
        else:
            step["gasUsed"] = None

        # Assume totalCost is not applicable unless specified
        step["totalCost"] = None

        # Update nameOfTransport if mode is transit
        if step["modeOfTransport"] == "transit":
            # Extract transit details
            transit_details = first_leg.get("transit_details", {})
            line = transit_details.get("line", {})
            vehicle = line.get("vehicle", {})
            step["nameOfTransport"] = line.get("short_name") or line.get("name") or vehicle.get("name", "")
        else:
            step["nameOfTransport"] = ""

        updated_steps.append(step)

    # Update route_info with total distance and time
    route_info["totalTime"] = int(total_duration / 60)  # in minutes
    route_info["distance"] = f"{total_distance / 1000:.2f} km"

    # Recalculate efficiency, effectiveness, and health if needed
    # For simplicity, we'll leave these as is unless specific calculations are required

    # Update the route plan
    route_plan["route1Info"] = route_info
    route_plan["route1"] = updated_steps

    return json.dumps(route_plan)


# def update_route_with_directions(route_plan):
    endpoint = 'https://maps.googleapis.com/maps/api/directions/json'

    route_info = route_plan.get('route1Info', {})
    route_steps = route_plan.get('route1', [])

    total_distance = 0  # in meters
    total_duration = 0  # in seconds

    updated_steps = []

    for step in route_steps:
        origin = step.get('start')
        destination = step.get('end')
        mode = step.get('modeOfTransport', 'driving')

        if not origin or not destination:
            continue  # Skip if start or end is missing

        now = datetime.now()
        leg = gmaps.directions(origin, destination, mode, departure_time=now)
        
        if not leg:
            continue  # Skip if API call failed

        # Extract distance and duration
        leg_distance = leg['distance']['value']  # in meters
        leg_duration = leg['duration']['value']  # in seconds

        total_distance += leg_distance
        total_duration += leg_duration

        # Update step with accurate data
        step['timeTaken'] = f"{int(leg_duration / 60)} mins"
        step['distance'] = f"{leg_distance / 1000:.2f} km"

        # Add any additional calculations (e.g., calories, gas used)
        if step['modeOfTransport'] == 'walking':
            # Estimate calories burned (approx 50 kcal per km)
            calories = int((leg_distance / 1000) * 50)
            step['calories'] = calories
        elif step['modeOfTransport'] == 'bicycling':
            # Estimate calories burned (approx 30 kcal per km)
            calories = int((leg_distance / 1000) * 30)
            step['calories'] = calories
        else:
            step['calories'] = None

        if step['modeOfTransport'] == 'driving':
            # Estimate gas used (approx 8 liters per 100 km)
            gas_used = (leg_distance / 1000) * 8 / 100  # liters
            step['gasUsed'] = f"{gas_used:.2f} liters"
        else:
            step['gasUsed'] = None

        # Assume totalCost is not applicable unless specified
        step['totalCost'] = None

        # Update nameOfTransport if mode is transit
        if step['modeOfTransport'] == 'transit':
            # Extract transit details
            transit_details = leg.get('transit_details', {})
            line = transit_details.get('line', {})
            vehicle = line.get('vehicle', {})
            step['nameOfTransport'] = line.get('short_name') or line.get('name') or vehicle.get('name', '')
        else:
            step['nameOfTransport'] = ''

        updated_steps.append(step)

    # Update route_info with total distance and time
    route_info['totalTime'] = int(total_duration / 60)  # in minutes
    route_info['distance'] = f"{total_distance / 1000:.2f} km"

    # Recalculate efficiency, effectiveness, and health if needed
    # For simplicity, we'll leave these as is unless specific calculations are required

    # Update the route plan
    route_plan['route1Info'] = route_info
    route_plan['route1'] = updated_steps

    return route_plan
		
bureau = Bureau(
    port=8006,
    endpoint=["http://127.0.0.1:8006/submit"],
)
bureau.add(RouteVeriferAgent)
bureau.add(GoogleDirAgent)
 
if __name__ == "__main__":
    bureau.run()