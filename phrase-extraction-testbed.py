# html-to-freq-2.py https://programminghistorian.org/en/lessons/counting-frequencies
# RAKE howto: https://towardsdatascience.com/extracting-keyphrases-from-text-rake-and-gensim-in-python-eefd0fad582f


import urllib.request, urllib.error, urllib.parse
import json
import os
import RAKE
import re
import textrazor


import gspread
from datetime import datetime

# The ID and range of a sample spreadsheet.
GSHEET_CREDENTIALS = "d:/code/Etrade_Python/etrade_python_client/stockaccounts-ef30787c0d2c.json"
SLACKER_STOPWORDS_SPREADSHEET_ID = '1TpJQA_M6Ff9YLTZ4WlRFTlbuDa-s0qD9v2RHRHkpg4M'
STOPWORDS_URL = 'http://ir.dcs.gla.ac.uk/resources/linguistic_utils/stop_words'
JSON_FILE_ROOT_DIR = 'd:\\slackers-archive\\'
#JSON_FILE_DIRS_ARRAY = ['techandtools', 'ai-blockchain-ar-vr', 'announcements', 'architecture-and-budget-review', 'conways-law', 'events', 'kubernetes', 'opportunity-hiring', 'random', 'slacker-angels', 'startups', 'wolves-of-wall-street-3', 'women-in-tech']
JSON_FILE_DIRS_ARRAY = ['techandtools']
TEST_STRING = "StackOverflow Teams offer a free tier for 50 users.  Too bad we’ve got too many members (750) to make the switch, but for you small startups you can set up an internal StackOverflow for free: <https:\/\/techcrunch.com\/2021\/03\/17\/stack-overflow-adds-a-free-tier-to-its-fast-growing-teams-service\/|https:\/\/techcrunch.com\/2021\/03\/17\/stack-overflow-adds-a-free-tier-to-its-fast-growing-teams-service\/>"
# textrazor api key
textrazor.api_key = "3d8ebf5664cb85a14bd5a2a04c11e53603a89595304d7eb84098929f"

# Given a list of words, remove any that are
# in a list of stop words.

def removeStopwords(wordlist, stopwords):
    return [w for w in wordlist if w not in stopwords]

# Given a list of words, return a dictionary of
# word-frequency pairs.

def wordListToFreqDict(wordlist):
    wordfreq = [wordlist.count(p) for p in wordlist]
    return dict(list(zip(wordlist,wordfreq)))

# Sort a dictionary of word-frequency pairs in
# order of descending frequency.

def sortFreqDict(freqdict):
    aux = [(freqdict[key], key) for key in freqdict]
    aux.sort()
    aux.reverse()
    return aux

def basicCleanse(text, stopWords):
#    print('starting basicKeywordExtraction Stripping')
#strip URL and tags and tolower
#    print('raw text:', text)
    text = stripURLs(text)
#    print('stripURL text:', text)
    text = stripHTMLTags(text)
#    print('stripHTML text:', text)
    text = text.lower()
    text = stripSlackUserID(text)
#    print('stripped text:', text)
#    print('splitting nonAlphaNum delims to array')
    splitArray = splitNonAlphaNum(text)
#    print('splitNonAlphaNum after:', splitArray)
    return splitArray

def basicKeywordExtraction(text, stopWords):
    wordlist = basicCleanse(text, stopWords)
    wordlist = removeStopwords(wordlist, slacker_stopwords)
#    print("removed Stopwords after num: ", len(wordlist))
#    print("removed Stopwords after: ", wordlist)


    print("wordListToFreqDict...")
    dictionary = wordListToFreqDict(wordlist)
    print("sortFreqDict...")
    sorteddict = sortFreqDict(dictionary)
    return sorteddict

# stopwords = str(urllib.request.urlopen(STOPWORDS_URL).read())
# stopwords += str(slacker_stopwords).lower()

