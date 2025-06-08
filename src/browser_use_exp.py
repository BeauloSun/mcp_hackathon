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
        task='Go to https://www.rightmove.co.uk/, find the chepeast 1 bedroom apartment within 3 miles of Edinburgh city centre. Also let me know how much is the deposit',
        llm=llm,
        max_actions_per_step=4,
        browser_session=browser_session,
    )

    history = await agent.run(max_steps=20)
    result = history.final_result()
    with open('result.txt', 'w') as file:
        file.write(str(result))


if __name__ == '__main__':
    asyncio.run(run_search())
