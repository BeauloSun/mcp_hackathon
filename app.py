import gradio as gr
from src.mcp import (
    start_mcp_server, 
    interest_calculator, 
    monthly_payment, 
    search_internet,
    get_agency_review,
    calculate_stamp_duty,
    home_buying_tax_calculator_browser_use
)


with gr.Blocks() as demo:
    gr.Markdown("# MCP Server Host")
    gr.Markdown("---")

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

    with gr.Tab("Use Browser"):
        gr.Markdown(
            "This tool requires two inputs: url and task. Given both parameters, it can perform web scraping and return the related information in a human readable sentence(s)")
        website_url = gr.Textbox(
            label="URL (e.g.: https://www.google.com)", value='https://www.google.com', interactive=True)
        task = gr.Textbox(
            label="Task (e.g.: Find out how old is Donald Trump)", value='Find out how old is Donald Trump',  interactive=True)
        browser_use_btn = gr.Button("Start browsing")
        search_output = gr.Textbox(
            label="Search Output", interactive=False)
        browser_use_btn.click(
            search_internet,
            inputs=(website_url, task),
            outputs=search_output
        )

    with gr.Tab("Get Agency Review"):
        gr.Markdown("## Get Agency Review")
        gr.Markdown(
            "Retrieves and formats the review information for a given agency name. "
            "It first finds the place_id using names by Google Maps API and then fetches the review data using the "
            "place_id. Finally, it constructs a summary of the review data in string format."
        )
        agency_name_input = gr.Textbox(label="Agency Name", placeholder="e.g., Google London")
        get_review_btn = gr.Button("Get Review")
        review_output = gr.Textbox(label="Agency Review", interactive=False)
        get_review_btn.click(
            get_agency_review,
            inputs=agency_name_input,
            outputs=review_output
        )

    with gr.Tab("Calculate Stamp Duty"):
        gr.Markdown("## Calculate Stamp Duty Land Tax (SDLT)")
        gr.Markdown(
            "Calculates the Stamp Duty Land Tax (SDLT) for a property purchase in England or Northern Ireland. "
            "This function uses predefined tax bands and rates. It considers whether the buyer is a "
            "first-time buyer and if the property is an additional property, applying relevant "
            "thresholds and surcharges."
        )
        property_price_input_sd = gr.Number(label="Property Price (£)", value=300000)
        is_first_time_buyer_checkbox = gr.Checkbox(label="Is First-Time Buyer?", value=False)
        is_additional_property_checkbox = gr.Checkbox(label="Is Additional Property?", value=False)
        calculate_sd_btn = gr.Button("Calculate Stamp Duty")
        stamp_duty_output = gr.JSON(label="Stamp Duty Calculation") # Output is a dict
        calculate_sd_btn.click(
            calculate_stamp_duty,
            inputs=[property_price_input_sd, is_first_time_buyer_checkbox, is_additional_property_checkbox],
            outputs=stamp_duty_output
        )

    with gr.Tab("Home Buying Tax Calculator (Browser Use)"):
        gr.Markdown("## Home Buying Tax Calculator (via UK Gov Website)")
        gr.Markdown(
            "Uses a browser automation agent to navigate the UK government's Stamp Duty Land Tax (SDLT) "
            "calculator website and retrieve the total SDLT due based on provided property and "
            "purchaser details. This tool is specifically for properties in England or Northern Ireland."
        )
        hbt_region = gr.Textbox(label="Region (England or Northern Ireland)")
        hbt_property_type = gr.Textbox(label="Property Type (residential or non-residential)")
        hbt_day = gr.Textbox(label="Day of Transaction (DD)")
        hbt_month = gr.Textbox(label="Month of Transaction (MM)")
        hbt_year = gr.Textbox(label="Year of Transaction (YYYY)")
        hbt_purchaser_type = gr.Textbox(label="Purchaser Type (UK resident or non-UK resident)") # "Are any of the purchasers non-UK resident?" -> No = UK resident
        hbt_purchaser_purpose = gr.Textbox(label="Purchasing as Individual? (Yes or No)")
        hbt_more_properties = gr.Checkbox(label="Will own two or more properties after purchase?")
        hbt_replace_main_residence = gr.Checkbox(label="Replacing main residence (if owning more properties)?")
        hbt_first_time_buyer = gr.Checkbox(label="Ever owned property before? (No = First Time Buyer)") # "Have you ever owned or part owned another property?" -> No = FTB
        hbt_main_residence = gr.Checkbox(label="Will this be main residence (if first-time buyer)?")
        hbt_price = gr.Number(label="Property Purchase Price (£)")
        
        run_hbt_calc_btn = gr.Button("Run Tax Calculator via Browser")
        hbt_output = gr.Textbox(label="Tax Calculator Result")
        
        run_hbt_calc_btn.click(
            home_buying_tax_calculator_browser_use,
            inputs=[
                hbt_region, 
                hbt_property_type, 
                hbt_day, 
                hbt_month, 
                hbt_year, 
                hbt_purchaser_type, 
                hbt_purchaser_purpose, 
                hbt_more_properties, 
                hbt_replace_main_residence, 
                hbt_first_time_buyer, 
                hbt_main_residence, 
                hbt_price
            ],
            outputs=hbt_output
        )

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch(mcp_server=True)
