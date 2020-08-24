import medical_importer as mi
import os
from lxml import etree
import logging

import util

n_authors = 3

output_file="metadata_matching_I-N.txt"

if __name__ == '__main__':
    logging.basicConfig(filename = 'LogFile.txt', datefmt = 'd %b %Y %H:%M:%S', level = logging.WARNING)

    citation_connection = {}
    # for that sweet O(1) speed

    with open('oa_with_citations.txt', 'r') as f_citations:
        for line in f_citations:
            if line[0] in '0123456789':
                PMC_ID, _, pub_date, n_citations = line.strip().split('; ')
                citation_connection[PMC_ID] = {'citations': int(n_citations), 'pub_date': pub_date}
            else:
                logging.warning(f'Unparseable line from citation file: {line}')
                pass
    logging.info('citation matching successfully parsed.')
    for subdir, dir, files in os.walk(os.path.join(mi.base_directory, 'comm_use.I-N.xml')):
        file_empty = False
        with open(output_file, 'r') as f_meta:
            for line_no, line in enumerate(f_meta):
                if len(line) == 0 and line_no < 4:
                    file_empty = True
        if file_empty:
            logging.warning("File found empty. Emptying file and recreating header.")
            with open(output_file, 'w') as f_meta:
                f_meta.write(
                    "PMC_ID; publication_date; journal; article; article_category; author1_sur; author1;_given; author2_sur; author2_given; author3_sur, author3_given; keywords; citations\n")
        for file in files:
            if file != '.DS_Store':
                logging.info(f'Parsing file {file}')
                file_address = os.path.join(subdir, file)
                root = etree.parse(file_address).getroot()
                # retrieve metadata
                pmc_id = mi.get_pmc_id(file)
                try:
                    citations = citation_connection[pmc_id]['citations']
                    pub_date = citation_connection[pmc_id]['pub_date']
                except KeyError:
                    # skip articles that don't have citation data available
                    continue
                journal_name = util.get_article_info(root, util.parse_locations['journal_name'])
                article_title = util.get_article_info(root, util.parse_locations['article_title']).strip('\n\t;')
                article_category = util.get_article_info(root, util.parse_locations['article_category'])
                authors = util.get_authors(root, n_authors)
                keywords = mi.get_keywords(root)
                # abstract = mi.get_article_info(root, mi.parse_locations['abstract'], alt_text = 'No abstract could be parsed')
                with open('metadata_matching.txt', 'a') as f_meta:
                    f_meta.write(
                        f'{pmc_id}; {pub_date}; {journal_name}; {article_title}; {authors[0]}; {authors[1]}; {authors[2]}; {authors[3]}; {authors[4]}; {authors[5]}; {keywords}; {citations}\n')
