import telebot
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
from telebot.async_telebot import AsyncTeleBot
import json
from collections import defaultdict

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = '7939741557:AAHGEDG8NVbVJCXp7vGXjjgKIfY_IIfNgXY'
bot = AsyncTeleBot(TOKEN)
# Store uploaded files information
user_files = defaultdict(dict)

# Create a thread pool for handling multiple requests
thread_pool = ThreadPoolExecutor(max_workers=100)

async def fetch_api_data(session, url):
    async with session.get(url) as response:
        try:
            return await response.json()
        except aiohttp.ContentTypeError:
            # Return a default error response if JSON decoding fails
            return {"error": "Invalid response"}

async def process_bin(bin_number):
    async with aiohttp.ClientSession() as session:
        bin_url = f"https://omdev.pro/bin.php?Bin={bin_number}"
        vbv_url = f"https://omdev.pro/vbv.php?Bin={bin_number}"
        
        bin_data, vbv_data = await asyncio.gather(
            fetch_api_data(session, bin_url),
            fetch_api_data(session, vbv_url)
        )
        
        # If vbv_data contains an error, replace it with a default error response
        if "error" in vbv_data:
            vbv_data = {
                "Vbv Status": "ERROR",
                "Vbv Response": "ERROR"
            }
        
        return bin_data, vbv_data

def format_response(bin_data, vbv_data):
    bin_info = f"""[⌥] 𝐁𝐈𝐍 𝐥𝐨𝐨𝐤𝐮𝐩 𝐀𝐩𝐢
━━━━━━━━━━━━━━━━━
[⌬] 𝐁𝐈𝐍 ⇢ {bin_data.get('BIN', 'N/A')}
[⌬] 𝐈𝐧𝐟𝐨 ⇢ {bin_data.get('Brand', 'N/A')}-{bin_data.get('Credit/Debit', 'N/A')}-{bin_data.get('Card Type', 'N/A')}
[⌬] 𝐈𝐬𝐬𝐮𝐞𝐫 ⇢ {bin_data.get('Issuer', 'N/A')}
[⌬] 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇢ {bin_data.get('Country Name', 'N/A')}
━━━━━━━━━━━━━━━━━"""

    vbv_info = f"""Vbv Status: {vbv_data.get('Vbv Status', 'ERROR')}
Vbv Response: {vbv_data.get('Vbv Response', 'ERROR')}"""

    return f"{bin_info}\n{vbv_info}"

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    await bot.reply_to(message, "Welcome! Send me a 6-digit BIN number or a text file containing multiple BIN numbers.")

@bot.message_handler(commands=['bin'])
async def check_single_bin(message):
    if message.reply_to_message and message.reply_to_message.document:
        await check_file_bins(message)
    else:
        bin_number = message.text.split()[1] if len(message.text.split()) > 1 else None
        if bin_number and len(bin_number) == 6 and bin_number.isdigit():
            bin_data, vbv_data = await process_bin(bin_number)
            response = format_response(bin_data, vbv_data)
            await bot.reply_to(message, response)
        else:
            await bot.reply_to(message, "Please provide a valid 6-digit BIN number or reply to a file with /bin.")

@bot.message_handler(content_types=['document'])
async def handle_document(message):
    try:
        file_info = await bot.get_file(message.document.file_id)
        user_files[message.chat.id][message.message_id] = file_info
        await bot.reply_to(message, "File received. Reply to this message with /bin to start checking the BINs.")
    except Exception as e:
        await bot.reply_to(message, f"An error occurred while processing the file: {str(e)}")

@bot.message_handler(func=lambda message: message.text.startswith(('.bin', '!bin')))
async def check_single_bin_alt(message):
    bin_number = message.text.split()[1] if len(message.text.split()) > 1 else None
    if bin_number and len(bin_number) == 6 and bin_number.isdigit():
        bin_data, vbv_data = await process_bin(bin_number)
        response = format_response(bin_data, vbv_data)
        await bot.reply_to(message, response)
    else:
        await bot.reply_to(message, "Please provide a valid 6-digit BIN number.")

@bot.message_handler(func=lambda message: message.text == '/bin' and message.reply_to_message and message.reply_to_message.document)
async def check_file_bins(message):
    try:
        reply_to_message = message.reply_to_message
        file_info = user_files[message.chat.id].get(reply_to_message.message_id)
        
        if not file_info:
            await bot.reply_to(message, "Sorry, I couldn't find the file information. Please upload the file again.")
            return

        downloaded_file = await bot.download_file(file_info.file_path)
        bin_numbers = downloaded_file.decode('utf-8').splitlines()
        
        await bot.reply_to(message, f"Starting to check {len(bin_numbers)} BINs. This may take a while...")

        async def process_and_send(bin_number):
            if len(bin_number) == 6 and bin_number.isdigit():
                bin_data, vbv_data = await process_bin(bin_number)
                response = format_response(bin_data, vbv_data)
                await bot.send_message(message.chat.id, response)
            else:
                await bot.send_message(message.chat.id, f"Invalid BIN: {bin_number}")
        
        tasks = [asyncio.create_task(process_and_send(bin)) for bin in bin_numbers]
        await asyncio.gather(*tasks)
        
        await bot.send_message(message.chat.id, "Finished checking all BINs.")
        
        # Clean up the stored file information
        del user_files[message.chat.id][reply_to_message.message_id]
        
    except Exception as e:
        await bot.reply_to(message, f"An error occurred while checking the BINs: {str(e)}")

async def main():
    await bot.polling(non_stop=True, timeout=60)

if __name__ == '__main__':
    asyncio.run(main())

