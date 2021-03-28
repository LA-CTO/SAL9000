# RAKE https://github.com/fabianvf/python-rake
# howto: https://towardsdatascience.com/extracting-keyphrases-from-text-rake-and-gensim-in-python-eefd0fad582f
# 
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy handleEvent --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
# url: https://us-west2-sal9000-307923.cloudfunctions.net/handleEvent

# keywordExtraction API call: https://us-west2-sal9000-307923.cloudfunctions.net/keyphraseExtraction?message=helloSal9000
#  

from datetime import datetime
VERY_BEGINNING_TIME = datetime.utcnow()
START_TIME = VERY_BEGINNING_TIME

import json
import RAKE
from google.cloud import secretmanager
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import threading
import re

def getTimeSpan(starttime, label):
    endtime = datetime.utcnow()
    print(str(endtime-starttime)[:-4] + " " + label)
    return endtime

START_TIME = getTimeSpan(START_TIME, 'import time')
GCP_PROJECT_ID = "sal9000-307923"

# TODO:  Put SLACK_BOT_TOKEN and SLACK_USER_TOKEN in Google Secret Manager https://dev.to/googlecloud/using-secrets-in-google-cloud-functions-5aem
# TODO: SecretManager actually takes over 3 seconds to load module and look up secret keys!!  Gonna hardcode Slack OAuth tokens for now, if they
# get stolen I'll just reissue new ones

client = secretmanager.SecretManagerServiceClient()
START_TIME = getTimeSpan(START_TIME, 'secretmanager.SecretManagerServiceClient90')
def getGCPSecretKey(secretname):
    request = {"name": f"projects/{GCP_PROJECT_ID}/secrets/{secretname}/versions/latest"}
    response = client.access_secret_version(request)
    return response.payload.data.decode("UTF-8")
SLACK_BOT_TOKEN = getGCPSecretKey('SLACK_BOT_TOKEN')
SLACK_USER_TOKEN = getGCPSecretKey('SLACK_USER_TOKEN')

SLACK_WEB_CLIENT_BOT = WebClient(token=SLACK_BOT_TOKEN) 
SLACK_WEB_CLIENT_USER = WebClient(token=SLACK_USER_TOKEN) 


#For Slack Search API: https://api.slack.com/methods/search.messages
SLACK_SEARCH_URL = 'https://slack.com/api/search.messages'

#Number of search results to return
#if more than 5, Slack will not unfural block because to big. Yeah dumb.
NUM_SEARCH_RESULTS = 12

#TEST_STRINGS = [
#    "Anyone here use Copper CRM at their company? I’m working with two sales consultants (one is used to Salesforce and the other is used to Hubspot). I personally liked Copper cause it sits on top of Gmail. I’d rather use what the salespeople want to use, but in this case there’s no consensus lol.",
#    "Are there any opinions on accounting systems / ERP's? We're using SAP Business One (aka Baby SAP) and need to upgrade to something a bit more full featured. Personally I find the SAP consulting ecosystem rather abysmal in terms of talent, looking at netsuite as an alternative but curious to know what others are using / we should be looking at."
#    ]

TEST_STRINGS = ["https://knuckleheads.club"]
TEST_USER = 'U5FGEALER' # Gene
#TEST_TS = '1616731334.191200'
TEST_TS = '1616902047.213200'
          
TEST_CHANNEL_ID = 'GUEPXFVDE' #test

STOPWORDS_LIST=RAKE.SmartStopList()
RAKE_OBJECT = RAKE.Rake(RAKE.SmartStopList())

ENDPOINT_URL = "https://us-west2-sal9000-307923.cloudfunctions.net/keyphraseExtraction?message="

SAL_USER = 'U01R035QE3Z'
SAL_IMAGE = 'https://bit.ly/39eK1bY'
SAL_THIN_IMAGE = 'https://files.slack.com/files-pri/T5FGEAL8M-F01SXUR4CJD/sal_thin.jpg?pub_secret=97e5e68214'

START_TIME = getTimeSpan(START_TIME, 'all initialization time')

