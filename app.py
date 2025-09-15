import os
import boto3
from flask import Flask, render_template, request
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
s3 = boto3.client('s3')

app = Flask(__name__)

# Generate url used to display image. Expires in an hour
def create_presigned_url(bucket_name, key, expiration=3600):
    try:
        response = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        print(e)

# Given a category, returns a list of urls
def get_images(category: str):
    rows = supabase.table("images").select("object_key", "caption").eq("category", category).execute()
    data = rows.data
    urls = [{"url": create_presigned_url("smerfmc", d["object_key"]), "caption": d["caption"]} for d in data]
    return urls

# Given a category, returns a description
def get_description(category: str):
    rows = supabase.table("categories").select("categoryDescription").eq("categoryName", category).execute()
    data = rows.data
    print(data)
    description = data[0]['categoryDescription']
    print(description)
    return description

# Get all categories
def get_categories():
    rows = supabase.table("categories").select("categoryName").execute()
    data = rows.data
    names = [d['categoryName'] for d in data]
    return names

# home page by default displays the first category listed in the database
@app.route("/")
def index():
    categories = get_categories()
    urls = get_images(categories[0])
    description = get_description(categories[0])
    return render_template('index.html', urls = urls, description = description, categories = categories)

# If user changes category, displays images under that category
# Uses hidden input (form)
@app.route("/choose", methods=["POST"])
def choose():
    print(request.form)
    category = request.form.get("category")
    print(category)

    urls = get_images(category)
    description = get_description(category)
    categories = get_categories()
    return render_template('index.html', urls = urls, description = description, categories = categories)

if __name__ == "__main__":
    app.run(debug=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)