# Given a text string, remove all non-alphanumeric
# characters (using Unicode definition of alphanumeric).
def stripNonAlphaNum(text):
    clean = re.compile(r'\W+', re.UNICODE)
    return re.sub(clean, ' ', text)

# Given a text string, split all non-alphanumeric 
# characters (using Unicode definition of alphanumeric) return as array to alphaNum tokens
def splitNonAlphaNum(text):
    return re.compile(r'\W+', re.UNICODE).split(text)

# Remove all URLS
def stripURLs(textString):
    return re.sub(r'http\S+', '', textString)
#    return re.sub(r'^https?:\/\/.*[\r\n]*', '', textString, flags=re.MULTILINE)

# Remove all html tags
def stripHTMLTags(textString):
    return re.sub(r'<.*?>', '', textString)


# Is Slack user id - start with 'u' and contains number
def stripSlackUserID(textString):
    return re.sub(r'u\d', '', textString)

def RAKEPhraseExtraction(stringArray, stopWords):
    print("About to RAKE with num stopwords:", len(stopWords))
    rakeObject = RAKE.Rake(stopWords)
    return rakeObject.run(stringArray)
#    return rakeObject.run(TEST_RAKE_STRING)


# Return reverse order tuple of 2nd element
def sortTuple(tup):
    # key is set to sort using second elemnet of
    # sublist lambda has been used
    tup.sort(key = lambda x: x[1])
    tup.reverse()
    return tup

# Return the top weighed Phrase from RAKE of stringArray
def extractTopPhraseRAKE(stringArray, stopwords):
    raked = RAKEPhraseExtraction(stringArray, stopwords)
    print("Raked results: ", raked)
    sorteddict = sortTuple(raked)[-10:]
    if sorteddict[0]: 
        return sorteddict[0][0]
    return ''


# Use TextRazer to Analyze a textString
def analyzeTextRazer(textString):
    print("About to call TextRazor for: " + textString)
    client = textrazor.TextRazor(extractors=["entities", "topics"])
    response = client.analyze(textString)
    for entity in response.entities():
        print(entity.id, entity.relevance_score, entity.confidence_score, entity.freebase_types) 


gc = gspread.service_account(filename=GSHEET_CREDENTIALS)
sh = gc.open_by_key(SLACKER_STOPWORDS_SPREADSHEET_ID)
worksheet1 = sh.worksheet('stopwords')
slacker_stopwords = worksheet1.col_values(1)
worksheet1 = sh.worksheet('stopwords0')
boring_stopwords = worksheet1.col_values(1)
# print('stopwords: ', slacker_stopwords)
print('number of slacker stopwords: ', len(slacker_stopwords))
print('number of boring stopwords: ', len(boring_stopwords))

# Call TextRazer API
#analyzeTextRazer(TEST_STRING)
#raked = extractTopPhraseRAKE(TEST_STRING, boring_stopwords)
#print('raked after:', raked)



all_messages = ''
all_tup_list = []
num_messages = 0
num_phrases = 0

#RAKE_OBJECT = RAKE.Rake(RAKE.SmartStopList()) slacker_stopwords
RAKE_OBJECT = RAKE.Rake(slacker_stopwords)
# Initializing Dictionary
urlCounter = {}
keyPhraseCounter = {}
userMessageCounter = {}
userKeyPhraseCounter = {}

for channel_dir in JSON_FILE_DIRS_ARRAY:
    channel_dir = JSON_FILE_ROOT_DIR + channel_dir + "\\"
    print("Processing dir: ", channel_dir)

    textcounter=0

    for json_file in os.listdir(channel_dir):
        json_file = channel_dir + json_file
#        print("Processing file: ", json_file)
        with open(json_file, encoding="utf-8") as f:
            json_data = json.load(f)

        # pretty_json = json.dumps(json_data, indent = 4, sort_keys=True)
        #print(pretty_json)

        for this_json in json_data:
            if this_json.get('type') != "message":
                continue
            if 'bot_id' in this_json:
