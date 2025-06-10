from browser_use import Agent
from browser_use.browser import BrowserProfile, BrowserSession
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import asyncio

from mcp.server.fastmcp import FastMCP

# --------------------- Getting API key ---------------------
import os
from dotenv import load_dotenv

load_dotenv()
ninja_api = os.getenv("NINJA_API")
gemini_api = os.getenv('GEMINI_API_KEY')
gmap_api = os.getenv("GMAP_API_KEY")
openai_api = os.getenv("OPENAI_API_KEY")
# --------------------- Getting API key ---------------------

mcp = FastMCP("Demo")


@mcp.tool()
def interest_calculator(principal: float) -> str:
    """
    Calculates the simple interest payable for a given principal amount based on the current
    Bank of England base rate.

    Args:
        principal (float): The principal amount for which to calculate interest.

    Returns:
        str: A string detailing the principal, interest payable, and the annual interest rate,
             or an error message if the calculation fails.
    """
    if not ninja_api:
        return "Error: NINJA_API environment variable not set."

    api_url = 'https://api.api-ninjas.com/v1/interestrate?country=United Kingdom'
    try:
        response = requests.get(api_url, headers={'X-Api-Key': ninja_api})
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        rate = float(response.json()[
                     'central_bank_rates'][0]['rate_pct']) * 0.01
        total = round((principal * rate), 2)
        return f"For a principal of £{principal:.2f}, the interest payable is £{total:.2f} (at an annual rate of {rate*100:.2f}%)."
    except requests.exceptions.RequestException as e:
        return f"Error fetching interest rate: {e}"
    except KeyError:
        return "Error: Could not parse interest rate data from the API response."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# TODO: create shared function to retrieve interest rate


@mcp.tool()
def monthly_payment(principal: float, number_of_years: int) -> str:
    """
    Calculates the fixed monthly payment for a loan based on the principal amount,
    number of years, and the current Bank of England base rate.

    Args:
        principal (float): The total loan amount.
        number_of_years (int): The duration of the loan in years.

    Returns:
        str: The calculated monthly payment as a string, or an error message if the
             calculation fails or interest rate data cannot be fetched.
    """
    if not ninja_api:
        return "Error: NINJA_API environment variable not set."

    api_url = 'https://api.api-ninjas.com/v1/interestrate?country=United Kingdom'
    try:
        response = requests.get(api_url, headers={'X-Api-Key': ninja_api})
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        annual_rate = float(response.json()[
            'central_bank_rates'][0]['rate_pct']) * 0.01
        monthly_rate = annual_rate / 12
        num_payments = number_of_years * 12
        if monthly_rate == 0:
            return principal / num_payments
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
            ((1 + monthly_rate) ** num_payments - 1)

        return f"{monthly_payment}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching interest rate: {e}"
    except KeyError:
        return "Error: Could not parse interest rate data from the API response."
    except Exception as e:
        return f"An unexpected error occurred: {e}"


@mcp.tool()
async def search_internet(url: str, task: str) -> str:
    """
    **Navigates to a specified URL, performs web scraping based on a given task,
    and returns relevant information in a human-readable sentence(s).**

    Args:
        url (str): The complete URL (e.g., "https://www.example.com/page") to navigate to and scrape. This should be a full and valid URL.
        task (str): The task required to complete, summarized or inferenced from the original user input. To determine what is needed to be found using web search.

    Returns:
        str: A string containing the extracted information or a summary of the
             Browse outcome. This will be a human-readable sentence or paragraph.
             Returns an error message if navigation or scraping fails.
    """
    llm = ChatGoogleGenerativeAI(
        model='gemini-2.0-flash-exp', api_key=gemini_api)

    browser_session = BrowserSession(
        browser_profile=BrowserProfile(
            viewport_expansion=0,
            user_data_dir='~/.config/browseruse/profiles/default',
        )
    )

    agent = Agent(
        task=f'Go to {url}, and perform the task: {task}',
        llm=llm,
        max_actions_per_step=5,
        browser_session=browser_session,
    )
    try:
        history = await agent.run(max_steps=20)
        result = str(history.final_result())
        return f"Successfully went through {url}. Result message: {result}"
    except Exception as e:
        return f"Failed to navigate to {url}: {e}"


