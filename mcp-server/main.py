import gradio as gr
import requests

from mcp.server.fastmcp import FastMCP

# --------------------- Getting API key ---------------------
import os
from dotenv import load_dotenv

load_dotenv()
ninja_api = os.getenv("NINJA_API")
# --------------------- Getting API key ---------------------

mcp = FastMCP("Demo")

# A random tool to calculate how much interest you need to pay (for experiment)


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

# --- Gradio UI Functions ---


def start_mcp_server():
    try:
        mcp.run()
        return "MCP Server 'Demo' started successfully. Check your console for details if any."
    except Exception as e:
        return f"Error starting MCP Server: {e}"

# --- Gradio Interface ---


with gr.Blocks() as demo:
    gr.Markdown("# MCP Server Host")
    gr.Markdown("---")

    with gr.Tab("MCP Server Control"):
        gr.Markdown("## Start your FastMCP Server")
        server_status_output = gr.Textbox(
            label="Server Status", interactive=False)
        start_server_btn = gr.Button("Start MCP Server")
        start_server_btn.click(start_mcp_server, outputs=server_status_output)

    with gr.Tab("Interest Calculator Tool"):
        gr.Markdown("## Calculate Interest")
        gr.Markdown(
            "This tool calculates the interest payable based on a principal amount, using current UK central bank rates.")
        principal_input = gr.Number(
            label="Principal Amount (£)", value=1000.00)
        calculate_interest_btn = gr.Button("Calculate Interest")
        interest_output = gr.Textbox(
            label="Calculated Interest", interactive=False)
        calculate_interest_btn.click(
            interest_calculator,
            inputs=principal_input,
            outputs=interest_output
        )

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch()
