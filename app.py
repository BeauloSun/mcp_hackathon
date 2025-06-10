import gradio as gr
import asyncio
import json
import threading
from typing import Dict, Any, List, Optional
from src.mcp import mcp # start_mcp_server removed as it's no longer directly called

from dotenv import load_dotenv
load_dotenv()

# Global list to store tools
mcp_tools_list = []

def _run_async_global(coro):
    """Helper to run async functions in sync context"""
    try:
        # Try to get the current loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No loop exists, create a new one
        return asyncio.run(coro)

def load_and_normalize_tools():
    """Load tools from MCP, normalize schema, and store in mcp_tools_list."""
    global mcp_tools_list
    try:
        raw_tools = _run_async_global(mcp.list_tools())
        current_tools = [] # Temporary list for this load operation
        for tool in raw_tools:
            if hasattr(tool, 'inputSchema') and tool.inputSchema and 'properties' in tool.inputSchema:
                for param_name, param_schema in tool.inputSchema['properties'].items():
                    if isinstance(param_schema, dict) and 'type' in param_schema and isinstance(param_schema['type'], str):
                        param_schema['type'] = param_schema['type'].lower()
            current_tools.append(tool)
        
        mcp_tools_list = current_tools # Assign to global list
        print(f"Loaded and normalized {len(mcp_tools_list)} tools:")
        for tool_item in mcp_tools_list:
            print(f"  - {tool_item.name}: {tool_item.description[:100] if tool_item.description else 'No description'}...")
    except Exception as e:
        print(f"Error loading tools: {e}")
        mcp_tools_list = []

def get_tool_names_global() -> List[str]:
    """Get list of tool names for dropdown from mcp_tools_list"""
    return [tool.name.replace('_', ' ').title() for tool in mcp_tools_list]

def get_tool_by_display_name_global(display_name: str):
    """Get tool object by display name from mcp_tools_list"""
    tool_name = display_name.lower().replace(' ', '_')
    for tool in mcp_tools_list:
        if tool.name == tool_name:
            return tool
    return None

