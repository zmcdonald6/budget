#Author: Zedaine McDonald

import boto3
import os
from datetime import datetime

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = "msgitbucket"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

def upload_to_s3(file, filename, user, filetype, year=None):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{filetype}/{year}_" if year else f"{filetype}/"
    key = f"{prefix}{user}_{now}_{filename}"

    s3.upload_fileobj(file, BUCKET_NAME, key)
    return key

def list_files_by_type(filetype):
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=f"{filetype}/")
    contents = response.get("Contents", [])
    return [obj["Key"] for obj in contents]

def get_file_from_s3(key):
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
    return obj["Body"].read()
