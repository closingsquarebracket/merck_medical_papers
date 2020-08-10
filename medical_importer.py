import requests
import os
from lxml import etree
import datetime
import re
import json

citation_block_size = 250
with open('locations.json', 'r') as f_loc:
    # create your local locations file for data locations and url requests.
    locations = json.load(f_loc)
base_directory = locations['base_directory']
base_request_url = locations['base_request_url']
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
                pub_year, pub_month, pub_day = 1, 1, 1 # silce complaints from IDE
    if pub_date is not None:
        # parse date into standard format
        pub_date = datetime.date(int(pub_year), int(pub_month), int(pub_day))
    return pub_date

def get_citation_count(pmc_id):
    # TODO: Bottleneck in retrieval. The API allows retrieval of info in blocks of up to 500. Need to rework this to allow for block access.
    anwer = requests.get(f"{base_request_url}dbfrom=pubmed&linkname=pubmed_pmc_refs&id={pmc_id}&retmode=json")
    try:
        number_of_citations = len(anwer.json()['linksets'][0]['linksetdbs'][0]['links'])
    except KeyError:
        # if there are no citations, the 'linksetdbs' key is not set, leading to a key error instead of an empty list.
        number_of_citations = 0
    return number_of_citations

def get_multiple_citations(list_of_ids):
    """retrieve citation lists for multiple input ids"""
    id_block = ''
    for id in list_of_ids:
        id_block += f'&id={id}'
    answer = requests.get(f"{base_request_url}dbfrom=pubmed&linkname=pubmed_pmc_refs{id_block}&retmode=json")
    list_of_links = answer.json()['linksets']
    list_of_citations = []
    for counter, links in enumerate(list_of_links):
        try:
            citations = list_of_links[counter]['linksetdbs'][0]['links']
        except KeyError:
            citations = []
        list_of_citations.append(citations) # list of lists: [[<citations>], [<citations>]] in the same order as input list
    return list_of_citations

def clean_index_file():
    with open('oa_file_list.txt', 'r') as f_original:
        file_lines = f_original.readlines()
    publication_names = []
    publication_dates = []
    pmcs = []
    unparseable = 0
    for line in file_lines[1:]: # leave out initial empty line
        location, publication, pmc, *_ = line.split('\t')
        try:
            _, publication_name, publication_date, *_ = re.split(r"([\w\s()]+.?)\s(\d{4}\s\w{3}\s\d+);", publication) # :( re is expensive
            # 25% unparseable
        except ValueError:
            try:
                _, publication_name, publication_date, *_ = re.split(r"([\w\s()]+.?)\s(\d{4}\s\w{3})[-;\s]",
                                                                     publication)  # :( double re is expensive
                publication_date += ' 1' # account for missing dates
                #down to 2% unparseable
            except ValueError:
                print(line)
                unparseable += 1
                continue
        pmc = pmc[3:]
        publication_names.append(publication_name)
        publication_dates.append(publication_date)
        pmcs.append(pmc)
    print(len(pmcs))
    print(f"unparseable = {100*unparseable/len(pmcs)}%.")

    with open('oa_wo_citations.txt', 'w+') as f_wo:
        f_wo.write('PMC_ID; Publication; Publication_date\n')
        for counter in range(len(pmcs)):
            f_wo.write(f"{pmcs[counter]}; {publication_names[counter]}; {publication_dates[counter]}\n")

if __name__ == '__main__':
    # iterate over all files under the base directory.
    # try:
    #     f_table = open("comm_use.A-B_base_information.csv", 'w+')
    #     f_table.write("PMC_ID; Journal_name; Publication_date; Citation_count\n")
    #     for subdir, dir, files in os.walk(base_directory):
    #         for file in files:
    #             if file != '.DS_Store':
    #                 print(file)
    #                 file_address = os.path.join(subdir, file)
    #                 # capture PMC ID. Just grab it from file name.
    #                 pmc_id = get_pmc_id(file)
    #                 pub_date = 0
    #                 # start parsing the xml tree
    #                 tree = etree.parse(file_address)
    #                 root = tree.getroot()
    #                 # retrieve standard journal name
    #                 journal_name = get_journal_name(root)
    #                 # find publication date
    #                 pub_date = get_publication_date(root)
    #                 # get citation count
    #                 n_citations = get_citation_count(pmc_id)
    #                 f_table.write(f"{pmc_id}; {journal_name}; {pub_date}; {n_citations}\n")
    # finally:
    #     f_table.close()

    # with open('oa_file_list.txt', 'r') as f_original:
    #     file_lines = f_original.readlines()
    # publication_names = []
    # publication_dates = []
    # pmcs = []
    # unparseable = 0
    # for line in file_lines[1:]: # leave out initial empty line
    #     location, publication, pmc, *_ = line.split('\t')
    #     try:
    #         _, publication_name, publication_date, *_ = re.split(r"([\w\s()]+.?)\s(\d{4}\s\w{3}\s\d+);", publication) # :( re is expensive
    #         # 25% unparseable
    #     except ValueError:
    #         try:
    #             _, publication_name, publication_date, *_ = re.split(r"([\w\s()]+.?)\s(\d{4}\s\w{3})[-;\s]",
    #                                                                  publication)  # :( double re is expensive
    #             publication_date += ' 1' # account for missing dates
    #             #down to 2% unparseable
    #         except ValueError:
    #             print(line)
    #             unparseable += 1
    #             continue
    #     pmc = pmc[3:]
    #     publication_names.append(publication_name)
    #     publication_dates.append(publication_date)
    #     pmcs.append(pmc)
    # print(len(pmcs))
    # print(f"unparseable = {100*unparseable/len(pmcs)}%.")
    #
    # with open('oa_wo_citations.txt', 'w+') as f_wo:
    #     f_wo.write('PMC_ID; Publication; Publication_date\n')
    #     for counter in range(len(pmcs)):
    #         f_wo.write(f"{pmcs[counter]}; {publication_names[counter]}; {publication_dates[counter]}\n")
    # quit()
    with open('oa_wo_citations.txt', 'r') as f_wo:
        lines = f_wo.readlines()
    pmcs = []
    publication_names = []
    publication_dates = []

    for line in lines[1:]:
        pmc, publication_name, publication_date = line.strip().split("; ") #remove \n after date
        pmcs.append(pmc)
        publication_names.append(publication_name)
        publication_dates.append(publication_date)

    n_citations = []
    full_web_of_citations = {}
    with open('full_web.json', 'r') as f_web:
        old_web = json.load(f_web)  # read old information from file
    full_web_of_citations = {**old_web, **full_web_of_citations} # join dictionaries
    del old_web
    print(f"number of papers: {len(pmcs)}, currently processed: {len(full_web_of_citations)}")

    for block in range(2399000, len(pmcs), citation_block_size): # in case of crash, restart from last printed 'start' value
        start = block
        print(start)
        end = min(len(pmcs), block + citation_block_size) # avoid overshooting and having to rerun.
        source_papers = pmcs[start:end]
        citations = get_multiple_citations(pmcs[start:end])
        for counter in range(end-start):
            n_citations.append(len(citations[counter]))
            full_web_of_citations[source_papers[counter]] = citations[counter]

        with open('oa_with_citations.txt', 'a') as f_table:
            for counter in range(start,end):
                f_table.write(f"{pmcs[counter]}; {publication_names[counter]}; {publication_dates[counter]}; {n_citations[counter - start]}\n")

        with open('full_web.json', 'w') as f_web:
            json.dump(full_web_of_citations, f_web)







    # TODO: It may be possible to retrieve metadata and citation count in one. Need to study Entrez syntax.


