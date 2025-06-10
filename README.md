---
title: Uk Property Mcp
emoji: 📊
colorFrom: purple
colorTo: purple
sdk: gradio
sdk_version: 5.33.1
python_version: 3.12
app_file: app.py
pinned: false
license: apache-2.0
short_description: MCP server for help in looking for an apartment in the UK
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
# To-do (both)

1. Area measurement based on image :blush:
2. Distance calculation given user's location input :blush:
3. Browser-use tool integration / fancy feature exploration :heart_eyes:
4. Crime analysis
5. Agency information
6. Local amenities (supermarket, hospitals, parks, gyms, schools, parking etc.)

# To-do (renting)

1. Deposit (expected return given years of rent)
2. Agency rating and review :heart_eyes:

# To-do (buying)

1. Tax calculator (first time, stamp-duty, house price) :heart_eyes:
2. Maintenance estimation

# How to run

1. uv sync
2. uv run main.py

# For browser-use package:

uv pip install browser-use

uv run python -m playwright install

# Exploration

1. https://github.com/tadata-org/fastapi_mcp

2. https://zapier.com/mcp

3. https://apify.com/store/categories