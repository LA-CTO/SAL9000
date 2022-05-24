# Main for commandline run and quick tests
# $env:GOOGLE_APPLICATION_CREDENTIALS="C:\code\SAL9000\sal9000-307923-dfcc8f474f83.json"

# Imports the Google Cloud client library
from google.cloud import language_v1

# Instantiates a client
client = language_v1.LanguageServiceClient()

TEST_STRINGS = [
    "Hi all - thank you @Lee Ditiangkin for the invite! I'm co-founder / GP of a new B2B-centric pre-seed and seed-stage fund called Garuda Ventures (garuda.vc). Previously was an early employee at Okta, where I was an early/founding member of all of our inorganic growth functions (M&A, BD, Ventures) -- and before that did a few other things back East in NYC/DC (law/finance/etc). Am based in the Bay Area, but we invest everywhere.\nExcited to meet and learn from technical leaders, operators, and entrepreneurs (and hopefully re-connect with some familiar faces :slightly_smiling_face:). Our portfolio companies are also always hiring. Feel free to reach out! Always up for a chat."
#    "Any recommendations for an easy to use no code platform to do mobile app POCs?  A non-technical friend wants to do some prototyping.  I'm looking at bubble.io, flutterflow.io, appgyver.com and appypie.com.  Ideally, I'd like her to start with something that can later be easily ported to a more permanent architecture if her ideas become viable.",
 #   "Morning Slackers - Anyone here using the enterprise version of https://readme.com/pricing . If so, how much are you paying? Any alternatives?",
 #   "Anyone used https://www.thoughtspot.com/ before or currently using it?"
#        "Okta not having a good morning:\nhttps://twitter.com/_MG_/status/1506109152665382920"
#        "Not sure where to post this: I'm looking for the recommendation of the dev shops that can absorb the product dev and support soup to nuts, preferably in LatAm, I've already reached out to EPAM, looking for more leads"
#        "This has been asked a few times on here already, but curious if anyone has developed any strong opinions since the last time it was asked. What has worked the best for your front end teams in E2E testing React Native apps? Appium? Detox?",
#        "I am looking for a good vendor who has integrations to all of the adtech systems out there to gather and normalize campaign performance data. Ideally, it would be a connector or api we can implement to aggregate campaign performance data.  Also, we have a data lake in S3 and Snowflake, if that helps. Please let me know if anyone knows of any good providers in this space.  Thx!!",    
#        "Can someone point me to feature flagging best practices? How do you name your feature flags? How do you ensure a configuration of flags is compatible?"
        ]

# The text to analyze
text = TEST_STRINGS[0]
document = language_v1.Document(
    content=text, type_=language_v1.Document.Type.PLAIN_TEXT
)

# Detects the sentiment of the text
sentiment = client.analyze_sentiment(
    request={"document": document}
).document_sentiment

print("Text: {}".format(text))
print("Sentiment: {}, {}".format(sentiment.score, sentiment.magnitude))

#analyze entities
response = client.analyze_entities(
    document=document,
    encoding_type='UTF32',
    )

for entity in response.entities:
#    print('=' * 20)
    print('         name: {0}'.format(entity.name))
#    print('         type: {0}'.format(entity.type))
#    print('     metadata: {0}'.format(entity.metadata))
#    print('     salience: {0}'.format(entity.salience))
#    print('     sentiment: {0}'.format(entity.sentiment))

# annotateText
"""
annotatedTextResponse = client.annotate_text(
    request={"document": document}
)

print("Text: {}".format(text))
print("AnnotateTextResponse: " + annotatedTextResponse)
"""