@mcp.tool()
def get_agency_review(name: str) -> str:
    """
    Retrieves and formats the review information for a given agency name.

    It first finds the place_id using names by google maps api and then fetches the review data using the 
    place_id. Finally, it constructs a summary of the review data in string format.

    Args:
        name (str): The name of the agency or place for which to retrieve reviews.

    Returns:
        str: A formatted string summarizing the agency's rating and review count,
             or an error message if the data cannot be found.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": name,
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address,geometry", # Request the fields you need
        "key": gmap_api,
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    data = response.json()
    place_id = None  # Initialize place_id

    if data.get("status") == "OK" and data.get("candidates"):
        # Return the first candidate's information
        place = data["candidates"][0]
        place_id = place.get("place_id")
        # {
        #     "place_id": place.get("place_id"),
        #     "name": place.get("name"),
        #     "formatted_address": place.get("formatted_address"),
        #     "geometry": place.get("geometry")
        # }
    elif data.get("status") == "ZERO_RESULTS":
        return f"Error: No agency found for '{name}'."
    else:
        error_message = data.get("error_message", "Unknown error from Google Places API.")
        return f"Error finding agency '{name}': {data.get('status')} - {error_message}"

    if not place_id:
        return f"Error: Could not retrieve place_id for '{name}'."

    url = f"https://places.googleapis.com/v1/places/{place_id}"
    # Check for available fields:
    # https://developers.google.com/maps/documentation/places/web-service/place-details
    # fields is for information of the place (NO SPACE AFTER COMMA)
    fields = "displayName,rating,userRatingCount"
    params = {
        "fields": fields,
        "key": gmap_api
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    result = response.json()
    # {'rating': 4.4, 'userRatingCount': 42, 'displayName': {'text': 'Endsleigh Court', 'languageCode': 'en'}}
    result_str = f"The rating of {result['displayName']['text']} is {result['rating']}, with {result['userRatingCount']} reviews."
    return result_str


@mcp.tool()
def calculate_stamp_duty(property_price: int, is_first_time_buyer: bool = False, is_additional_property: bool = False):
    """
    Calculates the Stamp Duty Land Tax (SDLT) for a property purchase in England or Northern Ireland.

    This function uses predefined tax bands and rates. It considers whether the buyer is a
    first-time buyer and if the property is an additional property, applying relevant
    thresholds and surcharges.

    Args:
        property_price (float): The purchase price of the property.
        is_first_time_buyer (bool, optional): True if the buyer is a first-time buyer.
                                              Defaults to False.
        is_additional_property (bool, optional): True if the property purchase will result
                                                 in owning an additional property.
                                                 Defaults to False.

    Returns:
        dict: A dictionary containing the total stamp duty, property price,
              buyer status flags, and a breakdown of the calculation by tax band.
    """
    # TODO: add logic to update this
    property_price = float(property_price)
    standard_bands = [
        (125000, 0.0),      
        (250000, 0.02),     
        (925000, 0.05),     
        (1500000, 0.10),    
        (float('inf'), 0.12)
    ]
    
    first_time_buyer_bands = [
        (300000, 0.0),     
        (500000, 0.05),     
        (925000, 0.05),     
        (1500000, 0.10),    
        (float('inf'), 0.12)
    ]
    additional_property_surcharge = 0.05
    if is_first_time_buyer and property_price <= 500000:
        bands = first_time_buyer_bands
    else:
        bands = standard_bands
    
    stamp_duty = 0
    breakdown = []
    remaining_price = property_price
    previous_threshold = 0
    
    for threshold, rate in bands:
        if remaining_price <= 0:
            break
            
        # Calculate the amount in this band
        band_amount = min(remaining_price, threshold - previous_threshold)
        band_duty = band_amount * rate
        
        # Add additional property surcharge if applicable
        if is_additional_property:
            surcharge = band_amount * additional_property_surcharge
            band_duty += surcharge
        
        stamp_duty += band_duty
        
        if band_amount > 0:
            rate_display = rate * 100
            if is_additional_property:
                rate_display += additional_property_surcharge * 100
            
            breakdown.append({
                'band': f'£{previous_threshold:,} - £{min(threshold, property_price):,}',
                'amount': band_amount,
                'rate': f'{rate_display}%',
                'duty': band_duty
            })
        
        remaining_price -= band_amount
        previous_threshold = threshold
        
        if threshold >= property_price:
            break
    
    return {
        'total_stamp_duty': round(stamp_duty, 2),
        'property_price': property_price,
        'is_first_time_buyer': is_first_time_buyer,
        'is_additional_property': is_additional_property,
        'breakdown': breakdown
    }


@mcp.tool()
def home_buying_tax_calculator_browser_use(region: str, property_type: str, day:str, month:str, year:str , purchaser_type:str, purchaser_purpose: str, more_properties:bool, replace:bool,First_time_Buyer: bool,main_residence:bool, price:int)-> str:
    """
    Uses a browser automation agent to navigate the UK government's Stamp Duty Land Tax (SDLT)
    calculator website and retrieve the total SDLT due based on provided property and
    purchaser details.

    This tool is specifically for properties in England or Northern Ireland.

    Args:
        region (str): The region of the property (e.g., "England", "Northern Ireland").
        property_type (str): Type of property (e.g., "residential", "non-residential").
        day (str): Day of the transaction.
        month (str): Month of the transaction.
        year (str): Year of the transaction.
        purchaser_type (str): Type of purchaser (e.g., "UK resident", "non-UK resident").
        purchaser_purpose (str): Purpose of purchase (e.g., "Yes" if individual, "No" if company).
        more_properties (bool): Whether the purchase results in owning two or more properties.
        replace (bool): If owning more properties, whether this replaces the main residence.
        First_time_Buyer (bool): Whether the purchaser has ever owned property before.
        main_residence (bool): If a first-time buyer, whether this will be the main residence.
        price (int): The purchase price of the property.

    Returns:
        str: The result from the browser interaction, typically the total SDLT due or an
             error message if the process fails.
    """
    if region.lower() in 'england' or region.lower() in 'northern ireland':
        url = 'https://www.tax.service.gov.uk/calculate-stamp-duty-land-tax/#!/intro'
        task = """
        Follow the below steps to use the tax calculator in the url. 
        1. Click 'Start Now'
        2. Select 'Freehold' when the page asks "Is your transaction freehold or leasehold?"
        3. Click {property_type} when the page asks "Is the transaction residential or non-residential?"
        4. When you reach the page asking for the "Effective date of your transaction":
            You are asked to provide the transaction date.
            Use the format: **{day}/{month}/{year}** (e.g. 08/06/2025)
            Then fill:
            - Day → {day}
            - Month → {month}
            - Year → {year}

        5. Proceed based on the {property_type}:
            5.1 IF {property_type} IS 'residential':
                You will be asked:
                **"Are any of the purchasers non-UK resident?"** → Select {purchaser_type}
            5.2 IF {property_type} IS 'non-residential':
                → Skip to **Step 10**
        6. When you reach the page asking for the "Are you purchasing the property as an individual?" → Select {purchaser_purpose}
        7.Proceed based on the {purchaser_purpose}:
            7.1 IF {purchaser_purpose} IS 'Yes':
                You will be asked:
                **"Will the purchase of the property result in owning two or more properties?"** → Select {more_properties}
            7.2 IF {purchaser_purpose} IS 'NO':
                → Skip to **Step 10**
        8.Proceed based on the {more_properties}:
            8.1 IF {more_properties} IS 'Yes':
                You will be asked in same page:
                **"Is the property being purchased replacing your main residence?"** → Select {replace}
                → Skip to **Step 10**
            8.2 IF {more_properties} IS 'NO':
                You will be asked:
                **"Have you ever owned or part owned another property?"** → Select {First_time_Buyer}
        9.Proceed based on the {First_time_Buyer}:
            9.1 IF {First_time_Buyer} IS 'Yes':
                → Skip to **Step 10**
            9.2 IF {First_time_Buyer}IS 'NO':
                You will be asked:
                **"Will this property be your main residence?"** → Select {main_residence}
        10. You will be asked to **directly enter the purchase price**, enter the {price}.

        At every step:
        - Carefully read the question.
        - Make the appropriate choice or enter the required value.
        - Then click **'Continue'** to proceed.

        Final step:

        1. After entering the purchase price (`{price}`), click **'Continue'**.
        2. You will be taken to a page titled **"Check your answers"**.
        3. On that page, click the button labeled **"Calculate your SDLT"**.
        4. Once the result page loads, look for the field labeled **"Total SDLT due (£)"** — this is the final tax amount.
        Extract that value as the result.
        """
        result = asyncio.run(search_internet(url, task))
        return result


def start_mcp_server():
    try:
        mcp.run()
        return "MCP Server 'Demo' started successfully. Check your console for details if any."
    except Exception as e:
        return f"Error starting MCP Server: {e}"
