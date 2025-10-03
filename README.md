## SmerfMC Discord Bot
A Discord bot for private server allows users to upload and categorize game screenshots.

### Features
Several commands the user can call.
    **‘/upload’** : upload an image to an existing category, with an optional caption
    **‘/create_category’** : create a new category to which images can be uploaded under
    **‘/change_category’** : edit an existing category name
    **‘/change_description’** : edit an existing category’s description
    **‘/view_categories’** : displays all categories and their descriptions
    **‘/gallery’** : gives a link to the website
    **'/bahh'** : Troll command :)

Uploaded images get stored in Amazon S3. Corresponding object keys, categories, and descriptions storied in Supabase. The website calls this database to display images.

### Built With
- Backend: Python (Discord.py, Boto3, Supabase)
Front end details found [here](https://github.com/Jordanjt4/SmerfMC-Gallery)