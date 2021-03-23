# RAKE https://github.com/fabianvf/python-rake
# howto: https://towardsdatascience.com/extracting-keyphrases-from-text-rake-and-gensim-in-python-eefd0fad582f
# 
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy keyphraseExtraction --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
# Deploy from github:
# gcloud functions deploy keyphaseExtraction --project=sal9000-307923 --source=https://source.developers.google.com/projects/sal9000-307923/repos/github_genechuang_sal9000/moveable-aliases/main/paths// --runtime=python39 --trigger-http --allow-unauthenticated --region=us-west2
#
# Call functionl: https://us-west2-sal9000-307923.cloudfunctions.net/keyphraseExtraction?message=helloSal9000
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
NUM_SEARCH_RESULTS = 3

#TEST_STRINGS = [
#    "Anyone here use Copper CRM at their company? I’m working with two sales consultants (one is used to Salesforce and the other is used to Hubspot). I personally liked Copper cause it sits on top of Gmail. I’d rather use what the salespeople want to use, but in this case there’s no consensus lol.",
#    "Are there any opinions on accounting systems / ERP's? We're using SAP Business One (aka Baby SAP) and need to upgrade to something a bit more full featured. Personally I find the SAP consulting ecosystem rather abysmal in terms of talent, looking at netsuite as an alternative but curious to know what others are using / we should be looking at."
#    ]

TEST_STRINGS = ["What is redis?"]

STOPWORDS_LIST=RAKE.SmartStopList()
RAKE_OBJECT = RAKE.Rake(RAKE.SmartStopList())
ENDPOINT_URL = "https://us-west2-sal9000-307923.cloudfunctions.net/keyphraseExtraction?message="


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

# EventSubscription detected a top post in channel, SAL9000 to extract KeyPhrase, Search and Respond
# Slack Event webhook: https://us-west2-sal9000-307923.cloudfunctions.net/respondToPost
# https://api.slack.com/events/message.groups
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy respondToPost --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
#
# Sample request: {'token': '41px5FTEvkFHVLe5rCf7KQyU', 'team_id': 'T5FGEAL8M', 'api_app_id': 'A01R8CEGVMF', 'event': {'client_msg_id': '566327fd-2d22-4255-a72a-1c885d593d1c', 'type': 'message', 'text': 'SAL 9001 are you reading this message to a PRIVATE channel in GCP function? I subscribed to message.groups not message.channels <https://api.slack.com/apps/A01R8CEGVMF/event-subscriptions>', 'user': 'U5FGEALER', 'ts': '1616434450.064100', 'team': 'T5FGEAL8M', 'blocks': [{'type': 'rich_text', 'block_id': 'Qpo', 'elements': [{'type': 'rich_text_section', 'elements': [{'type': 'text', 'text': 'SAL 9001 are you reading this message to a PRIVATE channel in GCP function? I subscribed to message.groups not message.channels '}, {'type': 'link', 'url': 'https://api.slack.com/apps/A01R8CEGVMF/event-subscriptions'}]}]}], 'channel': 'GUEPXFVDE', 'event_ts': '1616434450.064100', 'channel_type': 'group'}, 'type': 'event_callback', 'event_id': 'Ev01SS5E8A6L', 'event_time': 1616434450, 'authorizations': [{'enterprise_id': None, 'team_id': 'T5FGEAL8M', 'user_id': 'U01R035QE3Z', 'is_bot': True, 'is_enterprise_install': False}], 'is_ext_shared_channel': False, 'event_context': '1-message-T5FGEAL8M-GUEPXFVDE'}

