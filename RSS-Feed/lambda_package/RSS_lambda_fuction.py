"""
Author - Rob Zabel
An AWS Lambda function that scrapes RSS feeds and delivers the latest articles to an IM webhook
"""
import os
import urllib3
import json
import boto3
import feedparser
import time 



def load_titles():
    """
    Grabs the article titels from S3
    """ 
    #Use the Boto3 client to interact with S3
    s3 = boto3.client('s3')
    bucket_name = os.getenv('S3_BUCKET')
    object_key = os.getenv('S3_BUCKET_OBJECT')

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        variable = response['Body'].read().decode('utf-8')
    
    except s3.exceptions.NoSuchKey:
        print("No Articles available")
    
    #Change the string to a dict
    articles = eval(variable)
    return articles
 
 
def save_titles(titles):
    """
    writes the article titles to S3
    """ 
    #Use the Boto3 client to interact with S3
    s3 = boto3.client('s3')
    bucket_name = os.getenv('S3_BUCKET')
    object_key = os.getenv('S3_BUCKET_OBJECT')

    #save the latest titles
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=str(titles).encode('utf-8')) 
    

def check_titles(last_collected_title, list):
    """
    Checks if the latest title is still in the response after the weekend 
    """
    for dictionary in list:
        if last_collected_title == dictionary['title']:
            return last_collected_title
        else:
            no_title = True
    if no_title:
        last_collected_title = list[0]['title']
        return last_collected_title


def webex_message(article):
    """
    Takes the article, formats the message then sends it to webex
    """
    # The API Endpoint for webex
    api_endpoint = os.getenv('API_ENDPOINT')#create message endpoint
    access_token = os.environ.get('WebexSecureEndpointBotToken') #secure endpoint bot access token
    
    # Set the headers for the request and provide access token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
        }
    room_id = os.environ.get('WebexRoomID') # Webex room ID
   
   
    TITLE = article.get('title') or "Unavailable"
    LINK = article.get('link') or "Unavailable"
    DATE = article.get('published') or "Unavailable"
    SUMMARY = article.get('summary') or "Unavailable"
    WEBSITE = article.get('title_detail')['base'] or "Unavailable"
    match WEBSITE:
        case "https://www.bleepingcomputer.com/feed/":
            WEBSITE = "Bleeping Computer"
        case  "https://feeds.feedburner.com/TheHackersNews":
            WEBSITE = "The Hacker News"
        case "https://www.crowdstrike.com/blog/feed":
            WEBSITE = "CrowdStrike"        
        case "https://digital.nhs.uk/feed/cyber-alerts-feed.xml":
            WEBSITE = "NHS Cyber Alerts"
    
    MESSAGE = f"""***New Article reported by {WEBSITE}***\
    \n{TITLE}\
    \n{DATE}\
    \n{SUMMARY}\
    \n{LINK}\n"""

    # Create the payload for the Webex API request
    payload = {
        'roomId': room_id,
        'text': MESSAGE
    }

    # Create a PoolManager object from urllib3
    http = urllib3.PoolManager()

    # Send the POST request with the data and headers
    response = http.request('POST', api_endpoint, body=json.dumps(payload), headers=headers)

    # Print the response from the webhook
    print(response.status)


def get_feeds():
    """
    Scrapes the RSS endpoints for the latest feeds
    """
    # RSS Feed outlet and endpoint
    RSS_FEEDS = {
        "CrowdStrike":"https://www.crowdstrike.com/blog/feed", 
        "TheHackerNews": "https://feeds.feedburner.com/TheHackersNews",
        "BleepingComputer": "https://www.bleepingcomputer.com/feed/", 
        "NHS Cyber Alerts": "https://digital.nhs.uk/feed/cyber-alerts-feed.xml"
        }

   
    #Cycle through the Feeds
    for feed in RSS_FEEDS:
        #Get the URL of the Feed
        URL = RSS_FEEDS[feed]
        #attempt to get the feeds and send them to webex
        last_collected_title = load_titles() #load the current latest title for comparrison
        
        try:    
            news_feed = feedparser.parse(URL) #use the feedparser module to grab the formatted feeds
            articles = news_feed.entries #create a dictionary of the articles
            latest_title = articles[0]['title']#grab the latest article title
            validated_last_title = check_titles(last_collected_title[feed], articles)#load the current latest title for comparrison
                
            if latest_title == validated_last_title: #check if any new articles are published
                print("No new Articles")
            else:
                for article in articles: 
                    if article['title'] != validated_last_title: #cycle through the list of articles until you get to one you have seen before
                        webex_message(article)#send the article to webex
                        time.sleep(2)
                    else:
                        last_collected_title[feed] = latest_title #update the latest article title
                        print("All caught up")
                        break #break out of the loop and onto the next feed
            last_collected_title[feed] = latest_title #update the latest article title
            save_titles(last_collected_title) #save the articles file to s3
        except Exception as e:
            print(f"An error occurred: {e}")
            
            
def lambda_handler(event, context):

    # Start scraping feeds
    get_feeds()