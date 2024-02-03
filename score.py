from functools import partial
import pandas as pd
import numpy as np

import preprocess


def term_frequency(document, term):
    return document.count(term)

def term_frequency__weighting_term(document, term):
    tf = term_frequency(document, term)
    if tf == 0:
        return 0
    return 1 + np.log10(tf)

def _document_frequency(document, term):
    return int(term in document)

def document_frequency(documents, term):
    return sum(map(partial(_document_frequency, term=term), documents))

def inverse_document_frequency(documents, term):
    return np.log10(len(documents) / document_frequency(documents, term))

def weighting_term(docs, document, term):
    return term_frequency__weighting_term(document, term) * inverse_document_frequency(docs, term)

def document_length(docs, document, terms):
    return np.sqrt(np.sum(np.fromiter((weighting_term(docs, document, term) ** 2 for term in terms), 'float32')))

def _normalized(docs, terms, document, term):
    wt = weighting_term(docs, document, term)
    length = document_length(docs, document, terms)
    return wt / length

def normalized(docs, terms, document):
    length = document_length(docs, document, terms)
    for term in terms:
        yield weighting_term(docs, document, term) / length

def score(docs, document, query):
    terms = list(preprocess.unique_tokens([*document, *query]))
    doc_norm = np.fromiter(normalized(docs, terms, document), 'float32')
    query_norm = np.fromiter(normalized(docs, terms, query), 'float32')
    return np.sum(doc_norm * query_norm)

def average_precision(docs, documents: list[list[str]], query, minimum=0, maximum=1):
    scores = list(map(partial(score, docs, query=query), documents))
    return np.mean(list(filter(lambda sc: minimum <= sc <= maximum, scores)))

def mean_average_precision(docs, documents: list[list[list[str]]], queries, minimum=0, maximum=1):
    score = 0
    for _documents, query in zip(documents, queries):
        score += average_precision(docs, _documents, query, minimum, maximum)
    return score / len(queries)

def _steps_matrix(docs, total_terms, query):
    matrix = pd.DataFrame()
    matrix['terms'] = total_terms
    matrix['tf'] = matrix['terms'].map(partial(term_frequency, query))
    matrix['tf-wt'] = matrix['terms'].map(partial(term_frequency__weighting_term, query))
    matrix['df'] = matrix['terms'].map(partial(document_frequency, docs))
    matrix['idf'] = matrix['terms'].map(partial(inverse_document_frequency, docs))
    matrix['wt'] = matrix['terms'].map(partial(weighting_term, docs, query))
    matrix['nz'] = matrix['terms'].map(partial(_normalized, docs, total_terms, query))
    return matrix

def steps_matrix(docs, document, query):
    total_terms = list(preprocess.unique_tokens([*document, *query]))
    query_matrix = _steps_matrix(docs, total_terms, query)
    doc_matrix = _steps_matrix(docs, total_terms, document)
    matrix = query_matrix.set_index('terms').join(doc_matrix.set_index('terms'), lsuffix='_q', rsuffix='_d')
    matrix.columns = pd.MultiIndex.from_product([['Query', 'Document'], ['tf', 'tf-wt', 'df', 'idf', 'wt', 'nz']])
    matrix['prod'] = matrix['Query', 'nz'] * matrix['Document', 'nz']
    return matrix
