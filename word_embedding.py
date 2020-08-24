import gensim.models
import logging
import util
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from collections import Counter

stemmer = PorterStemmer()

alt_text = 'n/a'

def pre_processor(input_text) -> list:
    sentences = sent_tokenize(input_text.lower())
    tokenized_sentences = []
    for sentence in sentences:
        words = [stemmer.stem(word) for word in word_tokenize(sentence) if word not in stopwords.words('english')]
        tokenized_sentences.append(words)
    return tokenized_sentences


class CorpusLoader:
    def __init__(self, base_file_location: str):
        self.file_location = base_file_location

    def __iter__(self):
        for file in util.file_processor(self.file_location):
            file_name = file.split('/')[-1]
            pmc_code = file_name[:-5]
            xml_file = util.parse_document(file)
            abstract = str(util.get_abstract(xml_file, alt_text))
            if abstract == alt_text:
                # skip unreadables to not influence training
                continue
            sentences = pre_processor(abstract)
            for sentence in sentences:
                yield pmc_code, sentence

class StemmedLoader(CorpusLoader):
    def __iter__(self):
        with open(self.file_location, 'r') as f:
            for line in f:
                pmc, *sentence = line.split(' ')
                print(pmc, end = '\r')
                yield sentence

if __name__ == '__main__':
    stemmed_abstracts = StemmedLoader('stemmed abstracts.txt')


    medical_w2v = gensim.models.Word2Vec(sentences = stemmed_abstracts, size = 128, workers = 4)
    medical_w2v.save('medical_w2v.model')