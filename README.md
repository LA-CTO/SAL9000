# SAL9000

12/5/2022 UPDATE
With the recent buzz in OpenAI GPTChat, I just 'upgraded' @SAL 9001  from "Marvin the Sarcastic Chatbot on curie-1 engine" to GPTChat on davince-3 engine.  SAL is already a member in a few channels like #announcements #techandtools #sall-e and will automatically respond to all top posts.  If you @mention SAL in a thread on any channel you can also trigger a response. If your prompt starts with "@SAL 9001 draw me" you will trigger DALL-E.  Finally you can chat directly with @SAL 9001  for private GPTChat or DALL-E.  Davinci engine costs 10x more than Curie engine, so I set a OpenAI budget and SAL will be disabled if we go above budget.  Enjoy your new AI overlord!

SAL 9000 became sentient on March 16 2021 on CTO Slackers.

SAL upgraded from RAKE to OpenAI GPT Token parsing in Q1 2022

RAKE https://github.com/fabianvf/python-rake
howto: https://towardsdatascience.com/extracting-keyphrases-from-text-rake-and-gensim-in-python-eefd0fad582f
 
Deployed to Google CLoud local - run from repo root dir:
gcloud functions deploy handleEvent --runtime python39 --trigger-http --allow-unauthenticated --project=sal9000-307923 --region=us-west2

3/16/21: @here Slackers: I created the SAL 9000 slackbot using Zapier + python_rake in Google Cloud Function REST API  - Ask any question in this #techandtools channel, it will pull 1st most relevant result from Slack search of key phrase in #techandtools.  

3/10/22: I just redeployed @SAL 9001 - For keyword extraction, I replaced RAKE with OpenAI Completion (thx @Helin Cao for the tip), so now SAL should be smarter with extracting most relevant keywords from your question to search against Slack archive.  OpenAI also does not provide keyword weights, so you won't see numbers in parenthesis in the search button labels anymore. For those interested in my gnarly python GCP Cloud Function code to build SAL: https://github.com/genechuang/SAL9000/blob/main/main.py

TODO/WishList for SAL 9000 (feel free to add requests/bugs by replying to this post):
1. Build a simple keyword extraction function in Python Done: I used this word count example and generated a Slackers word histogram here
2. Research @paulsri suggestions for key phrase extraction: a. RAKE b. pke c. PyTextRank     SEMI-DONE: built python function with python-rake
3. Make RESTful API of KeywordExtraction and deploy in cloud DONE:  Use flask to wrap RAKEKeyPhraseExtraction and deployed to GCP
4. Create SlackBot using Zapier for now DONE: @SAL 9001 
5. Make SAL answer in thread DONE: Zap Send Channel Message in Slack has a Thread field
6. SAL should only reply to top level posts, not to comments in thread.  Not sure if Zapier can control this, will have to build a SALBot Google Cloud Function to get that level of control on type of Slack event that will trigger a webhook call to SAL. Done: Zapier has a Filter Zap and I need to check Slack message thread_ts doesn't exist or ts = thread_ts: 
7. Create clone HAL 9000, launch SAL 9000 to #techandtools and keep HAL 9000 in #test to iterate and improve search recall, relevancy, and query processing.  DONE: HAL 9000 is born and sits in #test, SAL 9000 is launched to #techandtools 
8. Look at Slack chatbot tutorial to build a standalone Slack bot and not rely on Zapier. DONE:  SAL 9001 is 100% on GCP Python Function!  Added slack_sdk and implemented WebClient.search_messages, WebClient.users_info and WebClient.chat_postMessage  
9. Return more than 1 search result (Zapier Slack Search doesn't seem to return or expose  more than 1 result row - I may have to build a SALBot Function to hit Slack Search API directly. DONE: SAL 9001 can configure number of search results returned
10. Provide more than 1 keyphrase extraction - Right now I'm returning only the top scored key phrase extraction from python-RAKE - I can return the full weighted list and either show the top N results and run N Slack queries, OR have a interactive menu of key phrase choice:  Hey Slacker do you mean "key phrase A", "key Phrase B", or "key Phrase C"? PARTIALLY DONE: SAL 9001 will show multiple keyphrases, but still need to use Slack Blockkit
11. Add GCP Secrets Manager so I can secure SLACK_BOT_TOKEN and SLACK_USER_TOKEN and check code into github. DONE!
12. Allow keyphrase extraction relevancy feedback:  "Did I do a good job guessing what you mean?  Yes/No" Or even "If I didn't not guess what you mean, what DID you mean to ask?  Please enter subject/topic:" - Then feed this back into ML database, and try other algorithms like rake-nltk or 3rd party services like  TextRazor.com and GetGuru.com
13. Eventually move out of Zapier workflow (which was easy to set up and don't have to deal with Slack App/API development with tokens and authorizations mess) and into Cloud Function Slack Bot in Python, where I have full control on input, output, filtering, etc.
14. Eventually index the entire Slacker history on ElasticSearch - then we don't have to rely on Slack Search API, and can optimize our own search relevancy, results set, create topics/categorizes/facets, and build knowledgebase topic pages.
15. Depluralize/Normalize: headless CMSs -> headless CMS
16. Look into Duolingo open sourced Metasearch from @Duc Chau
17. 3/10/22 Added OpenAI for extraction, replacing RAKE