def respondToPost(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    print("main.respondToPost called with request: ", request_json)
    if request_json and 'challenge' in request_json:
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
            handleAsynchSALResponse(event, NUM_SEARCH_RESULTS)
        else:
            print("This message request fell through all filters, so not responding to it")
    else:
            print("This message has no event element?? Doing nothing...")

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

# Use selected a keyphrase from SAL9001 first response, perform Search and Respond with search results
# Slack Event webhook: https://us-west2-sal9000-307923.cloudfunctions.net/respondToSearchButton
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy respondToSearchButton --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2
#

def respondToSearchButton(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.make_response>`.
    """
    print("main.respondToSearchButton called with request: ", request)

 # Get data from payload stolen from Phoebe: https://github.com/TotoroSyd/heybot/blob/master/heybot_v2.py

    #solution janice https://medium.com/@janicejabraham/creating-a-slack-app-using-the-events-api-and-slack-dialog-368ea54273af
    payload = json.loads(request.form.get('payload'))
    print('respondToSearch got payload: ', payload)
    payload_type = payload["type"]
    print('respondToSearch payload_type: ', payload_type)
    # Initiate channel_id

    if payload_type == "block_actions":
        # get channel_id
        channel_id = payload["channel"]["id"]
        # Get action id to track button action
        actions = payload["actions"][0]
        value = actions["value"]
        searchme = value

        print('Gonna refresh the block with new search:', searchme)
        handleAsynchButtonResponse(payload, NUM_SEARCH_RESULTS, searchme)
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

def handleAsynchButtonResponse(payload, rtnCount, searchme):
    thr_response = Thread(target=handleButtonResponse,
                          args=[payload, rtnCount, searchme])
    thr_response.start()

def handleButtonResponse(payload, rtnCount, searchme):
    print('about to extract some info from payload: ', payload)
    user = payload['user']['id']
    channel_id = payload['channel']['id']
    thread_ts = payload['message']['thread_ts'] 
    this_ts = payload['message']['ts'] 
    text = payload['message']['text']

    block = constructSALReply(user, text, rtnCount, searchme)
    print('Modified block: ', block)
    response = postBlockToSlackChannel(channel_id, thread_ts, this_ts, block, text)


# Create a thread to handle the request and respond immediately
# A response time of longer than 3 seconds causes a timeout 
# error message in Slack
def handleAsynchSALResponse(event, rtnCount):
    thr_response = Thread(target=handleSALResponse,
                          args=[event, 3])
    thr_response.start()

def handleSALResponse(event, rtnCount):
    text = event['text']
    channel_id = event['channel']
    ts = event['ts']
    user = event['user']

    block = constructSALReply(user, text, rtnCount, '')
    response = postBlockToSlackChannel(channel_id, ts, '', block, text)


#Posts a String message to Slack channel
def postMessageToSlackChannel(channel, ts, text):
    # Test send message to 'test' channel
    try:
        response = SLACK_WEB_CLIENT_BOT.chat_postMessage(
        channel = channel,
        thread_ts=ts,
        text = text
        )
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        print('error sending message to slack channel:', e)
        assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'
    return response    

#Posts a Block to parent post thread_ts.  If this_ts > 0, update the Block
def postBlockToSlackChannel(channel, thread_ts, this_ts, block, text):
    # Test send blockkit to 'test' channel
    try:
        if len(this_ts) == 0: #Post a new reply block
            response = SLACK_WEB_CLIENT_BOT.chat_postMessage(
            channel = channel,
            thread_ts=thread_ts,
            text = text,
            blocks = block
            )
        else: #Update the existing reply block and unfurl the permalink
            response = SLACK_WEB_CLIENT_BOT.chat_update(
            channel = channel,
            ts=this_ts,
            text = text,
            blocks = block,
            attachments = [] # remove previous preview attachments, hopefully will generate new previews?
            )

            
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        print('error sending message to slack channel:', e)
        assert e.response["error"]    # str like 'invalid_auth', 'channel_not_found'
    return response    

# This method will construct the entire SAL 9001 Response, may be Boxkit
def constructSALReply(user, text, resultCount, searchme):

    extractedKeyPhrases = extractTopPhrasesRAKE(text, 1)
    count = 0
#    print('who is ', user)
    whoami = SLACK_WEB_CLIENT_BOT.users_info(user=user)
#    print('whoami is ', whoami)
    username = whoami['user']['name'];
#    print('username is ', username)
    if(len(extractedKeyPhrases) < 0):
        return "Hello @" + username + " I don't know what you want"

#    returnStr="Hello @" + username +" I think you meant " + str(extractedKeyPhrases) + ", results:\n"
    returnStr="Hello @" + username +" please pick one of the following topics for me to noodle on:\n"

    slack_block_kit = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": returnStr
            }
        },
        {
			"type": "divider"
		},
    ]

#    print('Slack Blockkit: ', slack_block_kit)
    elements = []
    count = 0
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

        elements.append(
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": keyPhrase + " " + str(weight)
                },
    			"style": thisButtonStyle,
                "value": keyPhrase,
            }
        )
    slack_block_kit.append(
        {
            "type": "actions",
            "elements": elements
        }
    )
    slack_block_kit.append(
        {
			"type": "divider"
		}
    )
#    print('Slack Blockkit before search: ', slack_block_kit)
    resultLinks = searchSlackMessages(searchme, NUM_SEARCH_RESULTS, 1)
    linksString = ''
    for thisPermaLink in resultLinks:
        linksString += thisPermaLink + '\n'
    slack_block_kit.append(
       {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": linksString
            }
        }
    )
    print('Slack Blockkit after search: ', slack_block_kit)

    return slack_block_kit


EXAMPLE_BLOCK = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "You have a new request:\n*<fakeLink.toEmployeeProfile.com|Fred Enriquez - New device request>*"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Approve"
					},
					"style": "primary",
					"value": "click_me_123"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Deny"
					},
					"style": "danger",
					"value": "click_me_123"
				}
			]
		}
]

# defining a params dict for the parameters to be sent to the API 
# https://api.slack.com/methods/search.messages
#  
# arguments
# query=text, count=20, highlight=true, page=1, sort=score/timestamp, sort_dir=desc/asc, team_id=T1234567890
#
# Return a lit of permalinks of matched results

def searchSlackMessages(text, resultCount, page):
    results = []
    response = SLACK_WEB_CLIENT_USER.search_messages(query=text, sort='score', sor_dir='desc', count=resultCount, page=page) 
#    print ('search response: ', response)
    for match in response['messages']['matches']:
        results.append(match['permalink'])
    return results



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

    # Test Slack Search
    SALsays = constructSALReply('U5FGEALER', 'serverless', NUM_SEARCH_RESULTS, '')
    print("SALsays: ", SALsays)

    print("About to go threading!")
    event = {
        'text': 'What is lambda and serverless?', 
        'channel': 'test', 
        'ts': '1616474040.077300',
        'user': 'U5FGEALER'
        }
    handleAsynchSALResponse(event, 3)

