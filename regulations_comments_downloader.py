import requests, os, json, xmltodict, datetime, re, sys
import pandas as pd


def get_document_ids(docket_id, api_key):
    docs_url = "https://api.regulations.gov/v4/documents?filter[docketId]={}&api_key={}".format(docket_id, api_key)
    data = json.loads(requests.get(docs_url).text)

    if ("error" in data) and (data["error"]["code"] == "OVER_RATE_LIMIT"):
        print("[" + str(datetime.datetime.now()) + "] " + "You've exceeded your API limit! Wait an hour and try again. Don't worry, we saved your progress.")
        return None

    data = data["data"]
    doc_ids = []
    doc_links = []
    for i in range(len(data)):
        doc_ids.append(data[i]["attributes"]["objectId"])
        doc_links.append(data[i]["links"]["self"])

    print("[" + str(datetime.datetime.now()) + "] " + "Retrieved {} documents for docket {}".format(len(doc_ids), docket_id))
    return doc_ids, doc_links

def get_allComments(docket_id, doc_ids, api_key):
    # get all comments
    comments = []
    # Iterate through all documents on the docket
    for doc_id in doc_ids:
        # Page through all pages (up to 5000 comments)
        max_pages = 20
        for i in range(1, max_pages):
            comment_url = "https://api.regulations.gov/v4/comments?filter[commentOnId]={}&include=attachments&page[size]=250&page[number]={}&api_key={}".format(doc_id, str(i), api_key)
            data = json.loads(requests.get(comment_url).text)

            if ("error" in data) and (data["error"]["code"] == "OVER_RATE_LIMIT"):
                print("[" + str(datetime.datetime.now()) + "] " + "You've exceeded your API limit! Wait an hour and try again.")
                return None

            data = data["data"]
            if len(data) == 0:
                break
            comments.extend(data)

    # Create list of comment links
    comment_links = []
    for i in range(len(comments)):
        comment = comments[i]
        comment_links.append(comment["links"]["self"])

    print("[" + str(datetime.datetime.now()) + "] " + "Found {} comments on {} documents for docket {}".format(len(comment_links), len(doc_ids), docket_id))
    return comments, comment_links

def check_previousWork(file_path):

    file_exist = os.path.exists(file_path)
    api_links = set()

    # If file exists, then load the data and create a set that contains comment links.
    if file_exist:
        df = pd.read_csv(file_path, index_col = None)
        links_set = set(df["link"])
        print("[" + str(datetime.datetime.now()) + "] " + "Found {} document(s)/comment(s) that were previously saved".format(len(links_set)))

        return df, links_set
    else:
        return None, None

