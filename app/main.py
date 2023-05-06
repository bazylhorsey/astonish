from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel
import boto3
import uuid
import os
import yaml
from fastapi.openapi.utils import get_openapi
import stripe
from uuid import UUID

class HtmlInput(BaseModel):
    """
    A request body model for the host-html and update-html endpoints.
    It takes a raw HTML file as input and returns a hosted HTML file URL.
    If used as an update it takes a UUID that represents the HTML file to update so it is {{uuid}}.html
    """
    html: str
    uuid: UUID | None
class HtmlOutput(BaseModel):
    """
    A response body model for the host-html endpoint.
    It returns a stripe checkout URL to pay for hosting the HTML file.
    """
    url: str
    detail: str

app = FastAPI(
    title="Astonish.io",
    description="Astonish.io is a platform for hosting and sharing interactive HTML files with ChatGPT.",
    version="0.1.0",
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name=os.environ['AWS_REGION']
)

stripe.api_key = os.environ['STRIPE_SECRET_KEY']
bucket_name = 'astonishio-single-file'

@app.post("/host-html")
async def host_html(html_input: HtmlInput) -> HtmlOutput:
    """
    Takes a raw HTML file as request input and hosts it online.
    """
    html_string = html_input.html
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

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": 1000,  # Set the price in cents (e.g., $10.00)
                "product_data": {
                    "name": "Astonish.io HTML Hosting",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=hosted_url,
        cancel_url="https://astonishio.app",  # Replace with your own cancel URL
    )

    # return RedirectResponse(url=session.url, status_code=303)
    return HtmlOutput(url=session.url, detail="Please click the link for $10 to host your HTML file.")
    
@app.put("/update-html")
async def update_html(html_input: HtmlInput):
    """
    Takes a raw HTML file and a UUID as request input and updates the corresponding S3 object.
    """
    html_string = html_input.html
    file_key = f"{html_input.uuid}.html"

    # Check if the object exists in the S3 bucket
    try:
        s3_client.head_object(Bucket=bucket_name, Key=file_key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Object with UUID {html_input.uuid} not found in S3")

    # Update the object with the new HTML content
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=html_string,
            ContentType='text/html',
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update HTML content in S3: {str(e)}")

    # Return the updated hosted HTML file URL
    hosted_url = f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
    return JSONResponse(content={"url": hosted_url})

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Astonish.io",
        version="0.1.0",
        description="An API for hosting and sharing interactive HTML files with ChatGPT.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

@app.get("/openapi.yaml", response_class=PlainTextResponse)
async def get_openapi_yaml():
    openapi_schema = custom_openapi()
    openapi_yaml = yaml.safe_dump(openapi_schema)
    return openapi_yaml

@app.get("/.well-known/ai-plugin.json", response_class=FileResponse)
async def get_plugin_manifest():
    return FileResponse("app/.well-known/ai-plugin.json")

@app.get("/health")
async def health_check():
    return "OK"