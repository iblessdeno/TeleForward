import asyncio
import sys
import nest_asyncio
import logging
import os
import re
import mimetypes
from datetime import datetime, timedelta
from io import BytesIO
from credentials import API_ID, API_HASH, SOURCE_CHANNEL_IDS, TARGET_CHANNEL_IDS

from telethon import TelegramClient, events
from telethon.tl.types import InputPeerChannel, InputPeerUser, MessageMediaPhoto, MessageMediaDocument, InputMediaUploadedPhoto, MessageMediaWebPage, InputMediaUploadedDocument
from telethon.tl.functions.messages import UploadMediaRequest

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

# Forbidden words
FORBIDDEN_WORDS = ["advertise", "omwamba", "eliking"]

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

def contains_forbidden_words(text, channel_name):
    if text is None:
        return False
    
    text_lower = text.lower()
    channel_name_lower = channel_name.lower()
    
    # Check for channel name similarity
    if channel_name_lower in text_lower:
        return True
    
    # Check for forbidden words
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    
    return False

def get_file_extension(media):
    if isinstance(media, MessageMediaPhoto):
        return '.jpg'
    elif isinstance(media, MessageMediaDocument):
        mime_type = media.document.mime_type
        extension = mimetypes.guess_extension(mime_type)
        return extension if extension else '.bin'
    return ''

async def process_message(message):
    try:
        # Clean the text content
        cleaned_text = remove_usernames_and_links(message.text) if message.text else ""
        
        # Get the source channel name
        source_channel = await client.get_entity(message.peer_id.channel_id)
        source_channel_name = source_channel.title
        
        # Check for forbidden words
        if contains_forbidden_words(cleaned_text, source_channel_name):
            logger.info(f"Message contains forbidden words or channel name, skipped: {cleaned_text[:30]}...")
            return
        
        # Handle messages with media
        if message.media:
            # Check if it's a grouped media message
            if hasattr(message, 'grouped_id'):
                # For grouped media, we need to get all related messages
                chat = await message.get_chat()
                grouped_messages = await client.get_messages(chat, min_id=message.id-10, max_id=message.id+10)
                grouped_messages = [msg for msg in grouped_messages if msg.grouped_id == message.grouped_id]
                media_group = []
                group_text = ""
                for msg in grouped_messages:
                    if msg.text:
                        group_text += remove_usernames_and_links(msg.text) + "\n\n"
                    if msg.media and not isinstance(msg.media, MessageMediaWebPage):
                        file_extension = get_file_extension(msg.media)
                        media_file = await msg.download_media(file=BytesIO(), thumb=-1)
                        if media_file:
                            media_file.seek(0)
                            if isinstance(msg.media, MessageMediaPhoto):
                                uploaded_file = await client.upload_file(media_file, file_name=f'photo{file_extension}')
                                media_group.append(InputMediaUploadedPhoto(uploaded_file))
                            elif isinstance(msg.media, MessageMediaDocument):
                                attributes = msg.media.document.attributes
                                uploaded_file = await client.upload_file(media_file, file_name=f'document{file_extension}')
                                media_group.append(InputMediaUploadedDocument(
                                    file=uploaded_file,
                                    mime_type=msg.media.document.mime_type,
                                    attributes=attributes,
                                    force_file=False
                                ))
                
                # Send the grouped media
                if media_group:
                    for target_id in TARGET_CHANNEL_IDS:
                        await client.send_file(
                            target_id,
                            file=media_group,
                            caption=group_text.strip(),
                            force_document=False
                        )
                    logger.info(f"Forwarded grouped media message ({len(media_group)} items) with cleaned caption to {len(TARGET_CHANNEL_IDS)} channels: {group_text[:30] if group_text else 'No caption'}...")
                else:
                    logger.warning("No valid media found in grouped message")
            
            # Handle single media message
            elif not isinstance(message.media, MessageMediaWebPage):
                file_extension = get_file_extension(message.media)
                media_file = await message.download_media(file=BytesIO(), thumb=-1)
                if media_file:
                    media_file.seek(0)
                    if isinstance(message.media, MessageMediaPhoto):
                        uploaded_file = await client.upload_file(media_file, file_name=f'photo{file_extension}')
                        uploaded_media = InputMediaUploadedPhoto(uploaded_file)
                    elif isinstance(message.media, MessageMediaDocument):
                        attributes = message.media.document.attributes
                        uploaded_file = await client.upload_file(media_file, file_name=f'document{file_extension}')
                        uploaded_media = InputMediaUploadedDocument(
                            file=uploaded_file,
                            mime_type=message.media.document.mime_type,
                            attributes=attributes,
                            force_file=False
                        )
                    else:
                        uploaded_media = media_file

                    for target_id in TARGET_CHANNEL_IDS:
                        await client.send_file(
                            target_id,
                            file=uploaded_media,
                            caption=cleaned_text,
                            force_document=False
                        )
                    logger.info(f"Forwarded single media message with cleaned caption to {len(TARGET_CHANNEL_IDS)} channels: {cleaned_text[:30] if cleaned_text else 'No caption'}...")
                else:
                    logger.warning("Failed to download media, sending as text-only message")
                    if cleaned_text:
                        for target_id in TARGET_CHANNEL_IDS:
                            await client.send_message(target_id, cleaned_text)
                        logger.info(f"Forwarded cleaned text message to {len(TARGET_CHANNEL_IDS)} channels: {cleaned_text[:30]}...")
                    else:
                        logger.info("Message was empty after cleaning, skipped")
            
            # Handle web page preview as text-only message
            elif isinstance(message.media, MessageMediaWebPage):
                if cleaned_text:
                    for target_id in TARGET_CHANNEL_IDS:
                        await client.send_message(target_id, cleaned_text)
                    logger.info(f"Forwarded cleaned text message (removed web preview) to {len(TARGET_CHANNEL_IDS)} channels: {cleaned_text[:30]}...")
                else:
                    logger.info("Message was empty after cleaning and removing web preview, skipped")
        
        # Handle text-only messages
        elif cleaned_text:
            for target_id in TARGET_CHANNEL_IDS:
                await client.send_message(target_id, cleaned_text)
            logger.info(f"Forwarded cleaned text message to {len(TARGET_CHANNEL_IDS)} channels: {cleaned_text[:30]}...")
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
        for target_id in TARGET_CHANNEL_IDS:
            target_channel = await client.get_entity(target_id)
            logger.info(f"Target channel: {target_channel.title}")
    except ValueError as e:
        logger.error(f"Error resolving target channel: {e}")
        logger.info("Make sure you have access to all target channels and the IDs are correct.")
        return
    except Exception as e:
        logger.error(f"Unexpected error resolving target channel: {e}")
        return

    logger.info(f"Listening for messages in channels: {valid_source_channels}")
    logger.info(f"Forwarding messages to channels: {TARGET_CHANNEL_IDS}")

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