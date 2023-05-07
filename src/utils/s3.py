import requests
import boto3


def s3_upload_fileobj_by_url(
        source_url: str,
        s3_region: str,
        s3_bucket_name: str,
        s3_file_path: str,
        filename: str,
):
    # get raw object
    req = requests.get(source_url, stream=True)

    # init s3
    s3_session = boto3.Session()
    s3 = s3_session.resource('s3')
    s3_session_bucket = s3.Bucket(s3_bucket_name)

    # upload
    s3_url = f"{s3_file_path}/{filename}"
    s3_http_url = f"https://s3.{s3_region}.amazonaws.com/{s3_bucket_name}/{s3_file_path}/{filename}"

    s3_session_bucket.upload_fileobj(req.raw, s3_url)

    return s3_http_url