#                print(this_json.get('bot_id') + " is a bot!")
                continue
            if 'subtype' in this_json:
                subtype = this_json.get('subtype')
                if "channel_join" == subtype:
                    continue
#                print("subtype: ", subtype)
#            print('this_json:', this_json)
            this_text = this_json.get('text')
#            print("this_text: ", this_text)
            if not this_text:
                continue

            textcounter+=1
            thisUser = this_json.get('user')
            userMessageCounter[thisUser] = userMessageCounter.get(thisUser, 0) + 1

#            print('thisUser: ', thisUser)
#            print("this_text:", this_text)
            urlre = 'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
            urls = re.findall(urlre , this_text)
            for url in urls:
                url = url.split("?")[0]
                url = url.split("//")[1]
                urlCounter[url] = urlCounter.get(url, 0) + 1

#            this_text = re.sub(r'^https?:\/\/.*[\r\n]*', '', this_text)
            this_text = re.sub(r'<?http\S+', '', this_text)
#            print("all urls: ", urls)
#            print("stripped url text: ", this_text)

#CLEANSE
#            this_text = stripHTMLTags(this_text)
#            this_text = this_text.lower()
#            this_text = stripSlackUserID(this_text)

            rakedTuple = RAKE_OBJECT.run(this_text, minCharacters = 2)
#            print('rakedTuple:', rakedTuple)
            for thisTuple in rakedTuple:
                keyphrase = thisTuple[0]
                keyPhraseCounter[keyphrase] = keyPhraseCounter.get(keyphrase, 0) + 1

print("textcounter: ", textcounter)

urlCounter = sorted(urlCounter.items(), key = lambda x: x[1], reverse = True)
print("url count: ", len(urlCounter))

keyPhraseCounter = sorted(keyPhraseCounter.items(), key = lambda x: x[1], reverse = True)
#print("keyphrase count: ", keyPhraseCounter)
print("keyphrase count: ", len(keyPhraseCounter))

userMessageCounter = sorted(userMessageCounter.items(), key = lambda x: x[1], reverse = True)
print("user message count: ", len(userMessageCounter))

count=0
for keyPhrase in keyPhraseCounter:
    print(keyPhrase[0] + ":" + str(keyPhrase[1]))
    count+=1
    if count > 40:
        break



"""
            cleaned_this_text_array = basicCleanse(this_text)


            cleaned_this_text = ' '.join(cleaned_this_text_array)
            print('cleaned_this_text: ', cleaned_this_text)
            cleaned_sorteddict = sortTuple(RAKEPhraseExtraction(cleaned_this_text))[-10:]
            print('cleaned_this_text keywords: ', cleaned_sorteddict)

            all_messages += '\n' + this_text
            num_messages +=1

sorteddict = basicKeywordExtraction(all_messages)

#raked = RAKEPhraseExtraction(all_messages, boring_stopwords)
#print('raked after:', raked)

#all_raked_string = ''
#for this_tup in raked:
#    print("this_tup: ", this_tup)
#    all_tup_list += [this_tup[0]]
#    num_phrases +=1
#print("Number of messages: ",  num_messages)
#print("Number of phrases: ",  num_phrases)
#print("all_tup_list: ", all_tup_list)


# RAKE phraseword extraction
#sorteddict = sortTuple(RAKEPhraseExtraction(TEST_STRING, slacker_stopwords))[-10:]
#sorteddict = sortTuple(RAKEPhraseExtraction(all_messages, slacker_stopwords))[-1000:]

#print(sorteddict)

# basic keyword extraction
#sorteddict = basicKeywordExtraction(all_messages, slacker_stopwords)

print("dumping histogram to file...")
with open('histogram.txt', 'w') as outfile:
    for s in sorteddict: 
        print(str(s), file=outfile)
"""
