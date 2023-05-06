from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import boto3
import uuid
import os
import stripe

class HtmlInput(BaseModel):
    """
    A request body model for the host-html and update-html endpoints.
    It takes a raw HTML file as input and returns a hosted HTML file URL.
    If used as an update it takes a UUID that represents the HTML file to update so it is {{uuid}}.html
    """
    html: str
    url: str | None
    
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
    Takes a raw HTML file as request input and hosts it online. IF the user also puts a UUID in the request body, it will update the corresponding file.
    """
    if html_input.url:
        html_string = html_input.html
        file_key = html_input.url.split("/")[-1]

        # Check if the object exists in the S3 bucket
        try:
            s3_client.head_object(Bucket=bucket_name, Key=file_key)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Object with UUID {file_key} not found in S3")

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
        
        return HtmlOutput(url=f"https://{bucket_name}.s3.amazonaws.com/{file_key}", detail="Your HTML file has been updated.")
        
    else:
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
            metadata={"url": hosted_url},
            cancel_url="https://astonishio.app",  # Replace with your own cancel URL
        )

        return HtmlOutput(url=session.url, detail="Please click the link for $10 to host your HTML file on Astonish.io.")

@app.delete("/delete-html")
async def delete_html(url: str):
    """
    Deletes a hosted HTML file.
    """
    file_key = url.split("/")[-1]

    # Check if the object exists in the S3 bucket
    try:
        s3_client.head_object(Bucket=bucket_name, Key=file_key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Object with UUID {file_key} not found in S3")

    # Delete the object
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete HTML content in S3: {str(e)}")

    return {"detail": f"HTML file with UUID {file_key} has been deleted."}

@app.get("/.well-known/ai-plugin.json", response_class=FileResponse)
async def get_plugin_manifest():
    return FileResponse("app/.well-known/ai-plugin.json")