# https://sumit-ghosh.com/articles/python-download-progress-bar/
def download(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')

def save_attachment(folder_path, attachment):
    name, url = attachment
    file_path = folder_path + name
    ext = url.split('.')[-1]
    file_path = file_path + "." + ext

    file_already_downloaded = os.path.exists(file_path)

    if not file_already_downloaded:

        print("\t[" + str(datetime.datetime.now()) + "] " + "Downloading file ({})".format(name))
        download(url, file_path)

    else:
        print("\t[" + str(datetime.datetime.now()) + "] " + "File was already downloaded ({})".format(name))

def get_comment_details(link, api_key, column_names, folder_path, comment_id, commentOrDocument):
    print("[" + str(datetime.datetime.now()) + "] " + "Working on {} {}".format(commentOrDocument, comment_id))

    # Identify and save comment data
    comment_url = link + "?api_key={}".format(api_key)
    comment_data = json.loads(requests.get(comment_url).text)

    if ("error" in comment_data) and (comment_data["error"]["code"] == "OVER_RATE_LIMIT"):
        print("[" + str(datetime.datetime.now()) + "] " + "You've exceeded your API limit! Wait an hour and try again.")
        return None
    # ["modifyDate", "docketId", "commentOnDocumentId", "commentId", "organization", "firstName", "lastName", "title", "comment"]
    comment_data = comment_data["data"]
    comment_details = pd.DataFrame(columns = column_names)
    comment_details.at[0, 'commentOrDocument'] = commentOrDocument
    comment_details.at[0, 'id'] = comment_id
    comment_details.at[0, 'modifyDate'] = comment_data["attributes"]["modifyDate"]
    comment_details.at[0, 'docketId'] = comment_data["attributes"]["docketId"]
    comment_details.at[0, 'organization'] = comment_data["attributes"]["organization"]
    comment_details.at[0, 'lastName'] = comment_data["attributes"]["firstName"]
    comment_details.at[0, 'lastName'] = comment_data["attributes"]["lastName"]
    comment_details.at[0, 'title'] = comment_data["attributes"]["title"]
    comment_details.at[0, 'link'] = link

    if commentOrDocument == "comment":
        comment_details.at[0, 'commentOnDocumentId'] = comment_data["attributes"]["commentOnDocumentId"]
        comment_details.at[0, 'comment'] = comment_data["attributes"]["comment"]
    else:
        comment_details.at[0, 'commentOnDocumentId'] = None
        comment_details.at[0, 'comment'] = None

    # Identify and save attachment links
    attachments = []
    if commentOrDocument == "comment":
        attachments_url = link + "/attachments?api_key={}".format(api_key)
        attachments_data = json.loads(requests.get(attachments_url).text)

        if ("error" in attachments_data) and (attachments_data["error"]["code"] == "OVER_RATE_LIMIT"):
            return None

        attachments_data = attachments_data["data"]
        for item in attachments_data:
            if item["attributes"]["restrictReasonType"] == None:
                title = item["attributes"]["title"]
                link = item["attributes"]["fileFormats"][0]["fileUrl"]
                attachments.append((title, link))

        if len(attachments) > 0:
            folder_path = folder_path + comment_id + "/"
            folder_path_exists = os.path.isdir(folder_path)
            if not folder_path_exists:
                os.mkdir(folder_path)
                print("\t[" + str(datetime.datetime.now()) + "] " + "Created folder at: " + folder_path)
            else:
                print("\t[" + str(datetime.datetime.now()) + "] " + "Folder already exists!")

        for item in attachments:
            title, link = item
            save_attachment(folder_path, (title, link))
    else:

        folder_path = folder_path + comment_id + "/"
        folder_path_exists = os.path.isdir(folder_path)
        if not folder_path_exists:
            os.mkdir(folder_path)
            print("\t[" + str(datetime.datetime.now()) + "] " + "Created folder at: " + folder_path)
        else:
            print("\t[" + str(datetime.datetime.now()) + "] " + "Folder already exists!")


        attachments_data = [""]
        title = comment_data["attributes"]["title"]
        link = comment_data["attributes"]["fileFormats"][0]["fileUrl"]
        attachments.append((title, link))
        save_attachment(folder_path, (title, link))

    comment_details.at[0, 'attachments'] = attachments

    print("\t[" + str(datetime.datetime.now()) + "] " + "Collected {} {} with {} attachments ({} were downloadable)".format(commentOrDocument, comment_id, len(attachments_data), len(attachments)))
    return comment_details

def get_allComment_details(comment_links, document_links, folder_path, docket_id, api_key, column_names):

    # Try to load previous work
    previous_work_path = folder_path + "comment_details.csv"
    allComments_details, allComments_links = check_previousWork(previous_work_path)
    if allComments_links == None:
        allComments_details = pd.DataFrame(columns = column_names)
        allComments_links = set()

    try:
        # Loop through all documents
        for link in document_links:
            p = re.compile("[^\/]+$")
            m = p.search(link)
            doc_id = m.group()

            if link not in allComments_links:
                doc_details = get_comment_details(link, api_key, column_names, folder_path, doc_id, "document")
                if doc_details is None:
                    print("[" + str(datetime.datetime.now()) + "] " + "You've exceeded your API limit! Wait an hour and try again. Don't worry, we'll save your progress.")
                    print("[" + str(datetime.datetime.now()) + "] " + "Exiting documents loop...")
                    return allComments_details

                allComments_details = pd.concat([allComments_details, doc_details])

            else:
                print("[" + str(datetime.datetime.now()) + "] " + "Document {} was previously saved! Skipping...".format(doc_id))

        # Loop through all comments
        for link in comment_links:
            p = re.compile("[^\/]+$")
            m = p.search(link)
            comment_id = m.group()

            if link not in allComments_links:
                comment_details = get_comment_details(link, api_key, column_names, folder_path, comment_id, "comment")
                if comment_details is None:
                    print("[" + str(datetime.datetime.now()) + "] " + "You've exceeded your API limit! Wait an hour and try again. Don't worry, we'll save your progress.")
                    print("[" + str(datetime.datetime.now()) + "] " + "Exiting comments loop...")
                    return allComments_details

                allComments_details = pd.concat([allComments_details, comment_details])

            else:
                print("[" + str(datetime.datetime.now()) + "] " + "Comment {} was previously saved! Skipping...".format(comment_id))

    except KeyboardInterrupt:
        print("[" + str(datetime.datetime.now()) + "] " + 'Interrupted!')
        return allComments_details

    print("[" + str(datetime.datetime.now()) + "] " + "Saving progress...")
    print("[" + str(datetime.datetime.now()) + "] " + "All {} document(s) and {} comment(s) were saved and all attachments were downloaded!".format(len(document_links), len(comment_links)))
    allComments_details.to_csv(previous_work_path, index=False)

def setup_folder(baseFolder_path, docket_id):
    folder_path = baseFolder_path + docket_id + "/"
    folder_path_exists = os.path.isdir(folder_path)
    if not folder_path_exists:
        os.mkdir(folder_path)
        print("[" + str(datetime.datetime.now()) + "] " + "Created folder at: " + folder_path)
    else:
        print("[" + str(datetime.datetime.now()) + "] " + "Folder already exists!")

    return folder_path


def main_loop(api_key, baseFolder_path):

    try:
        docket_id = sys.argv[1]
    except:
        print("[" + str(datetime.datetime.now()) + "] " + "Make sure to include your docket ID as an argument!\nEx: python3 regulations_comments_downloader.py 'NIST-2021-0006'")
        print("[" + str(datetime.datetime.now()) + "] " + "Exiting...")
        return None

    column_names = ["commentOrDocument", "modifyDate", "docketId", "commentOnDocumentId", "id", "organization", "firstName", "lastName", "title", "comment", "attachments", "link"]
    folder_path = setup_folder(baseFolder_path, docket_id)

    # Get list of documents
    doc_ids, doc_links = get_document_ids(docket_id, api_key)
    if doc_ids == None:
        print("[" + str(datetime.datetime.now()) + "] " + "Exiting...")
        return None

    # Get list of comments
    allComments = get_allComments(docket_id, doc_ids, api_key)
    if allComments == None:
        print("[" + str(datetime.datetime.now()) + "] " + "Exiting...")
        return None
    comments, comment_links = allComments

    # Get all comment details and attachments
    get_allComments_csv = get_allComment_details(comment_links, doc_links, folder_path, docket_id, api_key, column_names)
    if get_allComments_csv is not None:
        print("[" + str(datetime.datetime.now()) + "] " + "Saving progress...")
        get_allComments_csv.to_csv(folder_path + "comment_details.csv", index=False)
        print("[" + str(datetime.datetime.now()) + "] " + "Exiting main loop...")

######

api_key = "DEMO_KEY"
baseFolder_path = "/path/to/folder/"

main_loop(api_key, baseFolder_path)
