from functools import partial
import operator

import preprocess
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
    quotes = list(filter(lambda x: isinstance(x, list), terms))
    if quotes:
        for quote in quotes:
            if not has_subset(document, quote):
                return False
        return True

    return any(term in document for term in list(filter(lambda x: isinstance(x, str), terms)))


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


def handle_wildcard(query, index=None, replace=True):
    terms = query.copy()
    for idx, term in enumerate(query):
        if term.startswith('*'):
            term = term.removeprefix('*')
            terms[idx] = term
            if replace and index is not None:
                terms.extend(index.get_related_terms(term))
    return terms


def handle_quote(query, replace=True):
    terms = query.copy()
    _count = 0
    for start_idx, stop_idx in get_position_of_quotes(query):
        if replace:
            for _ in range(start_idx, stop_idx+1):
                terms.pop(start_idx - _count)
            sublist = [
                query[start_idx].removeprefix('"'),
                *query[start_idx+1:stop_idx],
                query[stop_idx].removesuffix('"')
            ]
            terms.insert(start_idx-_count, sublist)
            _count += stop_idx - start_idx
        else:
            terms[stop_idx] = terms[stop_idx].removesuffix('"')
            terms[start_idx] = terms[start_idx].removeprefix('"')
    return terms


def flatten(array):
    flat = []
    for item in array:
        if isinstance(item, (list, tuple, set)):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat


def format_query(query, index=None, wildcard=True, quote=True):
    terms = query.copy()
    terms = handle_wildcard(terms, index=index, replace=wildcard)
    terms = handle_quote(terms, replace=quote)
    return terms


def _search(documents: dict['doc-id', 'doc'], query) -> dict['doc_id', 'doc_score']:
    score_function = partial(score.score, list(documents.values()), query=flatten(query))
    return dict(
        sorted(
            list(
                map(
                    lambda x: (x[0], score_function(x[1])),
                    list(get_related_docs(documents, query))  # (doc-id, doc)
                )
            ),
            key=operator.itemgetter(-1),
            reverse=True
        )
    )


def search(index, documents, query):
    query = format_query(query, index=index)
    query = preprocess.preprocess(query)
    query = list(index.validate_terms(query))
    return _search(documents, query)



if __name__ == "__main__":
    query = ['hello', '"sir', 'ken"', 'when', '"today', 'show"', 'starts']
    print('Query:', query)
    print('Quote Handled:', handle_quote(query))
    print('Wildcard Handled (replace=False):', handle_wildcard(query, replace=False))
