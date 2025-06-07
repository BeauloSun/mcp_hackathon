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
# --------------------- Getting API key ---------------------

mcp = FastMCP("Demo")


@mcp.tool()
def interest_calculator(principal: float) -> str:
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
def browse_internet() -> str:
    # TBC........

    return True


@mcp.tool()
def search_internet(url: str, task: str) -> str:
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

    async def run_Browse_task():
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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run_Browse_task())
    loop.close()
    return result


def start_mcp_server():
    try:
        mcp.run()
        return "MCP Server 'Demo' started successfully. Check your console for details if any."
    except Exception as e:
        return f"Error starting MCP Server: {e}"
