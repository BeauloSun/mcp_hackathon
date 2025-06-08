import inspect
import gradio as gr
import asyncio
from src.mcp import mcp, start_mcp_server

tools = asyncio.run(mcp.list_tools())


with gr.Blocks() as demo:
    gr.Markdown("# MCP Server Host")
    gr.Markdown("---")

    with gr.Tab("MCP Server Control"):
        gr.Markdown("## Start your FastMCP Server")
        server_status_output = gr.Textbox(label="Server Status", interactive=False)
        start_server_btn = gr.Button("Start MCP Server")
        start_server_btn.click(start_mcp_server, outputs=server_status_output)

    # Dynamically create tabs for each registered tool
    for tool_name, tool_fn in tools:
        with gr.Tab(tool_name.replace('_', ' ').title()):
            gr.Markdown(f"## {tool_name.replace('_', ' ').title()}")
            sig = inspect.signature(tool_fn)
            input_components = []
            for param in sig.parameters.values():
                if param.annotation in (bool,) or param.name.startswith('is_'):
                    comp = gr.Checkbox(label=param.name.replace('_', ' ').title())
                elif param.annotation in (int, float):
                    comp = gr.Number(label=param.name.replace('_', ' ').title())
                else:
                    comp = gr.Textbox(label=param.name.replace('_', ' ').title())
                input_components.append(comp)
            ret_ann = sig.return_annotation
            if ret_ann is dict:
                output_component = gr.JSON(label=f"{tool_name.replace('_', ' ').title()} Output")
            else:
                output_component = gr.Textbox(label=f"{tool_name.replace('_', ' ').title()} Output", interactive=False)
            run_btn = gr.Button(f"Run {tool_name.replace('_', ' ').title()}")
            run_btn.click(tool_fn, inputs=input_components, outputs=output_component)

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch(mcp_server=True)
