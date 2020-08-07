import requests
import os
from lxml import etree
import datetime

base_directory = "/Volumes/υπόλοιπο/medical paper analysis/comm_use.A-B.xml"

def get_pmc_id(file):
    """extract the ID from the file name"""
    pmc_id = file.split(".")[0]
    return pmc_id[3:]

def get_journal_name(parsed_document):
    """extract the journal name based on a parsed document. If no name can be extracted, return 'n/a'."""
    try:
        journal_name = parsed_document.find("front/journal-meta/journal-id[@journal-id-type='nlm-ta']").text
    except AttributeError:
        # capture occasional parsing error
        journal_name = "n/a"
    return journal_name

def get_publication_date(parsed_document):
    """extract the publication date. returns 'n/a' for non-parseable dates."""
    pub_date = 'n/a'
    try:
        # for online publications
        pub_day = parsed_document.find("front/article-meta/pub-date[@pub-type='epub']/day").text
        pub_month = parsed_document.find("front/article-meta/pub-date[@pub-type='epub']/month").text
        pub_year = parsed_document.find("front/article-meta/pub-date[@pub-type='epub']/year").text
    except AttributeError:
        try:
            # for publications that are published on paper
            pub_day = parsed_document.find("front/article-meta/pub-date[@pub-type='ppub']/day").text
            pub_month = parsed_document.find("front/article-meta/pub-date[@pub-type='ppub']/month").text
            pub_year = parsed_document.find("front/article-meta/pub-date[@pub-type='ppub']/year").text
        except AttributeError:
            try:
                # few cases the above empty, capture release to PMC
                pub_day = parsed_document.find("front/article-meta/pub-date[@pub-type='pmc-release']/day").text
                pub_month = parsed_document.find("front/article-meta/pub-date[@pub-type='pmc-release']/month").text
                pub_year = parsed_document.find("front/article-meta/pub-date[@pub-type='pmc-release']/year").text
            except AttributeError:
                # parsing error or other publication method
                pub_date = None
    if pub_date is not None:
        # parse date into standard format
        pub_date = datetime.date(int(pub_year), int(pub_month), int(pub_day))
    return pub_date

def get_citation_count(pmc_id):
    # TODO: Bottleneck in retrieval. The API allows retrieval of info in blocks of up to 500. Need to rework this to allow for block access.
    anwer = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&linkname=pubmed_pmc_refs&id={pmc_id}&retmode=json")
    try:
        len(number_of_citations = anwer.json()['linksets'][0]['linksetdbs'][0]['links'])
    except KeyError:
        # if there are no citations, the 'linksetdbs' key is not set, leading to a key error instead of an empty list.
        number_of_citations = 0
    return number_of_citations

if __name__ == '__main__':
    # iterate over all files under the base directory.
    try:
        f_table = open("comm_use.A-B_base_information.csv", 'w+')
        f_table.write("PMC_ID; Journal_name; Publication_date; Citation_count\n")
        for subdir, dir, files in os.walk(base_directory):
            for file in files:
                if file != '.DS_Store':
                    print(file)
                    file_address = os.path.join(subdir, file)
                    # capture PMC ID. Just grab it from file name.
                    pmc_id = get_pmc_id(file)
                    pub_date = 0
                    # start parsing the xml tree
                    tree = etree.parse(file_address)
                    root = tree.getroot()
                    # retrieve standard journal name
                    journal_name = get_journal_name(root)
                    # find publication date
                    pub_date = get_publication_date(root)
                    # get citation count
                    n_citations = get_citation_count(pmc_id)
                    f_table.write(f"{pmc_id}; {journal_name}; {pub_date}; {n_citations}\n")
    finally:
        f_table.close()




