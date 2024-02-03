from abc import ABC, abstractmethod
from collections import UserDict
import json

import search
import score


class Index(UserDict, ABC):
    def __init__(self):
        super().__init__()

        self._doc_counter = 1
        self.documents = {}
        self.terms = set()

    def get_term(self, term):
        if term not in self.terms:
            raise IndexError(f'Term <{term}> does not exists!')
        return self[term]

    def find_related_terms(self, term):
        return list(filter(lambda t: (term in t) and (term != t), self.terms))

    def add_document(self, doc, doc_id=None):
        if doc_id is None:
            doc_id = self._doc_counter
            self._doc_counter += 1
        elif doc_id in self.doc_ids:
            raise IndexError(f'Doc-ID <{doc_id}> already exists!')

        self.documents[doc_id] = doc
        self._add_document(doc, doc_id)
        return doc_id

    def add_documents(self, docs):
        for doc in docs:
            self.add_document(doc)

    def remove_document(self, doc_id):
        if doc_id not in self.doc_ids:
            raise ValueError(f'Doc-ID <{doc_id}> does not exists!')

        self.documents.pop(doc_id)
        self._remove_document(doc_id)

    def remove_documents(self, doc_ids):
        for doc_id in doc_ids:
            self.remove_document(doc_id)

    def validate_terms(self, terms):
        for term in terms:
            if isinstance(term, list):
                yield list(self.validate_terms(term))
            elif term in self.terms:
                yield term

    def save(self, filepath, indent=4):
        with open(filepath, 'w') as handler:
            return json.dump(self.data, handler, indent=indent)

    def fetch_id(self, doc_id):
        if doc_id not in self.doc_ids:
            raise IndexError(f'Doc-ID <{doc_id}> does not exists!')
        return self.documents[doc_id]

    def format_query(self, query, wildcard=True, quote=True):
        return search.format_query(self, query, wildcard=wildcard, quote=quote)

    def search(self, query, n=10):
        return search.search(self, self.documents, query, n=n)

    def score(self, document, query):
        return score.score(self.docs, document, query)

    def average_precision(self, documents, query, minimum=0, maximum=1):
        return score.average_precision(self.docs, documents, query, minimum=minimum, maximum=maximum)

    def mean_average_precision(self, documents, queries, minimum=0, maximum=1):
        return score.mean_average_precision(self.docs, documents, queries, minimum=minimum, maximum=maximum)

    def steps_matrix(self, document, query):
        return score.steps_matrix(self.docs, document, query)

    @property
    def docs(self): return list(self.documents.values())

    @property
    def doc_ids(self): return list(self.documents.keys())

    @abstractmethod
    def view_term(self, term): return

    @abstractmethod
    def count_term(self, term): return

    @abstractmethod
    def _add_document(self, terms, doc_id): pass

    @abstractmethod
    def _remove_document(self, doc_id): pass

    def __setitem__(self, key, value):
        self.data[key] = value


class NonPositionalIndex(Index):
    def _add_document(self, terms, doc_id):
        for term in terms:
            if term not in self.terms:
                self.terms.add(term)
                self[term] = []
            self[term].append(doc_id)

    def _remove_document(self, doc_id):
        for doc_ids in self.values():
            if doc_id in doc_ids:
                doc_ids.remove(doc_id)

    def count_term(self, term):
        return len(self.get_term(term))

    def view_term(self, term):
        print(f"Non-Positional Index ({term})")
        print('Doc-IDs:', self.get_term(term))
        print()


class PositionalIndex(Index):
    def _add_document(self, terms, doc_id):
        for term_id, term in enumerate(terms):
            if term not in self.terms:
                self.terms.add(term)
                self[term] = {}
            if doc_id not in self[term]:
                self[term][doc_id] = [term_id]
            else:
                self[term][doc_id].append(term_id)

    def _remove_document(self, doc_id):
        for result in self.values():
            if doc_id in result:
                result.pop(doc_id)

    def count_term(self, term):
        c = 0
        for term_ids in self.get_term(term).values():
            c += len(term_ids)
        return c

    def view_term(self, term):
        result = self.get_term(term)
        print(f"Positional Index ({term})")
        print("Doc-ID | [Term-IDs]")
        for doc_id, term_ids in result.items():
            print(doc_id, term_ids, sep=' | ')


if __name__ == '__main__':
    documents = [
        ['hello', 'world'],
        ['hello', 'my', 'dear'],
        ['what', 'on', 'world', 'is', 'going'],
        ['how', 'the', 'world', 'seems', 'for', 'you']
    ]

    print('Documents:', documents, '\n')

    positional = PositionalIndex()
    non_positional = NonPositionalIndex()

    positional.add_documents(documents)
    non_positional.add_documents(documents)

    term = 'world'
    positional.view_term(term)
    print()
    non_positional.view_term(term)