def call_mcp_tool_sync_global(tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Call MCP tool synchronously with error handling"""
    try:
        print(f"Calling tool {tool_name} with args: {tool_args}")
        result = _run_async_global(mcp.call_tool(tool_name, tool_args))
        print(f"Tool result: {result}")
        return {"success": True, "result": result}
    except Exception as e:
        error_msg = f"Error calling tool {tool_name}: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}

# Load tools at startup
load_and_normalize_tools()

def update_tool_interface(selected_tool_name: str):
    """Update the interface when a new tool is selected"""
    if not selected_tool_name or not mcp_tools_list:
        # Return updates to hide all components (12 textboxes + 12 radios)
        updates = [gr.update(visible=False) for _ in range(24)]
        updates.append(gr.update(value="Select a tool to see its description"))  # Description
        updates.append(gr.update(visible=False))  # Run button
        return updates
    
    tool = get_tool_by_display_name_global(selected_tool_name)
    if not tool:
        # Return updates to hide all components (12 textboxes + 12 radios)
        updates = [gr.update(visible=False) for _ in range(24)]
        updates.append(gr.update(value="Tool not found"))
        updates.append(gr.update(visible=False))
        return updates
    
    # Get input schema
    input_schema = tool.inputSchema or {}
    properties = input_schema.get('properties', {})
    required_fields = input_schema.get('required', [])
    
    textbox_updates = []
    radio_updates = []
    param_names = list(properties.keys())
    
    # Update up to 12 input components (textboxes and radios)
    for i in range(12):
        if i < len(param_names):
            param_name = param_names[i]
            param_schema = properties[param_name]
            is_required = param_name in required_fields
            
            param_title = param_schema.get('title', param_name.replace('_', ' ').title())
            if is_required:
                param_title += " *"
            
            param_description = param_schema.get('description', '')
            label = param_title
            if param_description:
                label += f" - {param_description}"
            
            param_type = param_schema.get('type', 'string')
            param_default = param_schema.get('default')
            
            if param_type == 'boolean' or param_type == 'bool':
                textbox_updates.append(gr.update(visible=False)) # Hide textbox
                radio_updates.append(gr.update(
                    visible=True,
                    label=label,
                    choices=["True", "False"],
                    value=str(param_default) if param_default is not None else "False"
                ))
            elif param_type in ['integer', 'number']:
                textbox_updates.append(gr.update(
                    visible=True,
                    label=label,
                    value=param_default if param_default is not None else (0 if param_type == 'integer' else 0.0)
                ))
                radio_updates.append(gr.update(visible=False)) # Hide radio
            else:  # string, array, object
                placeholder = ""
                if param_type == 'array':
                    placeholder = "item1, item2, item3"
                elif param_type == 'object':
                    placeholder = '{"key": "value"}'
                
                textbox_updates.append(gr.update(
                    visible=True,
                    label=label,
                    value=param_default if param_default else "",
                    placeholder=placeholder
                ))
                radio_updates.append(gr.update(visible=False)) # Hide radio
        else: # No parameter for this slot
            textbox_updates.append(gr.update(visible=False))
            radio_updates.append(gr.update(visible=False))
            
    updates = textbox_updates + radio_updates
    
    # Update description and run button
    description = tool.description if tool.description else "No description available"
    updates.append(gr.update(value=description))
    updates.append(gr.update(visible=True, value=f"▶️ Run {selected_tool_name}"))
    
    return updates

def run_selected_tool(selected_tool_name: str, *args):
    """Run the selected tool with provided arguments"""
    if not selected_tool_name:
        return {"error": "No tool selected"}
    
    tool = get_tool_by_display_name_global(selected_tool_name)
    if not tool:
        return {"error": f"Tool '{selected_tool_name}' not found"}
    
    try:
        # Get input schema
        input_schema = tool.inputSchema or {}
        properties = input_schema.get('properties', {})
        param_names = list(properties.keys())
        
        tool_args = {}
        num_text_inputs = 12  # Number of textbox components

        for i, param_name in enumerate(param_names):
            if i >= 12: # UI supports max 12 parameters
                break

            param_schema = properties[param_name]
            param_type = param_schema.get('type', 'string')
            
            arg_value_from_ui = None
            if param_type == 'boolean' or param_type == 'bool':
                # Boolean value comes from the i-th radio button, which is after all textboxes in *args
                arg_value_from_ui = args[num_text_inputs + i] 
            else:
                # Other types come from the i-th textbox
                arg_value_from_ui = args[i]

            # Skip empty arguments for optional parameters (not applicable to radio buttons which always have a value)
            is_optional_and_empty = (
                param_type != 'boolean' and
                not str(arg_value_from_ui).strip() and
                param_name not in input_schema.get('required', [])
            )
            if is_optional_and_empty:
                continue
            
            # Convert based on type
            try:
                if param_type == 'boolean' or param_type == 'bool':
                    # Value from gr.Radio is "True" or "False" string
                    tool_args[param_name] = (str(arg_value_from_ui) == "True")
                elif param_type == 'integer':
                    tool_args[param_name] = int(float(str(arg_value_from_ui))) if str(arg_value_from_ui).strip() else 0
                elif param_type == 'number':
                    tool_args[param_name] = float(str(arg_value_from_ui)) if str(arg_value_from_ui).strip() else 0.0
                elif param_type == 'array' and isinstance(arg_value_from_ui, str):
                    tool_args[param_name] = [item.strip() for item in arg_value_from_ui.split(',')] if arg_value_from_ui.strip() else []
                elif param_type == 'object' and isinstance(arg_value_from_ui, str):
                    tool_args[param_name] = json.loads(arg_value_from_ui) if arg_value_from_ui.strip() else {}
                else: # string
                    tool_args[param_name] = str(arg_value_from_ui)
            except (ValueError, json.JSONDecodeError) as e:
                return {"error": f"Invalid value for parameter '{param_name}': {str(e)}"}
        
        # Call the tool
        result = call_mcp_tool_sync_global(tool.name, tool_args)
        return result
        
    except Exception as e:
        return {"error": f"Error executing tool: {str(e)}"}

# Create Gradio interface
with gr.Blocks(title="MCP Tool Interface", theme=gr.themes.Monochrome()) as demo:
    gr.Markdown("# 🚀 MCP Tool Interface")
    gr.Markdown("Select and run your MCP tools with a dynamic interface")
    
    with gr.Tab("🔨 Tools"):
        gr.Markdown("## Available Tools")
        
        if not mcp_tools_list:
            gr.Markdown("⚠️ **No tools found!** Make sure your MCP server is running and tools are registered.")
        else:
            # Tool selector
            tool_dropdown = gr.Dropdown(
                choices=get_tool_names_global(),
                label="Select Tool",
                value=get_tool_names_global()[0] if get_tool_names_global() else None,
                interactive=True
            )
            
            # Tool description
            tool_description = gr.Textbox(
                label="Description",
                interactive=False,
                lines=3,
                value="Select a tool to see its description"
            )
            
            gr.Markdown("### Parameters")
            
            input_text_components = []
            input_radio_components = []

            for i in range(12):
                # Textbox for general inputs
                comp_text = gr.Textbox(label=f"Parameter {i+1}", visible=False)
                input_text_components.append(comp_text)
                
                # Radio for boolean inputs
                comp_radio = gr.Radio(
                    label=f"Parameter {i+1}", # Label will be updated by update_tool_interface
                    choices=["True", "False"], 
                    visible=False
                )
                input_radio_components.append(comp_radio)
            
            # Run button and output
            run_button = gr.Button("▶️ Run Tool", variant="primary", visible=False)
            output_json = gr.JSON(label="Tool Output")
            
            # Event handlers
            tool_dropdown.change(
                update_tool_interface,
                inputs=[tool_dropdown],
                outputs=input_text_components + input_radio_components + [tool_description, run_button]
            )
            
            run_button.click(
                run_selected_tool,
                inputs=[tool_dropdown] + input_text_components + input_radio_components,
                outputs=[output_json]
            )
    
    with gr.Tab("📚 Documentation"):
        gr.Markdown("## MCP Tools Documentation")
        
        if mcp_tools_list:
            for tool in mcp_tools_list:
                with gr.Accordion(f"📖 {tool.name.replace('_', ' ').title()}", open=False):
                    gr.Markdown(f"**Name:** `{tool.name}`")
                    
                    if tool.description:
                        gr.Markdown(f"**Description:** {tool.description}")
                    
                    # Parameters documentation
                    input_schema = tool.inputSchema or {}
                    properties = input_schema.get('properties', {})
                    required_fields = input_schema.get('required', [])
                    
                    if properties:
                        gr.Markdown("**Parameters:**")
                        param_docs = []
                        for param_name, param_schema in properties.items():
                            param_type = param_schema.get('type', 'string')
                            is_required = "✅ Required" if param_name in required_fields else "⚪ Optional"
                            param_desc = param_schema.get('description', 'No description')
                            default_val = param_schema.get('default')
                            default_text = f" (default: {default_val})" if default_val is not None else ""
                            param_docs.append(f"- **{param_name}** ({param_type}) - {is_required}{default_text}\n  {param_desc}")
                        
                        gr.Markdown("\n".join(param_docs))
                    else:
                        gr.Markdown("*No parameters required*")
                    
                    # Example usage
                    if properties:
                        gr.Markdown("**Example JSON:**")
                        example = {}
                        for param_name, param_schema in properties.items():
                            param_type = param_schema.get('type', 'string')
                            if param_type == 'string':
                                example[param_name] = "example_value"
                            elif param_type == 'number':
                                example[param_name] = 123.45
                            elif param_type == 'integer':
                                example[param_name] = 123
                            elif param_type == 'boolean':
                                example[param_name] = True
                            elif param_type == 'array':
                                example[param_name] = ["item1", "item2"]
                            elif param_type == 'object':
                                example[param_name] = {"key": "value"}
                        
                        gr.Code(json.dumps(example, indent=2), language="json")
        else:
            gr.Markdown("No tools available. Make sure your MCP server is running and tools are registered.")

if __name__ == "__main__":
    # Gradio will handle starting the MCP server with mcp_server=True
    print("Launching MCP Tool Interface…")
    print(f"Available tools: {ui.get_tool_names()}") # Ensure ui is used here
    demo.launch(
        share=False,
        show_error=True,
        inbrowser=True,
        mcp_server=True # Changed to True
    )
