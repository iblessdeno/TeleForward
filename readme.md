# TeleForward: Telegram Channel Content Curator

TeleForward is a Python-based Telegram bot that automatically forwards and curates content from multiple source channels to a target channel. It offers features like link removal, username anonymization, and customizable forwarding delays.

## Features

- Forward messages from multiple source channels to a target channel
- Remove usernames and links from forwarded messages
- Compress and forward images
- Remove web page previews
- Customizable delay between forwarded messages
- Configurable via external files for easy customization and privacy

## Setup

### Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/iblessdeno/TeleForward.git
   cd TeleForward
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `credentials.py` file with your Telegram API credentials and channel IDs:
   ```python
   API_ID = 'your_api_id'
   API_HASH = 'your_api_hash'
   SOURCE_CHANNEL_IDS = [channel_id1, channel_id2, channel_id3]
   TARGET_CHANNEL_ID = target_channel_id
   ```

4. Update `config.py` with your desired delay settings if needed.

5. Run the bot:
   ```
   python bot.py
   ```
### VPS Setup

1. Connect to your VPS via SSH:
   ```
   ssh username@your_vps_ip
   ```

2. Install Git, Python, and pip:
   ```
   sudo apt update
   sudo apt install git python3 python3-pip
   ```

3. Clone the repository:
   ```
   git clone https://github.com/iblessdeno/TeleForward.git
   cd TeleForward
   ```

4. Install the required packages:
   ```
   pip3 install -r requirements.txt
   ```

5. Create the `credentials.py` file:
   ```
   nano credentials.py
   ```
   Add the following content, replacing with your actual values:
   ```python
   API_ID = 'your_api_id'
   API_HASH = 'your_api_hash'
   SOURCE_CHANNEL_IDS = [channel_id1, channel_id2, channel_id3]
   TARGET_CHANNEL_IDS = target_channel_id
   ```
   Save and exit (Ctrl+X, then Y, then Enter).

6. Run the bot:
   ```
   python3 bot.py
   ```

7. To keep the bot running after closing the SSH session, use `nohup`:
   ```
   nohup python3 bot.py > bot.log 2>&1 &
   ```

8. To stop the bot later:
   ```
   ps aux | grep python3
   kill -9 <process_id>
   ```

## Configuration

- `credentials.py`: Store your Telegram API credentials and channel IDs
- `config.py`: Configure the delay between forwarded messages (default is 30 minutes)

## Updating the Bot

To update the bot with the latest changes from the repository:

1. Stop the bot if it's running
2. Pull the latest changes:
   ```
   git pull
   ```
3. Restart the bot

## Troubleshooting

- If you encounter permission issues, ensure you have the necessary rights to access all specified channels.
- Check the `bot.log` file for any error messages if the bot stops unexpectedly.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Created by iblessdeno
- Special thanks to the Telethon library developers

## Repository

For the latest version and to contribute, visit the GitHub repository:
[https://github.com/iblessdeno/TeleForward](https://github.com/iblessdeno/TeleForward)
