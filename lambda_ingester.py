import boto3
import csv
import datetime
import email
import email.policy
import json
import localstack_client.session
import os
import sys
import uuid
from urllib.parse import unquote_plus

dynamodb_client = boto3.client('dynamodb')
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

if os.environ['ENVIRONMENT'] == 'local':
    dynamo_clientdb = localstack_client.session.Session().client('dynamodb')
    s3_client = localstack_client.session.Session().client('s3')
    sqs_client = localstack_client.session.Session().client('sqs')

yearweek = datetime.date.today().strftime('%Y%U')
dynamo_table_name = f'an-sync-{yearweek}'

def lambda_handler(event, context):
    for record in event['Records']:

        # Fetch email from bucket
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        tmpkey = key.replace('/', '')
        download_path = f'/tmp/{uuid.uuid4()}{tmpkey}'
        print(f'bucket: {bucket} key: {key} download_path: {download_path}')
        s3_client.download_file(bucket, key, download_path)

        # Parse email and CSV attachment
        with open(download_path) as email_file:
            msg = email.message_from_file(email_file, policy=email.policy.default)

            if os.environ['DSA_KEY'] != msg.get('DsaKey'):
                print('DSA Key not found in email header, aborting.')
                return

            try:
                [attach] = [a for a in msg.iter_attachments() if a.get_content_type() == 'application/vnd.ms-excel']
            except(ValueError):
                # No CSV, something is wrong
                sys.exit(0)

            # Use dynamo to track progress between syncs
            init_db()

            csv_lines = attach.get_content().decode().splitlines()

            count = 0
            for row in csv.DictReader(csv_lines):
                d_row = dict(row)

                if not 'Email' in d_row:
                    # We can't continue processing without an email
                    pass

                sqs_client.send_message(
                    QueueUrl=os.environ['SQS_URL_INGESTED'],
                    MessageBody=json.dumps(d_row)
                )

                dynamo_clientdb.put_item(
                    TableName=dynamo_table_name,
                    Item={
                        'email': {'S': d_row['Email']},
                        'processed': {'BOOL': False}
                    }
                )

                count += 1

            print(f'Finished processing CSV ({count} rows).')

def init_db():
    try:
        dynamo_clientdb.create_table(
            TableName=dynamo_table_name,
            KeySchema=[
                {
                    'AttributeName': 'email',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        dynamo_clientdb.get_waiter('table_exists').wait(TableName=dynamo_table_name)
        print(f'Table created: {dynamo_table_name}')
    except dynamo_clientdb.exceptions.ResourceInUseException:
        print(f'Table already exists: {dynamo_table_name}')