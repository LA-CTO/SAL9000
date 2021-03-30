# Imports the Google Cloud client library
from google.cloud import logging
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file('d:\SAL9000\sal9000-307923-a9548c172b1d.json')

def list_entries(logger_name):
    """Lists the most recent entries for a given logger."""
    logging_client = logging.Client()
    logger = logging_client.logger(logger_name)

    print("Listing entries for logger {}:".format(logger.name))

    for entry in logger.list_entries():
        timestamp = entry.timestamp.isoformat()
        print("* {}: {}".format(timestamp, entry.payload))


# Instantiates a client
#credentials='d:\SAL9000\sal9000-307923-a9548c172b1d.json'
logging_client = logging.Client(credentials=credentials)

# The name of the log to write to
log_name = "my-log"
# Selects the log to write to
logger = logging_client.logger(log_name)

# The data to log
text = "Hello, world!"

# Writes the log entry
logger.log_text(text)

print("Logged: {}".format(text))