# Delay configuration
DELAY_UNIT = 'minutes'  # Can be 'seconds', 'minutes', or 'hours'
DELAY_VALUE = 30  # 30 minutes

# Function to get delay in seconds
def get_delay_seconds():
    if DELAY_UNIT == 'seconds':
        return DELAY_VALUE
    elif DELAY_UNIT == 'minutes':
        return DELAY_VALUE * 60
    elif DELAY_UNIT == 'hours':
        return DELAY_VALUE * 3600
    else:
        raise ValueError("Invalid DELAY_UNIT. Use 'seconds', 'minutes', or 'hours'.")