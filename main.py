# RAKE https://github.com/fabianvf/python-rake
# howto: https://towardsdatascience.com/extracting-keyphrases-from-text-rake-and-gensim-in-python-eefd0fad582f
# 
# Deployed to Google CLoud local - run from repo root dir:
# gcloud functions deploy keyphaseExtraction --project=sal9000-307923 --source=https://source.cloud.google.com/sal9000-307923/github_genechuang_sal9000/+/main --runtime=python39 --trigger-http

# Deployed to Google Cloud Function url: https://us-west2-stockaccounts.cloudfunctions.net/KeyPhraseExtract?message=test

import RAKE
from rake_nltk import Rake
import spacy
import pytextrank

TEST_STRINGS = [
    "Anyone here use Copper CRM at their company? I’m working with two sales consultants (one is used to Salesforce and the other is used to Hubspot). I personally liked Copper cause it sits on top of Gmail. I’d rather use what the salespeople want to use, but in this case there’s no consensus lol.",
    "Are there any opinions on accounting systems / ERP's? We're using SAP Business One (aka Baby SAP) and need to upgrade to something a bit more full featured. Personally I find the SAP consulting ecosystem rather abysmal in terms of talent, looking at netsuite as an alternative but curious to know what others are using / we should be looking at."
    ]

#TEST_STRING = "erp"

STOPWORDS_LIST=RAKE.SmartStopList()
#print("Initializing RAKE with SmartStopList size:", len(STOPWORDS_LIST))
RAKE_OBJECT = RAKE.Rake(RAKE.SmartStopList())

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
        return str(sortedtuple)
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
    return keyPhrases

if __name__ == "__main__":
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
