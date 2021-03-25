# RAKE https://github.com/fabianvf/python-rake
# howto: https://towardsdatascience.com/extracting-keyphrases-from-text-rake-and-gensim-in-python-eefd0fad582f
# 
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy handleEvent --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
# url: https://us-west2-sal9000-307923.cloudfunctions.net/handleEvent

# keywordExtraction API call: https://us-west2-sal9000-307923.cloudfunctions.net/keyphraseExtraction?message=helloSal9000
#  

import json
import RAKE
from rake_nltk import Rake
import spacy
import pytextrank
import requests
from google.cloud import secretmanager
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from threading import Thread
import time
from datetime import datetime

# TODO:  Put SLACK_BOT_TOKEN and SLACK_USER_TOKEN in Google Secret Manager https://dev.to/googlecloud/using-secrets-in-google-cloud-functions-5aem
client = secretmanager.SecretManagerServiceClient()
GCP_PROJECT_ID = "sal9000-307923"

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
NUM_SEARCH_RESULTS = 20

#TEST_STRINGS = [
#    "Anyone here use Copper CRM at their company? I’m working with two sales consultants (one is used to Salesforce and the other is used to Hubspot). I personally liked Copper cause it sits on top of Gmail. I’d rather use what the salespeople want to use, but in this case there’s no consensus lol.",
#    "Are there any opinions on accounting systems / ERP's? We're using SAP Business One (aka Baby SAP) and need to upgrade to something a bit more full featured. Personally I find the SAP consulting ecosystem rather abysmal in terms of talent, looking at netsuite as an alternative but curious to know what others are using / we should be looking at."
#    ]

TEST_STRINGS = ["What is redis vs mongodb?"]
TEST_USER = 'U5FGEALER' # Gene
TEST_TS = '1616650666.157000'
TEST_CHANNEL_ID = 'GUEPXFVDE' #test

STOPWORDS_LIST=RAKE.SmartStopList()
RAKE_OBJECT = RAKE.Rake(RAKE.SmartStopList())
ENDPOINT_URL = "https://us-west2-sal9000-307923.cloudfunctions.net/keyphraseExtraction?message="

SAL_USER = 'U01R035QE3Z'
SAL_IMAGE = 'https://bit.ly/39eK1bY'
SAL_THIN_IMAGE = 'https://bit.ly/3vQjA65'
def RAKEPhraseExtraction(extractString):
    return RAKE_OBJECT.run(extractString)

# Return reverse order tuple of 2nd element
def sortTuple(tup):
    # key is set to sort using second elemnet of
    # sublist lambda has been used
    tup.sort(key = lambda x: x[1])
    tup.reverse()
    return tup

# Return the top weighed Phrases from RAKE of stringArray
def extractTopPhrasesRAKE(stringArray, returnJSON):
    raked = RAKEPhraseExtraction(stringArray)
#    print("Raked results: ", raked)
    sortedtuple = sortTuple(raked)[-10:]
    if returnJSON:
        return sortedtuple
    else:
        if sortedtuple and sortedtuple[0]:
            return sortedtuple[0][0]
        else:
            return ''

#RAKE-NLTK
def RAKENLTKPhaseExtraction(extractString):
    r = Rake() # Uses stopwords for english from NLTK, and all punctuation characters
    r.extract_keywords_from_text(extractString)
    return r.get_ranked_phrases()[0:10]

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
    
    keyPhrases = extractTopPhrasesRAKE(rakeme, returnjson)
    return str(keyPhrases)

# Event handler for two types of events:
# 1) New message to public channel (message.channels) or private channel (message.groups), events registered here: https://api.slack.com/apps/A01R8CEGVMF/event-subscriptions?
# EventSubscription detected a top post in channel, SAL9000 to extract KeyPhrase, Search and Respond
#
# 2) Interactive user push search button. Registered here: https://api.slack.com/apps/A01R8CEGVMF/interactive-messages
# Use selected a keyphrase from SAL9001 first response, perform Search and Respond with search results
#
# Slack handleEvent webhook: https://us-west2-sal9000-307923.cloudfunctions.net/handleEvent
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy handleEvent --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
#
def handleEvent(request):
    request_json = request.get_json()
    eventAttributes = {}
    if request_json: # GET - must be new post event message.channels or message.groups
        print("main.handleEvent GET message.channels with request: ", request_json)
        if 'challenge' in request_json:
        #Slack url_verification challenge https://api.slack.com/events/url_verification
            return request_json['challenge']
        event = request_json['event']
        if event:
            if 'bot_id' in event:
                print('This is a bot message so not responding to it')
            elif 'thread_ts' in event:
                print('This is a thread message so not responding to it')
            elif event.get("subtype"):
                print('This is subtype so not repsponding to it: ', event.get("subtype"))
            elif 'text' in event:
                eventAttributes = {
                    'user': event['user'],
                    'channel_id': event['channel'],
                    'thread_ts': event['ts'],
                    'text': event['text'],
                    'searchme': ''
                }
            else:
                print("This message request fell through all filters, so not responding to it")
        else:
            print("This message has no event element?? Doing nothing...")
    else: # POST - Interactive event
        payload = json.loads(request.form.get('payload'))
        print('main.handleEven POST Interactive Event with payload: ', payload)
        payload_type = payload["type"]
        if payload_type == "block_actions":
            eventAttributes = {
                'user': payload['user']['id'],
                'channel_id': payload['channel']['id'],
                'thread_ts': payload['message']['thread_ts'], 
                'this_ts': payload['message']['ts'], 
                'searchme': payload["actions"][0]['value'],
                'text': payload['message']['text']
            }
            print('Interactive eventAttributes:', eventAttributes)

    if len(eventAttributes) > 0:
        constructAndPostBlock(eventAttributes)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

