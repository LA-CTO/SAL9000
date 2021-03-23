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

import RAKE
from rake_nltk import Rake
import spacy
import pytextrank
import requests
from google.cloud import secretmanager
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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
SLACK_BLOCK_KIT = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Danny Torrence left the following review for your property:"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://example.com|Overlook Hotel> \n :star: \n Doors had too many axe holes, guest in room " +
                    "237 was far too rowdy, whole place felt stuck in the 1920s."
            },
            "accessory": {
                "type": "image",
                "image_url": "https://images.pexels.com/photos/750319/pexels-photo-750319.jpeg",
                "alt_text": "Haunted hotel image"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Average Rating*\n1.0"
                }
            ]
        }
    ]

#For Slack Search API: https://api.slack.com/methods/search.messages
SLACK_SEARCH_URL = 'https://slack.com/api/search.messages'

#TEST_STRINGS = [
#    "Anyone here use Copper CRM at their company? I’m working with two sales consultants (one is used to Salesforce and the other is used to Hubspot). I personally liked Copper cause it sits on top of Gmail. I’d rather use what the salespeople want to use, but in this case there’s no consensus lol.",
#    "Are there any opinions on accounting systems / ERP's? We're using SAP Business One (aka Baby SAP) and need to upgrade to something a bit more full featured. Personally I find the SAP consulting ecosystem rather abysmal in terms of talent, looking at netsuite as an alternative but curious to know what others are using / we should be looking at."
#    ]

TEST_STRINGS = ["What is serverless?"]

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
        print("processing event: ", event)
        if 'thread_ts' in event:
            print('This is a thread message so not responding to it')
            return 'SAL 9001 not responding to thread message'
        if 'bot_id' in event:
            print('This is a bot message so not responding to it')
            return 'SAL 9001 not responding to bot message'
        if 'text' in event:
            text = event['text']
            channel_id = event['channel']
            ts = event['ts']
            user = event['user']

            rtnStr = constructSALReply(user, text, 3)

            response = postMessageToSlackChannel(channel_id, ts, rtnStr)
            return 'SAL 9001 responded!'
    return 'SAL 9001 is ok?'    


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

# This method will construct the entire SAL 9001 Response, may be Boxkit
def constructSALReply(user, text, resultCount):
    extractedKeyPhrases = extractTopPhrasesRAKE(text, 1)
    count = 0
    print('who is ', user)
    whoami = SLACK_WEB_CLIENT_BOT.users_info(user=user)
    print('whoami is ', whoami)
    username = whoami['user']['name'];
    print('username is ', username)
    if(len(extractedKeyPhrases) < 0):
        return "Hello @" + username + " I don't know what you want"

    returnStr="Hello @" + username +" I think you meant " + str(extractedKeyPhrases) + ", results:\n"
#    print('Extracted key phrases: ', extractedKeyPhrases)
    for keyPhraseTuple in extractedKeyPhrases:
        keyPhrase = keyPhraseTuple[0]
#        print('Gonna search this keyphrase:', keyPhrase)
        searchResults = searchSlackMessages(keyPhrase, resultCount, 1)
        for searchResult in searchResults:
            returnStr += searchResult + '\n'
        count = count + 1
        print('count is now:', count)
        if count >= 3:
            break
    return returnStr


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
    print ('search response: ', response)
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

#        extractmeurl = ENDPOINT_URL + extractme
#        print("calling url: ", extractmeurl)
#        response = requests.get(extractmeurl)
#        print("response: ", response.content)

    #postMessageToSlackChannel('test', '', 'Hello from SAL 9001! :tada:')        

    # Test Slack Search
    SALsays = constructSALReply('U5FGEALER', 'serverless', 10)
    print(SALsays)


