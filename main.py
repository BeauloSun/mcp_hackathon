import gradio as gr
from src.mcp import start_mcp_server, interest_calculator, monthly_payment


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

    with gr.Tab("Monthly Payment Calculator"):
        gr.Markdown(
            "This tool calculates the monthly payment based on a principal amount and number of years, using current UK central bank rates.")
        principal_input = gr.Number(
            label="Principal Amount (£)", value=100000.00)
        years = gr.Number(
            label="Number of Years", value=10)
        calculate_interest_btn = gr.Button("Calculate Payment")
        interest_output = gr.Textbox(
            label="Calculated Payment", interactive=False)
        calculate_interest_btn.click(
            monthly_payment,
            inputs=(principal_input, years),
            outputs=interest_output
        )

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch(mcp_server=True)
