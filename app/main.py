from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import boto3
import uuid
import os

app = FastAPI()

class HTMLInput(BaseModel):
    html: str

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name=os.environ['AWS_REGION']
)

bucket_name = 'astonishio-single-file'  # Replace with your own S3 bucket name

@app.post("/host-html")
async def host_html(request: Request):
    """
    Takes a raw HTML file as request input and hosts it online.
    """
    raw_html = await request.body()
    html_string = raw_html.decode("utf-8")
    # Generate a unique filename
    file_key = f"{uuid.uuid4()}.html"

    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=html_string,
            ContentType='text/html',
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload HTML content to S3: {str(e)}")


    # Return the hosted HTML file URL
    hosted_url = f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
    return JSONResponse(content={"url": hosted_url})

@app.get("/.well-known/ai-plugin.json", response_class=FileResponse)
async def get_plugin_manifest():
    return FileResponse("app/.well-known/ai-plugin.json")

