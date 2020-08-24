import os
import logging
import json
from lxml import etree

with open('locations.json', 'r') as f_loc:
    locations = json.load(f_loc)
base_directory = locations['base_directory']
base_request_url = locations['base_request_url']

parse_locations = {"journal_name": "front/journal-meta/journal-id[@journal-id-type='nlm-ta']",
                   "article_category": "front/article-meta/article-categories/subj-group/subject",
                   "article_title": "front/article-meta/title-group/article-title",
                   "abstract": "front/article-meta/abstract/p"}


def get_pmc_from_xml(parsed_document: etree) -> str:
    pmc = parsed_document.find('front/article-meta/article-id[@pub-id-type="pmc"]').text
    return pmc

def file_processor(base_location: str) -> str:
    """Iterator, returns file locations for each xml file, minus OS-internal files"""
    for subdir, dir, files in os.walk(base_location):
        for file in files:
            if file != '.DS_Store':
                logging.info(f"Currently processing {file}")
                yield os.path.join(subdir, file)


def get_article_info(parsed_document: etree, xml_location: str, alt_text: str = 'n/a'):
    try:
        information = parsed_document.find(xml_location).text
    except AttributeError:
        pmc = get_pmc_from_xml(parsed_document)
        logging.error(f'Failed to parse information in PMC{pmc}')
        information = alt_text
    if information is None:
        pmc = get_pmc_from_xml(parsed_document)
        logging.warning(f'Unsuccessful parsing in PMC{pmc}. Replacing with: "{alt_text}"')
        information = alt_text
    return information


def get_abstract(parsed_document: etree, alt_text: str = 'n/a') -> str:
    try:
        abstract = parsed_document.find('front/article-meta/abstract/p').text
        if abstract is None:
            abstract = ''
            for section in parsed_document.findall('front/article-meta/abstract/sec/p'):
                # for sectioned abstracts
                abstract += str(section.text)
            if abstract == '':
                abstract = alt_text
    except AttributeError:
        abstract = alt_text
    return abstract


def get_authors(parsed_document, min_number_authors):
    list_of_authors = []
    try:
        authors = parsed_document.findall('front/article-meta/contrib-group/')
        try:
            for author in authors:
                surname = author.find('name/surname').text
                given_name = author.find('name/given-names').text
                list_of_authors += [surname, given_name]
        except AttributeError:
            # Error in Parsing
            list_of_authors += ['ParsingError'] * 2
    except AttributeError:
        # list of authors cannot be found
        list_of_authors += ['MissingAuthor'] * 2

    if len(list_of_authors) <= 2 * min_number_authors:
        # padding if there is only one or two authors:
        list_of_authors += [' - '] * 2 * min_number_authors
    return list_of_authors[:2 * min_number_authors]


def parse_document(file_location):
    root = etree.parse(file_location).getroot()
    return root
