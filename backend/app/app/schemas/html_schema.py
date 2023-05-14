from pydantic import BaseModel

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