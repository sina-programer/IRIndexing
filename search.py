from functools import partial
import operator

import score


def has_subset(array, subarray):
    for item in subarray:
        if item not in array:
            return False

    n = len(subarray)
    for i in range(len(array)-n+1):
        if subarray == array[i:i+n]:
            return True

    return False

def is_doc_related(document, terms):
    compound_terms = list(filter(lambda x: isinstance(x, list), terms))  # terms inside a quotation
    if compound_terms:
        for cterm in compound_terms:
            if not has_subset(terms, cterm):
                return False
        return True

    simple_terms = list(filter(lambda x: x not in compound_terms, terms))
    return any(term in document for term in simple_terms)

def get_related_docs(documents, terms):
    for doc_id, doc in documents.items():
        if is_doc_related(doc, terms):
                yield doc_id, doc

def get_position_of_quotes(query):
    start_idx, stop_idx = None, None
    for idx, term in enumerate(query):
        if not start_idx and term.startswith('"'):
            start_idx = idx
        if start_idx and term.endswith('"'):
            stop_idx = idx

        if start_idx and stop_idx:
            yield start_idx, stop_idx
            start_idx, stop_idx = None, None

def handle_wildcard(index, query, replace=True):
    terms = query.copy()
    for idx, term in enumerate(query):
        if term.startswith('*'):
            term = term.removeprefix('*')
            terms[idx] = term
            if replace:
                terms.extend(index.get_related_terms(term))
    return terms

def handle_quote(query, replace=True):
    terms = query.copy()
    _count = 0
    for start_idx, stop_idx in get_position_of_quotes(query):
        if replace:
            for _ in range(start_idx, stop_idx+1):
                terms.pop(start_idx - _count)
            sublist = query[start_idx:stop_idx+1]
            sublist[0] = sublist[0].removeprefix('"')
            sublist[-1] = sublist[-1].removesuffix('"')
            terms.insert(start_idx-_count, sublist)
            _count += stop_idx - start_idx
        else:
            terms[stop_idx] = terms[stop_idx].removesuffix('"')
            terms[start_idx] = terms[start_idx].removeprefix('"')
    return terms

def format_query(index, query, wildcard=True, quote=True):
    terms = query.copy()
    terms = handle_wildcard(index, terms, replace=wildcard)
    terms = handle_quote(terms, replace=quote)
    return terms

def search(index, documents: dict['doc-id', 'doc'], query, n=10):
    query = format_query(index, query)
    score_function = partial(score.score, list(documents.values()), query=query)
    related_docs = list(get_related_docs(documents, query))  # (doc-id, doc)
    related_docs.sort(key=lambda x: score_function(x[1]), reverse=True)
    return list(map(operator.itemgetter(0), related_docs[:n]))


if __name__ == "__main__":
    query = ['hello', '"sir', 'ken"', 'when', '"today', 'show"', 'starts']
    print('Query:', query)
    print('Quote Positions:', list(get_position_of_quotes(query)))
    print('Quote Formatted:', handle_quote(query))
    print('Quote Formatted (replace=False):', handle_quote(query, replace=False))