def RAKEPhraseExtraction(extractString):
    extractString = removeURLsFromText(extractString)
    return RAKE_OBJECT.run(extractString)

# Return reverse order tuple of 2nd element
def sortTuple(tup):
    # key is set to sort using second elemnet of
    # sublist lambda has been used
    tup.sort(key = lambda x: x[1])
    tup.reverse()
    return tup

# Return the top weighed Phrases from RAKE of stringArray
def extractKeyPhrasesRAKE(stringArray):
    raked = RAKEPhraseExtraction(stringArray)
#    print("Raked results: ", raked)
    sortedtuple = sortTuple(raked)[-20:]
    return sortedtuple

# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy keyphraseExtraction --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
def keyphraseExtraction(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response>`.
    """
    rakeme=''
    returnjson = 0
    request_json = request.get_json()
    if request_json and 'challenge' in request_json:
        #Slack url_verification challenge https://api.slack.com/events/url_verification
        return request_json['challenge']
    elif request.args and 'message' in request.args:
        returnjson = 'returnjson' in request.args
        rakeme = request.args.get('message')
    elif request_json and 'message' in request_json:
        returnjson = request_json['returnjson']
        rakeme =  request_json['message']
    else:
        rakeme = ''
    
    keyPhrases = extractKeyPhrasesRAKE(rakeme)
    return str(keyPhrases)

# Event handler for 3 types of events:
# 1) New message to public channel (message.channels) or private channel (message.groups), events registered here: https://api.slack.com/apps/A01R8CEGVMF/event-subscriptions?
# EventSubscription detected a top post in channel, SAL9000 to extract KeyPhrase, Search and Respond
# 2) User adds :sal9001: emoji to post, SAL to reply to that post
# 3) Interactive user push search button. Registered here: https://api.slack.com/apps/A01R8CEGVMF/interactive-messages
# Use selected a keyphrase from SAL9001 first response, perform Search and Respond with search results
#
#
# Slack handleEvent webhook: https://us-west2-sal9000-307923.cloudfunctions.net/handleEvent
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy handleEvent --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
#
def handleEvent(request):
    # Google Scheduler 5 minute warmer
    # https://us-west2-sal9000-307923.cloudfunctions.net/handleEvent?warmer=true
    if request.args.get('warmer'): 
        print('handleEvent Google Scheduler 5 min warmer')
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

    # Don't handle any retry requests - Slack sends retries if it doesn't get response in 3 seconds
    retryNum = request.headers.get('X-Slack-Retry-Num')
    if retryNum and int(retryNum) > 1:
        print('handleEvent retryNum: ', retryNum)
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    
    request_json = request.get_json()
    eventAttributes = {}
    if request_json: # GET - must be new post event message.channels or message.groups
        if 'challenge' in request_json:
        #Slack url_verification challenge https://api.slack.com/events/url_verification
            return request_json['challenge']
        event = request_json['event']
        if event:
            if 'bot_id' in event:
                print('This is a bot message so not responding to it')
            elif event.get("subtype"):
                print('This is subtype so not responding to it: ', event.get("subtype"))
            elif 'text' in event and 'thread_ts' not in event:
                print("main.handleEvent GET text: ", event['text'])
                eventAttributes = {
                    'user': event['user'],
                    'channel_id': event['channel'],
                    'thread_ts': event['ts'],
                    'text': event['text'],
                    'searchme': ''
                }
            elif 'reaction_added' == event.get('type') and "sal9001" == event.get('reaction') and 'message' == event.get('item').get('type'): #User add sal9001 emoji::
                print('main.handleEven GET :sal9001: emoji payload:', event)
                channel_id = event.get('item').get('channel')
                ts = event.get('item').get('ts')
                user = event.get('user')
                #Get message from Slack API to get text
                response = SLACK_WEB_CLIENT_USER.conversations_history(channel=channel_id,latest=ts,limit=1,inclusive='true') 
                if response:
                    print('retrived whole response: ', response)
                    thisMessage =  response.get('messages')[0]
                    print('retrieved requested ts: ' + ts + " got response ts: " + thisMessage.get('ts') + " I hope: " + str(thisMessage))
                    if thisMessage.get('ts') == ts: #only respond to top message emoji
                        text = thisMessage.get('text')
                        eventAttributes = {
                            'user': user,
                            'channel_id': channel_id,
                            'thread_ts': ts,
                            'text': text,
                            'searchme': ''
                        }

            else:
                print("This GET request fell through all filters, event: ", event)
        else:
            print("This message has no event element?? Doing nothing...")
    else: # POST - Interactive event
        payload = json.loads(request.form.get('payload'))
        print('main.handleEven POST Interactive Event with payload: ', payload)
        payload_type = payload["type"]
        if "block_actions" == payload_type: #User pushed a search button
            text = payload['message']['text']
            print("main.handleEvent POST text: ", text)
            print("main.handleEvent POST bock_action: ", text)
            eventAttributes = {
                'user': payload['user']['id'],
                'channel_id': payload['channel']['id'],
                'thread_ts': payload['message']['thread_ts'], 
                'this_ts': payload['message']['ts'], 
                'searchme': payload["actions"][0]['value'],
                'text': text
            }

    if len(eventAttributes) > 0:
        constructAndPostBlock(eventAttributes)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 


# Asynchronously Construct a Slack block and post/update it
# Don't use this for now as weird stuff happens
def constructAndPostBlockAsync(eventAttributes):
    thread = threading.Thread(target=constructAndPostBlock, args=[eventAttributes])
    thread.start()


# Construct a Slack block and post/update it
def constructAndPostBlock(eventAttributes):
    startime = datetime.utcnow() 
    block = constructBlock(eventAttributes)
    getTimeSpan(startime, 'constructBlock')
    startime2 = datetime.utcnow() 
    response = postBlockToSlackChannel(eventAttributes, block)
    getTimeSpan(startime2, 'postBlockToSlackChannel')
#    getTimeSpan(startime, 'constructAndPostBlock')

#Posts a Block to parent post thread_ts.  
# If this_ts > 0, this is a user button push, update the existing block with with new search results
def postBlockToSlackChannel(eventAttributes, block):
    channel_id = eventAttributes['channel_id']
    text = eventAttributes['text']
    response = ''
    try:
        if 'this_ts' not in eventAttributes: 
###            print('posting new block to thread:', block)
            thread_ts = eventAttributes['thread_ts']
            response = SLACK_WEB_CLIENT_BOT.chat_postMessage(
                channel = channel_id,
                thread_ts=thread_ts,
                text = text,
                blocks = block
            )
        else: # user button push of existing block, update
            this_ts = eventAttributes['this_ts']
            print('update existing block to thread because this_ts:', this_ts)
            response = SLACK_WEB_CLIENT_BOT.chat_update(
                channel = channel_id,
                ts=this_ts,
                blocks = block,
                text = text,
                attachments=[] #zero out attachments just in case
            )

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        print('error postBlockToSlackChannel:', e)
        assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'
    return response    

# This method will construct the Slack Block 
def constructBlock(eventAttributes):
    starttime = datetime.utcnow()
    text = eventAttributes['text']
    user = eventAttributes['user']
    searchme = ''
    if 'searchme' in eventAttributes:
        searchme = eventAttributes['searchme']
    extractedKeyPhrases = extractKeyPhrasesRAKE(text)

    if(len(extractedKeyPhrases) < 0):
        greetings =  "Hello <@" + user + "> I don't know what you want"
    else:
        greetings ="Hello <@" + user +"> please pick a keyphrase for me to search my memory banks: " + "\n"

    slack_block_kit = [
        {
			"type": "image",
			"block_id": "sal_THIN_image",
			"image_url": SAL_THIN_IMAGE,
			"alt_text": "SAL 9001"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": greetings
			}
        }
    ]

#    print('Slack Blockkit: ', slack_block_kit)
    count = 0
    searchButtons = []
    for keyPhraseTuple in extractedKeyPhrases:
        keyPhrase = keyPhraseTuple[0]
        weight = keyPhraseTuple[1]
        thisButtonStyle = "primary"
        if len(searchme) > 0:
            if searchme == keyPhrase:
                thisButtonStyle = "danger"
        elif count == 0:
            thisButtonStyle = "danger"
            searchme = keyPhrase
        count += 1    

        searchButtons.append(
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": keyPhrase + " (" + str(weight) + ")"
                },
    			"style": thisButtonStyle,
                "value": keyPhrase,
            }
        )

    if len(searchButtons) > 0:
        slack_block_kit.append(
            {
                "type": "actions",
                "elements": searchButtons
            }
        )

    searchResultsString = ''
    if len(searchme) > 1: #don't bother searching if searchme length <= 1
        searchResults = searchSlackMessages(searchme, NUM_SEARCH_RESULTS, 1)
        count = 1
        thread_ts = ''
        if 'thread_ts' in eventAttributes:
            thread_ts = eventAttributes['thread_ts']
        for thisSearchResult in searchResults['messages']['matches']:
            thisUser = thisSearchResult['user']
            thisUserName = thisSearchResult['username']
            this_ts = thisSearchResult['ts']
            thisDate = datetime.fromtimestamp(int(this_ts.split(".")[0])).strftime('%m-%d-%y')

            if SAL_USER == thisUser: #skip posts by SAL
                continue
            if thread_ts == this_ts: #skip this parent post
                continue
            #Don't @user in search results, can get annying
            searchResultsString += "<" + thisSearchResult['permalink'] + "|" + thisDate + " " + searchme + "> " + " from "+ thisUserName+ "\n"
            count += 1

    if len(searchResultsString) == 0:
        searchResultsString = "I'm sorry <@" + user + ">. I'm afraid I can't do that."    

    endtime = datetime.utcnow()
    elapsestr = str(endtime-starttime)[:-4]
    searchResultsString += "\nsearch time: " + elapsestr
    slack_block_kit.append(
       {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": searchResultsString
            }
        }
    )
 
    return slack_block_kit


def removeURLsFromText(text):
    return re.sub(r'<?http\S+', '', text)

# defining a params dict for the parameters to be sent to the API 
# https://api.slack.com/methods/search.messages
#  
# arguments
# query=text, count=20, highlight=true, page=1, sort=score/timestamp, sort_dir=desc/asc, team_id=T1234567890
#
# Returns json of results as described: https://api.slack.com/methods/search.messages  
def searchSlackMessages(text, resultCount, page):
# Limit search to in #techandtools only for now
#    text = "in:techandtools " + text
    response = SLACK_WEB_CLIENT_USER.search_messages(query=text, sort='score', sor_dir='desc', count=resultCount, page=page) 
#    print ('search response: ', response)
    return response

# Main for commandline run and quick tests
if __name__ == "__main__":
    START_TIME = getTimeSpan(START_TIME, 'main start')
#    for extractme in TEST_STRINGS:
#        print('Raking:', extractme)
#        raked = extractKeyPhrasesRAKE(extractme)
#        print('raked return top:', raked)

        #testing RESTFUL call to keyPhraseExtraction
#        extractmeurl = ENDPOINT_URL + extractme
#        print("calling url: ", extractmeurl)
#        response = requests.get(extractmeurl)
#        print("response: ", response.content)

    #postMessageToSlackChannel('test', '', 'Hello from SAL 9001! :tada:')        

    # Test Block construction which includes Slack Search
    # SALsays = constructBlock(TEST_USER, 'serverless', '')
    # print("SALsays: ", SALsays)

    # Test Constructing and posting new block to Slack
    eventAttributes = {
        'text': TEST_STRINGS[0], 
        'channel_id': TEST_CHANNEL_ID, 
        'thread_ts': TEST_TS, 
        'user': TEST_USER
        }
    constructAndPostBlock(eventAttributes)

    START_TIME = getTimeSpan(VERY_BEGINNING_TIME, 'total')

