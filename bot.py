import os, io, uuid
import discord
import boto3
from botocore.exceptions import ClientError
from discord.ext import commands
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from discord import app_commands
from supabase import create_client, Client

load_dotenv()
# Discord variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
# databse variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

s3 = boto3.client('s3')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

def gen_s3_obj_key(category, filename):
    # format: category/uuid.ext
    gen_uuid = uuid.uuid4().hex # generate a uuid and take out the dashes
    ext = os.path.splitext(filename)[1] # 0th index is file name, 1st index is the extention
    return f"{category}/{gen_uuid}{ext}"

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

def get_category_names():
    # select all category names
    data = supabase.table("categories").select("categoryName").order("categoryName").execute()
    names = [d["categoryName"] for d in data.data]
    return names

def get_descriptions():
    # select all category names
    data = supabase.table("categories").select("categoryDescription").order("categoryName").execute()
    descriptions = [d["categoryDescription"] for d in data.data]
    return descriptions

def supa_insert(table_name: str, row: Dict[str, Any]):
    data = (
        supabase.table(f"{table_name}")
        .insert(row)
        .execute()
    )
    return data

async def autocomplete_categories(interaction: discord.Interaction, current: str):
    # users can choose a category that's properly capitalized from dropdown list
    categories = get_category_names()
    return [
        app_commands.Choice(name=category, value=category)
        for category in categories if current.lower() in category.lower()
    ]

@bot.event
async def on_ready():
    try:
        print("Local tree before sync:", [c.name for c in bot.tree.get_commands()])
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands: {[c.name for c in synced]}")
        print(f"{bot.user} is ready!")
    except Exception as e:
        print(e)

# troll command :)
@app_commands.guilds(GUILD_ID)
@bot.tree.command(name="bahh")
async def bahh(interaction: discord.Interaction):
    await interaction.response.send_message(f"moooo") 

# display existing categories 
@app_commands.guilds(GUILD_ID)
@bot.tree.command(name="view_categories", description="View existing categories")
async def view_categories(interaction: discord.Interaction):
    names = get_category_names()
    descriptions = get_descriptions() 
    if names: # bullet point
        result = "\n".join(
                f"• **{name}** - {desc}" 
                for name, desc in zip(names, descriptions))
    else:
        result = "No categories found."

    await interaction.response.send_message(f"{result}", ephemeral=True)

# users must create a category before uploading images to it
@app_commands.guilds(GUILD_ID)
@bot.tree.command(name="create_category")
async def create_category(interaction: discord.Interaction, 
                       category_name: str, 
                       category_description: Optional[str] = None):
    try:
        # check if it already exists in the database, check for lowercase because categories shouldn't have to be that similarly named
        names = get_category_names()
        lower_names = [name.lower() for name in names]
        if category_name.lower() in lower_names:
            await interaction.response.send_message(f"Category already exists!", ephemeral=True)
            return
        
        data = supa_insert("categories", {
                "categoryName" : category_name,
                "categoryDescription": category_description,
                })
        
        if len(data.data) > 0: # if it added something, data.data will be a list
            await interaction.response.send_message(f"Category added successfully.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Unable to add category. Please try again.", ephemeral=True)
    except Exception as e:
        print(f"Error while adding category: {e}")
        await interaction.response.send_message(f"Unable to add category. Please try again.", ephemeral=True)

# change category name
@app_commands.guilds(GUILD_ID)
@app_commands.autocomplete(old_category_name=autocomplete_categories)
@bot.tree.command(name="change_category_name", description="Change an existing category name. Case sensitive.")
async def change_category_name(interaction: discord.Interaction, 
                        old_category_name: str,
                        new_category_name: str):
    try:
        # update the name in the categories table
        data = (supabase.table("categories")
                .update({"categoryName": new_category_name})
                .eq("categoryName", old_category_name)).execute()
        
        # update the images under that category too
        response = (supabase.table("images")
            .select("category")
            .eq("category", old_category_name)).execute()
        old_cat_images = response.data

        for o in old_cat_images:
            new_data = (supabase.table("images")
                .update({"category" : new_category_name})
                .eq("category", old_category_name)).execute()

        await interaction.response.send_message(f"{old_category_name} successfully changed to {new_category_name}", ephemeral=True)
    except Exception as e:
        print(f"Error while editing category name: {e}")
        await interaction.response.send_message(f"Unable to edit category name. Reminder: This command is case sensitive. Check existing names with /view_categories.", ephemeral=True)

# Change category description
@app_commands.guilds(GUILD_ID)
@app_commands.autocomplete(category=autocomplete_categories)
@bot.tree.command(name="change_category_description", description="Change an existing category description. Category name is case sensitive.")
async def change_category_desc(interaction: discord.Interaction, 
                        category: str,
                        new_description: str):
    try:
        data = (supabase.table("categories")
                .update({"categoryDescription": new_description})
                .eq("categoryName", category)).execute()
        await interaction.response.send_message(f"Succesfully updated {category}'s description.", ephemeral=True)
    except Exception as e:
        print(f"Error while editing category name: {e}")
        await interaction.response.send_message(f"Unable to edit category description. Reminder: Category name case sensitive. Check existing names with /view_categories.", ephemeral=True)

# gives the link to the website gallery
@app_commands.guilds(GUILD_ID)
@bot.tree.command(name="gallery")
async def gallery (interaction: discord.Interaction):
    await interaction.response.send_message(f"https://smerfmc.onrender.com", ephemeral=True)

# image and category required
# category must be one of the categories listed
# if desired category not listed, must create a new category
@app_commands.guilds(GUILD_ID)
@bot.tree.command(name="upload")
@app_commands.autocomplete(category=autocomplete_categories)
async def upload(interaction: discord.Interaction,
                 image: discord.Attachment,
                 category: str,
                 caption: Optional[str] = None):
    if not image.content_type or not image.content_type.startswith("image"):
         await interaction.response.send_message(f"Please attach an image.", ephemeral=True) 
         return
    
    # check category
    categories = get_category_names()
    if category not in categories:
        await interaction.response.send_message(f"Category not found. Categories are case sensitive; please check spelling or select from the dropdown menu.")
        return
    
    await interaction.response.defer(thinking=True, ephemeral=True)

    # must unpack and turn into file object
    # upload_fileobj expects a file obj that must have "read" built into it
    data = await image.read()
    data_fileobj = io.BytesIO(data)
    data_fileobj.seek(0) # read from the 0th byte 
    obj_key = gen_s3_obj_key(category, image.filename)

    s3.upload_fileobj(data_fileobj, 'smerfmc', obj_key, ExtraArgs = {"ContentType": image.content_type})

    # insert into Supabase
    data = supa_insert("images", {
            "object_key" : obj_key,
            "category": category,
            "caption": caption
            })

    assert len(data.data) > 0
    # url = create_presigned_url("smerfmc", obj_key)

    await interaction.followup.send(f"Uploaded the object!", ephemeral=True)

bot.run(BOT_TOKEN)