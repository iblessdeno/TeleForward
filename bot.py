import asyncio
import sys
import nest_asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from io import BytesIO
from credentials import API_ID, API_HASH, SOURCE_CHANNEL_IDS, TARGET_CHANNEL_ID

from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChannel, InputPeerUser, MessageMediaPhoto, MessageMediaDocument, InputMediaUploadedPhoto, MessageMediaWebPage

# Import the delay configuration
from config import get_delay_seconds

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()



# Channel IDs
# SOURCE_CHANNEL_IDS = [-1002416255517, -1001760869872, -1009876543210]  # Add all source channel IDs here
# TARGET_CHANNEL_ID = -1002309120134  # ID of the channel to forward messages to

# Create a client
client = TelegramClient('user_session', API_ID, API_HASH)

# Queue to store messages for delayed forwarding
message_queue = asyncio.Queue()

# Last forwarded message time
last_forward_time = datetime.now() - timedelta(seconds=get_delay_seconds())

def remove_usernames_and_links(text):
    if text is None:
        return None
    # Remove usernames
    text = re.sub(r'@\w+', '', text)
    
    # Remove Telegram-style links (text in square brackets followed by URL)
    text = re.sub(r'\[([^\]]+)\]\(https?://[^\)]+\)', '', text)
    
    # Remove any remaining URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

async def process_message(message):
    try:
        # Clean the text content
        cleaned_text = remove_usernames_and_links(message.text) if message.text else ""
        
        # Check if the message has a web page preview
        if isinstance(message.media, MessageMediaWebPage):
            # If it's a web page preview, treat it as a text-only message
            if cleaned_text:
                await client.send_message(TARGET_CHANNEL_ID, cleaned_text)
                logger.info(f"Forwarded cleaned text message (removed web preview): {cleaned_text[:30]}...")
            else:
                logger.info("Message was empty after cleaning and removing web preview, skipped")
            return

        if message.media and not isinstance(message.media, MessageMediaWebPage):
            # Download the media (for non-web page media)
            media_file = await message.download_media(file=BytesIO())
            
            if media_file:
                media_file.seek(0)
                if isinstance(message.media, MessageMediaPhoto):
                    # Send as compressed photo
                    uploaded_file = await client.upload_file(media_file, part_size_kb=512)
                    uploaded_media = InputMediaUploadedPhoto(uploaded_file)
                    await client.send_file(
                        TARGET_CHANNEL_ID,
                        file=uploaded_media,
                        caption=cleaned_text
                    )
                else:
                    # For other types of media, send as is
                    await client.send_file(
                        TARGET_CHANNEL_ID,
                        file=media_file,
                        caption=cleaned_text
                    )
                logger.info(f"Forwarded media message with cleaned caption: {cleaned_text[:30] if cleaned_text else 'No caption'}...")
            else:
                logger.warning("Failed to download media, sending as text-only message")
                if cleaned_text:
                    await client.send_message(TARGET_CHANNEL_ID, cleaned_text)
                    logger.info(f"Forwarded cleaned text message: {cleaned_text[:30]}...")
                else:
                    logger.info("Message was empty after cleaning, skipped")
        elif cleaned_text:
            # If it's a text-only message and there's content after cleaning, send it
            await client.send_message(TARGET_CHANNEL_ID, cleaned_text)
            logger.info(f"Forwarded cleaned text message: {cleaned_text[:30]}...")
        else:
            logger.info("Message was empty after cleaning or had no content, skipped")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

async def forward_messages():
    global last_forward_time
    while True:
        if not message_queue.empty():
            current_time = datetime.now()
            if current_time - last_forward_time >= timedelta(seconds=get_delay_seconds()):
                message = await message_queue.get()
                await process_message(message)
                last_forward_time = current_time
                logger.info(f"Processed message at {current_time}")
            else:
                await asyncio.sleep(0.1)  # Short sleep to prevent CPU overuse
        else:
            await asyncio.sleep(0.5)  # Slightly longer sleep when queue is empty

async def main():
    global SOURCE_CHANNEL_IDS  # We'll update this with valid channels

    # Check if session file exists
    session_file = 'user_session.session'
    if os.path.exists(session_file):
        logger.info("Found existing session file. Connecting...")
    else:
        logger.info("No session file found. Please log in.")

    # Start the client
    await client.start()
    logger.info("Client has started.")
    me = await client.get_me()
    logger.info(f"Logged in as: {me.username}")

    # Resolve the channel entities
    valid_source_channels = []
    for channel_id in SOURCE_CHANNEL_IDS:
        try:
            source_channel = await client.get_entity(channel_id)
            logger.info(f"Source channel: {source_channel.title}")
            valid_source_channels.append(channel_id)
        except ValueError as e:
            logger.error(f"Error resolving channel {channel_id}: {e}")
            logger.info(f"Skipping channel {channel_id}")
        except Exception as e:
            logger.error(f"Unexpected error for channel {channel_id}: {e}")
            logger.info(f"Skipping channel {channel_id}")

    if not valid_source_channels:
        logger.error("No valid source channels found. Exiting.")
        return

    # Update SOURCE_CHANNEL_IDS with only valid channels
    SOURCE_CHANNEL_IDS = valid_source_channels

    try:
        target_channel = await client.get_entity(TARGET_CHANNEL_ID)
        logger.info(f"Target channel: {target_channel.title}")
    except ValueError as e:
        logger.error(f"Error resolving target channel: {e}")
        logger.info("Make sure you have access to the target channel and the ID is correct.")
        return
    except Exception as e:
        logger.error(f"Unexpected error resolving target channel: {e}")
        return

    logger.info(f"Listening for messages in channels: {valid_source_channels}")
    logger.info(f"Forwarding messages to channel: {TARGET_CHANNEL_ID}")

    # Set up the event handler for new messages
    @client.on(events.NewMessage(chats=SOURCE_CHANNEL_IDS))
    async def queue_message(event):
        await message_queue.put(event.message)
        logger.info(f"Queued new message from {event.chat_id}")

    # Start the forwarding task
    forward_task = asyncio.create_task(forward_messages())

    try:
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await client.run_until_disconnected()
    finally:
        forward_task.cancel()
        await forward_task

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)