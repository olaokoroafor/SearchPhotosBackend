import json
from datetime import datetime
import boto3
import urllib.parse
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-photos-x5jisq7uccul35xbr3bgyipk6a.us-east-1.es.amazonaws.com'
INDEX = 'photos'
# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')

def search_domain(q):
    client = OpenSearch(hosts=[{'host': HOST, 'port': 443}],
        http_auth=get_awsauth(REGION, 'es'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)
    res = client.search(index=INDEX, body=q)
    print("printing results")
    print(res)
    hits = res['hits']['hits']
    results = []
    for hit in hits:
        results.append(hit['_source'])
    return results
    
def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key, cred.secret_key, region, service, session_token=cred.token)
    
    
def lambda_handler(event, context):
    # TODO implement
    response = {}

    print(event)
    print("hello")
    front_end_message =event["queryStringParameters"]["q"]# "show me people"#json.loads(event["body"])["messages"][0]
    print(front_end_message)
    try:
        interpretations = ask_bot(front_end_message)["interpretations"]
        key1 = None
        key2 = None
        for intent in interpretations:
            if intent["intent"]["name"] == "SearchIntent":
                slots = intent["intent"]["slots"]
                if slots["Keyword1"] is not None:
                    key1 = slots["Keyword1"]["value"]["resolvedValues"][0] if len(slots["Keyword1"]["value"]["resolvedValues"]) > 0 else slots["Keyword1"]["value"]["originalValue"]
                if slots["Keyword2"] is not None:
                    key2 = slots["Keyword2"]["value"]["resolvedValues"][0] if len(slots["Keyword2"]["value"]["resolvedValues"]) > 0 else slots["Keyword2"]["value"]["originalValue"]
                    
                break
            
        print("Keys: ", key1, key2)

    except Exception as e:
        str(e)
        
    search_terms = []
    if key1:
        search_terms.append(key1)
    if key2:
        search_terms.append(key2)
    
    photos = []
    if len(search_terms) > 0:
        clauses = []
        for term in search_terms:
            clauses.append({"term": {"tag":term}})
        query = {
                "bool": {
                "should": clauses
                    }
                }
        print(query)
        print("Search Results")
        query = {
                "query": {
                "terms" : { "labels" : search_terms}
                }
            
        } 
        
        results = search_domain(query)
        print(results)
        photos = []
        BASE_URL = "https://ooo2139-b2.s3.amazonaws.com/"
        for result in results:
            photos.append({"url":str(BASE_URL+result["objectKey"]), "labels":result["labels"]})
        search_response = {"results":photos}
    
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(search_response)
        }
    else:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({"results":[]})
        }

def ask_bot(msg_from_user):
    try:
        print(msg_from_user)
        # Initiate conversation with Lex
        lex_response = client.recognize_text(
            botId='5SDX8IILXL',
            botAliasId='TSTALIASID',
            localeId='en_US',
            sessionId='testuser',
            text=msg_from_user)
        print(lex_response)
            
        return lex_response
            
    except Exception as e:
        print(e)
        return None