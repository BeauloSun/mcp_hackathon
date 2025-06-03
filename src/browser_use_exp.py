from browser_use.browser import BrowserProfile, BrowserSession
from browser_use import Agent
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))


load_dotenv()


api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError('GOOGLE_API_KEY is not set')

llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-exp', api_key=SecretStr(api_key))

browser_session = BrowserSession(
    browser_profile=BrowserProfile(
        viewport_expansion=0,
        user_data_dir='~/.config/browseruse/profiles/default',
    )
)


async def run_search():
    agent = Agent(
        task='Go to https://www.rightmove.co.uk/, search for all properties for rent within 3 miles radius of Edinburgh, give me the cheapest rent for 1b apartment.',
        llm=llm,
        max_actions_per_step=4,
        browser_session=browser_session,
    )

    await agent.run(max_steps=30)


if __name__ == '__main__':
    asyncio.run(run_search())
