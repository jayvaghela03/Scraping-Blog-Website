import os
import json
import requests
import pandas as pd
from loguru import logger
from bs4 import BeautifulSoup
from snakemd import Document, Inline, MDList

#Output file path
file_path = "output/data.json"
#Url of the actual page
start_url = 'https://lawctopus.com/clatalogue/clat-pg/'


def get_response(url):
    """
    The function `get_response` makes a GET request to a given URL and retries a specified number of
    times if the response status code is not 200, logging warnings and errors accordingly.
    
    :param url: The `url` parameter is the URL of the website or API endpoint that you want to send a
    GET request to
    :return: The function `get_response` returns a response object if the request is successful (status
    code 200). If the request encounters certain status codes (301, 302, 403, 404, 500, 503, 504), it
    logs a warning and retries the request. If the request encounters a
    `requests.exceptions.RequestException`, it logs an error. If the request is unsuccessful after
    """
    max_retries = 3
    for _ in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
            elif response.status_code in [301, 302, 403, 404, 500, 503, 504]:
                logger.warning(f"Received status code {response.status_code} for {url}. Retrying...")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException: {e} for {url}")
            
    logger.error(f"Failed to get a successful response for {url}")
    return None
        

def get_data():
    """
    The function `get_data` retrieves data from multiple pages by making API requests and parsing the
    response to extract the title and content of each post.
    :return: The function `get_data()` returns a list of dictionaries containing the title and content
    of posts from a website.
    """
    FINAL_DATA = []
    try:
        try:    
            numbers_of_pages = int(input('Enter number of pages to be crawled(default is 5) ->'))
        except:
            numbers_of_pages = 5
        
        for i in range(numbers_of_pages):
            ALL_PAGE_POSTS = []
            
            offset = i*10
            api_url = f'https://clatalogue.com/wp-json/wp/v2/posts?_embed&categories=610&per_page=10&offset={offset}&order=desc'
            response = get_response(api_url)
            logger.success(response.status_code)
            all_post_data = response.json()
            
            for post in all_post_data:
                data = {}
                title = post['title']['rendered']
                raw_content = post['content']['rendered']
                content = parse_content(raw_content)
                
                data['title'] = title
                data['content'] = content
                ALL_PAGE_POSTS.append(data)
            
            FINAL_DATA.extend(ALL_PAGE_POSTS)
            
        return FINAL_DATA
            
    except Exception as e:
        logger.error(f'IN GET_DATA -> {e}')            


def parse_content(raw_content):
    """
    The function `parse_content` takes raw HTML content, extracts a table from it, and converts it into
    a formatted document using the `python-docx` library. It also removes the table from the HTML
    content and returns the remaining text.
    
    :param raw_content: The raw content is the input data that needs to be parsed. It can be in any
    format, such as HTML, text, or a combination of both. The function `parse_content` takes this raw
    content as input and processes it to extract relevant information
    :return: The function `parse_content` returns a string that represents the parsed content from the
    input `raw_content`.
    """
    final_result = ''
    try:
        #Extracting the table and converting it to MD format using snake_md library
        doc = Document()
        html_table = pd.read_html(raw_content)[0].to_dict()
        content = []
        heading = list(html_table.keys())[0]
        doc.add_heading(heading)
        for x in html_table.values():
            for v in x.values():
                content.append(Inline(v.strip()))
            doc.add_block(MDList(content))
            
        final_result += str(doc).replace("\n"," ")
    except:
        pass

    #Using BeautifulSoup to extract the text from html
    soup = BeautifulSoup(raw_content, "lxml")
    
    #Removing the table from the text because table is already being extracted and formatedn into MD format
    try:
        soup.table.clear()
    except:
        pass
    
    value = soup.text.strip()
    final_result += value.replace("\n"," ")
    
    return final_result


def compare_data(existing_data, crawled_data):
    """
    The function compares existing data with crawled data and appends any new items to the existing data
    list.
    
    :param existing_data: A list containing the data that has already been crawled and stored
    :param crawled_data: A list of data that has been recently crawled or scraped from a source
    :return: the updated `existing_data` list after comparing it with the `crawled_data` list.
    """
    for item in crawled_data:
        if item not in existing_data:
            logger.success('NEW POST FOUND')
            existing_data.append(item)
            
    return existing_data
            

def read_json_file():
    """
    The function reads a JSON file and returns its contents if the file exists, otherwise it returns
    None.
    :return: The function `read_json_file` returns the existing data from the JSON file if the file
    exists, otherwise it returns `None`.
    """
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            existing_data = json.load(f)
            
        return existing_data
    else:
        return None
            

def save_to_json(data):
    """
    The function `save_to_json` saves data to a JSON file and logs a success message.
    
    :param data: The `data` parameter is the Python object that you want to save to a JSON file. It can
    be a dictionary, list, or any other valid JSON serializable object
    """
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)
    
    logger.success('OUTPUT FILE CREATED')


def main():
    """
    The main function reads existing data from a JSON file, crawls new data, compares the existing and
    crawled data, and saves the final output to a JSON file.
    """
    existing_data = read_json_file()
    crawled_data = get_data()
    
    if existing_data:
        final_output = compare_data(existing_data, crawled_data)
        save_to_json(final_output)
    else:
        save_to_json(crawled_data)


if __name__ == '__main__':
    main()
    