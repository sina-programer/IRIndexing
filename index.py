from abc import ABC, abstractmethod
from collections import UserDict
import json
import time
import os

import search
import score


class Index(UserDict, ABC):
    def __init__(self):
        super().__init__()

        self.terms = set()
        self.documents = {}
        self._doc_counter = 0

    @property
    def docs(self): return list(self.documents.values())

    @property
    def doc_ids(self): return list(self.documents.keys())

    @property
    @abstractmethod
    def is_positional(self): return

    @abstractmethod
    def count_term(self, term): return  # returns the frequency of the 'term'

    @abstractmethod
    def _add_document(self, terms, doc_id): pass  # add a doc considering the dictinoary structure

    @abstractmethod
    def _remove_document(self, doc_id): pass

    @abstractmethod
    def _get_term(self, term): return

    @classmethod
    def _dump(cls, filepath, dictionary, overwrite=True, backup=False, indent=4):
        if not overwrite and os.path.exists(filepath):
            counter = 2
            filedir, basename, ext = splitter(filepath)
            while os.path.exists(filepath := os.path.join(filedir, basename+f' ({counter})'+ext)):
                counter += 1

        with open(filepath, 'w') as handler:
            json.dump(dictionary, handler, indent=indent)

        if backup:
            filedir, basename, ext = splitter(filepath)
            cls._dump(
                os.path.join(
                    filedir,
                    basename + '.bac' + str(int(time.time())) + ext
                ),
                dictionary,
                overwrite=True,
                backup=False,
                indent=4
            )

    @classmethod
    def view_positional(cls, result, term=None):
        print(cls.__name__ + f" ({term})" if term else '')
        print("Doc-ID  | [Term-IDs]")
        for doc_id, term_ids in result.items():
            if isinstance(term_ids, list):
                print(format(doc_id, '<7'), term_ids, sep=' | ')
        print()

    @classmethod
    def view_nonpositional(cls, result, term=None):
        print(cls.__name__ + f" ({term})" if term else '')
        print('Doc-IDs:', result)
        print()

    def view_term(self, term):
        if self.is_positional:
            self.view_positional(self.get_term(term), term=term)
        else:
            self.view_nonpositional(self.get_term(term), term=term)

    def get_term(self, term):
        if not self.validate_term(term):
            raise IndexError(f'Term <{term}> does not exists!')
        return self._get_term(term)

    def add_document(self, document, doc_id=None):
        if doc_id is None:
            self._doc_counter += 1
            doc_id = self._doc_counter
        if self.validate_document(doc_id):
            raise IndexError(f'Doc-ID <{doc_id}> already exists!')

        for term in document:
            self.terms.add(term)
        self.documents[doc_id] = document
        self._add_document(document, doc_id)
        return doc_id

    def add_documents(self, docs):
        for doc in docs:
            self.add_document(doc)

    def remove_document(self, doc_id):
        if not self.validate_document(doc_id):
            raise ValueError(f'Doc-ID <{doc_id}> does not exists!')

        for term in self.documents.pop(doc_id):
            if self.count_term(term) == 0:
                self.terms.remove(term)
        self._remove_document(doc_id)

    def remove_documents(self, doc_ids):
        for doc_id in doc_ids:
            self.remove_document(doc_id)

    def fetch_document(self, doc_id):
        if not self.validate_document(doc_id):
            raise IndexError(f'Doc-ID <{doc_id}> does not exists!')
        return self.documents[doc_id]

    def validate_document(self, doc_id):
        return doc_id in self.documents

    def validate_term(self, term):
        return term in self.terms

    def validate_terms(self, terms):
        for term in terms:
            if isinstance(term, list):
                yield list(self.validate_terms(term))
            elif self.validate_term(term):
                yield term

    def dump(self, filepath=None, **kwargs):
        if filepath is None:
            filepath = type(self).__name__ + '.json'
        Index._dump(filepath, self.data, **kwargs)

    def get_related_terms(self, term, itself=False):
        return list(filter(lambda t: (term in t) and (True if itself else term != t), self.terms))

    def format_query(self, query, wildcard=True, quote=True):
        return search.format_query(query, index=self, wildcard=wildcard, quote=quote)

    def search(self, query):
        return search.search(self, self.documents, query)

    def score(self, document, query):
        return score.score(self.docs, document, query)

    def average_precision(self, documents, query, minimum=0, maximum=1):
        return score.average_precision(self.docs, documents, query, minimum=minimum, maximum=maximum)

    def mean_average_precision(self, documents, queries, minimum=0, maximum=1):
        return score.mean_average_precision(self.docs, documents, queries, minimum=minimum, maximum=maximum)

    def steps_matrix(self, document, query):
        return score.steps_matrix(self.docs, document, query)

    def __setitem__(self, key, value):
        self.data[key] = value



class Posting(Index, ABC):
    def _get_term(self, term):
        return self[term]


class Graph(Index, ABC):
    def _get_term(self, term):
        node = self.data
        for char in term:
            if char not in node:
                return
            node = node[char]
        return node

    def remove_key(self, key, node=None):
        if node is None:
            node = self.data

        if isinstance(node, dict):
            for item in Graph._get_doc_ids(node):
                if item == key:
                    del node[key]
            for value in node.values():
                self.remove_key(key, node=value)

    @classmethod
    def _get_doc_ids(cls, dic):
        return list(filter(lambda x: isinstance(x, int), dic.keys()))



class NonPositionalPosting(Posting):
    is_positional = False

    def _add_document(self, terms, doc_id):
        for term in terms:
            self.setdefault(term, list())
            self[term].append(doc_id)

    def _remove_document(self, doc_id):
        for term, doc_ids in self.items():
            if doc_id in doc_ids:
                self[term].remove(doc_id)

    def count_term(self, term):
        return len(self.get_term(term))


class PositionalPosting(Posting):
    is_positional = True

    def _add_document(self, terms, doc_id):
        for term_id, term in enumerate(terms):
            self.setdefault(term, dict())
            self[term].setdefault(doc_id, list())
            self[term][doc_id].append(term_id)

    def _remove_document(self, doc_id):
        for term, result in self.items():
            if doc_id in result:
                self[term].pop(doc_id)

    def count_term(self, term):
        count = 0
        for term_ids in self.get_term(term).values():
            count += len(term_ids)
        return count


class PositionalGraph(Graph):
    is_positional = True

    def _add_document(self, document, doc_id):
        for term_id, term in enumerate(document):
            node = self.data
            for char in term:
                node.setdefault(char, dict())
                node = node[char]
            node.setdefault(doc_id, list())
            node[doc_id].append(term_id)

    def _remove_document(self, doc_id):
        self.remove_key(doc_id)

    def count_term(self, term):
        node = self.data
        for char in term:
            if char not in node:
                break
            node = node[char]
        else:
            return sum(map(len, map(lambda x: node[x], self._get_doc_ids(node))))
        return -1



def splitter(path):
    filedir, filename = os.path.split(path)
    basename, extension = os.path.splitext(filename)
    return filedir, basename, extension


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
