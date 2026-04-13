"""
Uploads profile pictures to AWS S3.
"""

import boto3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET = os.getenv('AWS_S3_BUCKET')
REGION = os.getenv('AWS_REGION')

def upload_profile_pic_influencer(username: str, image_url: str) -> str:
    """
    Downloads profile pic from Instagram URL,
    uploads to S3, returns the public URL.
    """
    # Download the image
    response = requests.get(image_url)
    if response.status_code != 200:
        return None

    # Upload to S3
    key = f"profile-pics/{username}.jpg" 
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=response.content,
        ContentType='image/jpeg'
    )

    # Return the public URL
    public_url = f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}"
    return public_url

def upload_profile_pic_brand(username: str, image_url: str) -> str:
    """
    Downloads profile pic from Instagram URL,
    uploads to S3, returns the public URL.
    """
    # Download the image
    response = requests.get(image_url)
    if response.status_code != 200:
        return None

    # Upload to S3
    key = f"brand-profile-pics/{username}.jpg" 
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=response.content,
        ContentType='image/jpeg'
    )

    # Return the public URL
    public_url = f"https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}"
    return public_url

