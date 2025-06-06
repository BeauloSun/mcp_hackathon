import requests

from mcp.server.fastmcp import FastMCP

# --------------------- Getting API key ---------------------
import os
from dotenv import load_dotenv

load_dotenv()
ninja_api = os.getenv("NINJA_API")
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
def browse_internet(principal: float, number_of_years: int) -> str:
    # TBC........
    return True


def start_mcp_server():
    try:
        mcp.run()
        return "MCP Server 'Demo' started successfully. Check your console for details if any."
    except Exception as e:
        return f"Error starting MCP Server: {e}"