# Create a thread to handle the request and respond immediately
# A response time of longer than 3 seconds causes a timeout 
# error message in Slack
# I don't think this is needed and causing weird stuff in Google Function runtime
def handleEventAsync(eventAttributes):
    thr_response = Thread(target=constructAndPostBlock,
                          args=[eventAttributes])
    thr_response.start()

# Construct a Slack block and post/update it
def constructAndPostBlock(eventAttributes):
    start = time.time()
    block = constructBlock(eventAttributes)
    end = time.time()
    print('constructBlock time: ' + str(end-start))
    response = postBlockToSlackChannel(eventAttributes, block)
    end2 = time.time()
    print('postBlockToSlackChannel time: ' + str(end2-end))

#Posts a Block to parent post thread_ts.  
# If this_ts > 0, this is a user button push, update the existing block with with new search results
def postBlockToSlackChannel(eventAttributes, block):
    channel_id = eventAttributes['channel_id']
    text = eventAttributes['text']
    response = ''
    try:
        if 'this_ts' not in eventAttributes: 
            print('posting new block to thread:', block)
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
    text = eventAttributes['text']
    user = eventAttributes['user']
    searchme = ''
    if 'searchme' in eventAttributes:
        searchme = eventAttributes['searchme']
    extractedKeyPhrases = extractTopPhrasesRAKE(text, 1)
    if(len(extractedKeyPhrases) < 0):
        return "Hello <@" + user + "> I don't know what you want"

    returnStr="Hello <@" + user +"> please pick a keyphrase for me to search my memory banks:\n"

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
                "text": returnStr
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
    slack_block_kit.append(
        {
            "type": "actions",
            "elements": searchButtons
        }
    )

    searchResults = searchSlackMessages(searchme, NUM_SEARCH_RESULTS, 1)
    searchResultsString = ''
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
#        searchResultsString += "<" + thisSearchResult['permalink'] + "|" + searchme + " post " + str(count) + "> from <@"+ thisUser+">\n"
        searchResultsString += "<" + thisSearchResult['permalink'] + "|" + str(count) + " " + searchme + "> " + thisDate + " from "+ thisUserName+ "\n"
        count += 1

    if len(searchResultsString) == 0:
        searchResultsString = "I'm sorry <@" + user + ">. I'm afraid I can't do that."    
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
    print('found SLACK_BOT_TOKEN:', SLACK_BOT_TOKEN)
    print('found SLACK_USER_TOKEN:', SLACK_USER_TOKEN)

    for extractme in TEST_STRINGS:
        print('Raking:', extractme)
        raked = extractTopPhrasesRAKE(extractme, 0)
        print('raked return top:', raked)
        raked = extractTopPhrasesRAKE(extractme, 1)
        print('raked return all:', raked)

        print('Rake_NLTK results:', RAKENLTKPhaseExtraction(extractme))

        print('PyTextRanking: ', extractme)
        # load a spaCy model, depending on language, scale, etc.
        nlp = spacy.load("en_core_web_sm")
        # add PyTextRank to the spaCy pipeline
        nlp.add_pipe("textrank", last=True)
        doc = nlp(extractme)
        # examine the top-ranked phrases in the document
        print('PyTextRank:', doc._.phrases)
        for p in doc._.phrases:
            print("{:.4f} {:5d}  {}".format(p.rank, p.count, p.text))
        #    print(p.chunks)

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
    start = time.time()    
    constructAndPostBlock(eventAttributes)
    end = time.time()
    print('constructAndPostBlock time:', str(end-start))
