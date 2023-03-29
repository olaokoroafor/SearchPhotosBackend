import json
import urllib.parse
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


REGION = 'us-east-1'
HOST = 'search-photos-x5jisq7uccul35xbr3bgyipk6a.us-east-1.es.amazonaws.com'
INDEX = 'photos'

s3 = boto3.client('s3')

def delete_documents():
    client = OpenSearch(hosts=[{'host': HOST, 'port': 443}],
        http_auth=get_awsauth(REGION, 'es'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)
    q = {
    "query": {
        "match_all": {}
    }
}
    res = client.search(index=INDEX, body=q)
    print("printing results")
    #print(res)
    hits = res['hits']['hits']
    results = []
    for hit in hits:
        id = hit['_id']
        val = client.delete(index=INDEX, id=id)
        print(val)
        

def index_photo(dict_object):
    print("trying connection")
    client = OpenSearch(hosts=[{'host': HOST,'port': 443}], http_auth=get_awsauth(REGION, 'es'), use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
    print("connection made")
    #delete_documents()
    
        
    response = client.index(index="photos", body=json.dumps(dict_object))
    print(response)
    
def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key, cred.secret_key, region, service, session_token=cred.token)

def get_labels(bucket, photo):
     session = boto3.Session()
     client = session.client('rekognition')

     response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},MaxLabels=50)

     return_labels = []
     for label in response['Labels']:
         return_labels.append(str(label['Name']).lower())

     return return_labels
     

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    print(event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    labels = []
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        head_response = s3.head_object(Bucket=bucket, Key=key)
        print(head_response)
        try:
            labels = head_response["ResponseMetadata"]["HTTPHeaders"]['x-amz-meta-customlabels'].split(",")
            print(labels)
        except Exception:
            print("no labels")
            pass
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
        
    rek_labels = get_labels(bucket, key)
    labels.extend(rek_labels)
    search_json = {}
    search_json["objectKey"] = key
    search_json["bucket"] = bucket
    search_json["createdTimestamp"] = event['Records'][0]['eventTime']
    search_json['labels'] = labels
    print(key, labels)
    index_photo(search_json)
