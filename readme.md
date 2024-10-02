# TeleForward: Telegram Channel Content Curator

TeleForward is a Python-based Telegram bot that automatically forwards and curates content from multiple source channels to one or more target channels. It offers features like link removal, username anonymization, and customizable forwarding delays.

## Features

- Forward messages from multiple source channels to target channels
- Remove usernames and links from forwarded messages
- Compress and forward images
- Remove web page previews
- Customizable delay between forwarded messages
- Configurable via external files for easy customization and privacy

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/teleforward.git
   cd teleforward
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `credentials.py` file with your Telegram API credentials:
   ```python
   API_ID = 'your_api_id'
   API_HASH = 'your_api_hash'
   ```

4. Update `config.py` with your desired delay settings:
    ```python
   DELAY_UNIT = 'minutes'  # Can be 'seconds', 'minutes', or 'hours'
   DELAY_VALUE = 5  # The number of units to delay
   ```

5. Update `bot.py` with your source and target channel IDs:
   ```python
   SOURCE_CHANNEL_IDS = [channel_id1, channel_id2, channel_id3]  # Add all source channel IDs here
   TARGET_CHANNEL_ID = target_channel_id  # ID of the channel to forward messages to
   ```

## Usage

Run the bot using:
```
python bot.py
```

The bot will start forwarding messages from the specified source channels to the target channel, applying the configured delay between messages.

## Configuration

- `credentials.py`: Store your Telegram API credentials
- `config.py`: Configure the delay between forwarded messages
- `bot.py`: Set source and target channel IDs, and customize forwarding behavior

## Functionality

1. **Message Cleaning**: Removes usernames, links, and web page previews from messages.
2. **Media Handling**: Compresses and forwards images, forwards other media types as-is.
3. **Delayed Forwarding**: Implements a configurable delay between forwarding messages to avoid flooding.
4. **Multi-Channel Support**: Can listen to multiple source channels and forward to a target channel.
5. **Error Handling**: Robust error handling and logging for easy troubleshooting.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Created by iblessdeno
- Special thanks to the Telethon library developers

