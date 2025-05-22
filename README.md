
# Download Public Comments and Attachments from Regulations.gov

## About this project
This script automatically downloads public comments (and attachments) that were submitted in response to U.S. government Requests for Information (RFIs). The script downloads all comments and attachments for any docket on the U.S. government's [regulations.gov](https://regulations.gov) website. This is a particularly useful tool for anyone who wants to analyze RFIs that receive hundreds or thousands of comments (and attachments). A [similar project](https://github.com/willjobs/regulations-public-comments) (excellently written) already exists, but my project adds two key functions:

* **It keeps track of which comments/attachments you've already downloaded.** So if you exceed your API limit (1,000 calls per hour) in the middle of downloading a docket, it will save your partial progress. All you need to do is wait an hour for your API calls to reset and then run the script again! It'll identify which comments you've already downloaded and skip over those, preserving your API calls for the comments that you haven't yet downloaded.
* **It *downloads* all attachments associated with the RFI.** The other project does obtain the links to each attachment but *doesn't* actually download them for you. This is an issue if (like me) you want to create a folder on your computer where you can sift through the comments and attachments in an organized way; you need to download the attachments, not just find the links.

So how exactly does this script work? It's pretty simple!

1. You provide the script with a docket ID from [regulations.gov](https://regulations.gov) (ex: BIS-2021-0036). The script will create a folder for that docket ID; everything that the script downloads will go in this folder.
2. The script will identify every document and comment associated with the provided docket, and it will store the most important information in a handy CSV file. 
3. The script will create a sub-folder for each comment/document that had at least one attachment. The script will then automatically download each attachment and place it in the assigned sub-folder.

To see what the output looks like, check out the two examples in the "Examples" folder.

## Setup
1. Ensure that you've installed the "pandas" and "xmltodict" packages. If you *do* need to install these packages, you can run following command in your command-line: `pip install pandas xmltodict`
2. Download the script: `regulations_comments_downloader.py`
2. Obtain an API key on the [data.gov](https://api.data.gov/signup/) website.
3. Replace two values in the script (near the top of the file):
	* **Set API key**: Replace `DEMO_KEY` with your personal API key
	* **Set download directory**: Replace `/path/to/folder/` with the path to the directory where you'd like the script to download files. The script will take care of organizing the files!
4. In your command-line, navigate to the folder where you downloaded/edited the script.
5. Run the script, and when you do so, include as an argument the docket ID that you want to download. Ex: `python3 regulations_comments_downloader.py "BIS-2021-0036"`

## Common Issues

* "Filename too long" Error in Windows when cloning this Git repository. Follow [these directions](https://www.javaprogramto.com/2020/04/git-filename-too-long.html).
* New to Python? Here's how to run a Python script on [Windows](https://www.wikihow.com/Use-Windows-Command-Prompt-to-Run-a-Python-File) and [Mac](https://pythonbasics.org/execute-python-scripts/).

*Note: as mentioned above, if you exceed your API limit (1,000 calls per hour) in the middle of downloading a docket, the script will save your partial progress. All you need to do is wait an hour for your API calls to reset and then run the script again! It'll identify which comments you've already downloaded and skip over those, preserving your API calls for the comments that you haven't yet downloaded.*

MIT License- Copyright (c) 2021 Jacob A. Feldgoise
