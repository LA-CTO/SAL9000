# Imports the Google Cloud client library
from google.cloud import logging
from google.oauth2 import service_account
import datetime

LOGGING_CLIENT = None

if __name__ == "__main__":
    CREDENTIALS = service_account.Credentials.from_service_account_file('d:\SAL9000\sal9000-307923-a9548c172b1d.json')
    # Instantiates a client
    LOGGING_CLIENT = logging.Client(credentials=CREDENTIALS)
else:
    LOGGING_CLIENT = logging.Client()

# The name of the log to write to
#LOGGER_NAME = "my-log"
LOGGER_NAME="cloudfunctions.googleapis.com%2Fcloud-functions"

# Selects the log to write to
LOGGER = LOGGING_CLIENT.logger(LOGGER_NAME)

"""
gcloud logging read 'timestamp>"2021-04-01"' --project=sal9000-307923
gcloud logging read 'timestamp>="2021-04-01T18:30:15.384732Z"' --project=sal9000-307923

https://console.cloud.google.com/logs/query;query=resource.type%20%3D%20%22cloud_function%22%0Aresource.labels.region%20%3D%20%22us-west2%22%0Aseverity%3E%3DDEFAULT%0Alog_name%3D%22projects%2Fsal9000-307923%2Flogs%2Fcloudfunctions.googleapis.com%252Fcloud-functions%22?project=sal9000-307923

resource.type = "cloud_function"
resource.labels.region = "us-west2"
severity>=DEFAULT
timestamp >= "2016-11-29T23:00:00Z"
timestamp <= "2016-11-29T23:30:00Z"
timestamp>="2021-04-01"

This method will list logging entries duration_secs into the past from NOW
"""
def list_entries(duration_secs, onlyError):
    now_ts = datetime.datetime.utcnow()
    print("Now timestamp: ", now_ts)
    range_ts = now_ts - datetime.timedelta(seconds=duration_secs)
    print("Range  timestamp: ", range_ts)

#    filter_str = 'timestamp>="2021-04-01T18:30:15.384732Z"'
    filter_str = 'timestamp >="' + range_ts.strftime("%Y-%m-%dT%H:%M:%S.%fZ") + '"'
    if onlyError:
        filter_str += " severity >= ERROR"
    print("Listing entries for logger {}:".format(LOGGER.name) + " with filter: " + filter_str)
    log_entries = LOGGER.list_entries(filter_=filter_str)
#    for entry in log_entries:
#        timestamp = entry.timestamp.isoformat()
#        print("* {}: {}".format(timestamp, entry.payload))
    return log_entries

if __name__ == "__main__":
    list_entries(60*10, 0)

