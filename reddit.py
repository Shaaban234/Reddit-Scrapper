import logging
import os
import random
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

from urllib.parse import urlparse, unquote
import time

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

df = pd.read_csv('emails.csv')
emails_list = df['Email'].tolist()

# List of proxies
proxies = [
  '169.197.83.75:14365:cu3it:e41nwtvz'
]



# Global event to stop the upvote process
stop_event = asyncio.Event()

def extract_post_info(post_url):
    # Parse the URL
    parsed_url = urlparse(post_url)
    
    # Split the path to get the subreddit and post ID
    path_parts = parsed_url.path.split('/')
    
    # Extract the subreddit, post ID, and post title
    subreddit = path_parts[2]
    post_id = path_parts[4]
    post_title = path_parts[5].replace('_', ' ')
    
    return subreddit, post_id, unquote(post_title)

async def process_upvotes(num_upvotes, upvotes_per_hour, link):
    global stop_event
    global emails_list

    emails_list = emails_list[:num_upvotes]
    async with async_playwright() as p:
        for i in range(len(emails_list)):
            if stop_event.is_set():
                logger.info('Upvote process stopped.')
                break

            proxy_str = random.choice(proxies)
            proxy_parts = proxy_str.split(':')
            proxy = {
                "server": f"http://{proxy_parts[0]}:{proxy_parts[1]}",
                "username": proxy_parts[2],
                "password": proxy_parts[3]
            }

     
            logger.info(f'Starting upvote process for email {i+1}/{num_upvotes}: {emails_list[i]}')
            browser = await p.chromium.launch(headless=True, proxy={"server": proxy["server"], "username": proxy["username"], "password": proxy["password"]} ,args=[
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36','--no-sandbox', '--disable-setuid-sandbox','--disable-extensions'
        ])
            context = await browser.new_context(ignore_https_errors=True,viewport={'width': 1280, 'height': 800},no_viewport=True)
            page = await context.new_page()
            await stealth_async(page)   # Ap
            try:
                if stop_event.is_set():
                    logger.info('Upvote process stopped.')
                    break

                # Navigate to login page
                logger.debug(f'Navigating to login page with {emails_list[i]}')
                await page.goto('https://www.reddit.com/r/AmIHotSFW/comments/1esslxm/im_65_am_i_hot_f19/')
                await page.wait_for_timeout(20000)
                
                # # Take a screenshot
                # await page.screenshot(path=f'login_page_{i+1}.png')
                
                # Click login button
                login_button = page.locator('a#login-button')
                await login_button.click()
                await page.wait_for_timeout(10000)
                
                # # Take a screenshot
                # await page.screenshot(path=f'screenshots/login_click_{i+1}.png')
                
                if stop_event.is_set():
                    logger.info('Upvote process stopped.')
                    break

                # Fill in login details
                await page.fill('input[name="username"]', 'qihufa@teleg.eu')
                await page.fill('input[name="password"]', 'Fuckoff-1')
                login_button = page.locator('button:has-text("Log In")')

                if stop_event.is_set():
                    logger.info('Upvote process stopped.')
                    break

                if login_button:
                    await login_button.click()
                    await page.wait_for_timeout(10000)  # Adjust timeout as needed
                    
                    # Take a screenshot
                    await page.screenshot(path=f'screenshots/login_success_{i+1}.png')
                    logger.info(f'Logged in successfully with {emails_list[i]}')
                else:
                    logger.error(f'Login button not found for {emails_list[i]}')
                    continue

                if stop_event.is_set():
                    logger.info('Upvote process stopped.')
                    break
                age_confirmation_button = await page.query_selector('span:has-text("Yes, I\'m over 18")')
                if age_confirmation_button:
                    logger.info('Age confirmation button found. Clicking...')
                    await age_confirmation_button.click()
                    await page.wait_for_timeout(5000)
                # Handle the "View NSFW content" button
                nsfw_button = await page.query_selector('span:has-text("View NSFW content")')
                if nsfw_button:
                    logger.info('NSFW content button found. Clicking...')
                    await nsfw_button.click()
                    await page.wait_for_timeout(5000)  # Adjust timeout as needed

                
                if stop_event.is_set():
                    logger.info('Upvote process stopped.')
                    break

                logger.debug(f'Navigating to post page with {emails_list[i]}')
                await page.wait_for_timeout(35000)
                upvote_buttons = page.locator('button[upvote]')
                # await page.wait_for_selector('shreddit-overlay-display', state='hidden', timeout=30000)
                # await upvote_buttons.first.wait_for(state='visible')
                 
                button_count = await upvote_buttons.count()
                logger.debug(f'Number of upvote buttons found: {button_count}')
                
                # # # Optionally take a screenshot to verify
                # await page.screenshot(path=f'screenshots/available_buttons_{i+1}.png')
                if button_count > 0:
                    logger.info("this IF Worked")

                    upvote_button = upvote_buttons.nth(0)
                    # await page.evaluate('arguments[0].click()', upvote_button)  # Select the first button
                    await upvote_button.click()
                    await page.wait_for_timeout(1000)
                
            except Exception as e:
                logger.error(f'An error occurred for {emails_list[i]}: {e}')
            finally:
                await context.close()
                await browser.close()

            await asyncio.sleep(0.1)

            # Check for stop event after each iteration
            if stop_event.is_set():
                logger.info('Upvote process stopped.')
                break

            logger.debug(f'Progress updated: {i + 1}/{num_upvotes}')

            if i + 1 < len(emails_list):
                await asyncio.sleep(3600 / upvotes_per_hour)  # Control upvote rate

        if not stop_event.is_set():
            logger.info('Upvote process completed for all emails')

    stop_event.clear()

# Main function to start the upvote process
async def main():
    num_upvotes = 100  # Set the number of upvotes you want
    upvotes_per_hour = 30  # Set the rate of upvotes per hour
    link = 'https://www.reddit.com/r/AmIHotSFW/comments/1esslxm/im_65_am_i_hot_f19/'  # Set the link to the post you want to upvote

    await process_upvotes(num_upvotes, upvotes_per_hour, link)

if __name__ == '__main__':
    asyncio.run(main())
