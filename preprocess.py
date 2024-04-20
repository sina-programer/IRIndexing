from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
from nltk import pos_tag
import pandas as pd
import numpy as np
import string
import time


STOPWORDS = stopwords.words('english')
POS_TAGS = {
    'nn': 'n',
    'nns': 'n',
    'nnp': 'n',
    'nnps': 'n',

    'vb': 'v',
    'vbd': 'v',
    'vbg': 'v',
    'vbn': 'v',
    'vbp': 'v',
    'vbz': 'v',
    'md': 'v',

    'jj': 'a',
    'jjr': 'a',
    'jjs': 'a',

    'rb': 'r',
    'rbr': 'r',
    'rbs': 'r',
    'rb': 'r',
    'wrb': 'r',
}

def tokenize(sentence):
    return tokenizer.tokenize(sentence)

def is_stopword(token):
    return (token in STOPWORDS) or (token in string.punctuation)

def _stem(token):
    return stemmer.stem(token)

def stem(tokens):
    return list(map(_stem, tokens))

def _lemmatize(token):
    tag = pos_tag([token])[0][-1].lower()
    tag = POS_TAGS.get(tag, 'n')
    return lemmatizer.lemmatize(token, tag)

def lemmatize(tokens):
    tags = pos_tag(tokens)
    tags = list(map(lambda x: x[-1].lower(), tags))
    tags = list(map(lambda x: POS_TAGS.get(x, 'n'), tags))
    return list(map(lambda x: lemmatizer.lemmatize(*x), zip(tokens, tags)))

def preprocess(query, stemming=True, stopword=True, lower=True):
    tokens = []
    for token in query:
        if stopword and is_stopword(token):
            continue
        elif isinstance(token, (list, tuple, set)):
            tokens.append(preprocess(token))
            continue

        if lower:
            token = token.lower()
        if stemming:
            token = _stem(token)
        tokens.append(token)

    return tokens

def preprocess_sentence(string, return_token=False, delimiter=' '):
    tokens = preprocess(tokenize(string))
    if return_token:
        return tokens
    return delimiter.join(tokens)

def unique_tokens(tokens):
    used_tokens = set()
    for token in tokens:
        if token not in used_tokens:
            yield token
            used_tokens.add(token)


tokenizer = TweetTokenizer(preserve_case=False, reduce_len=True, strip_handles=True)
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()


if __name__ == "__main__":
    print('Benchmark stemming vs lemmatizing')
    print('Loading Data...')
    df = pd.read_csv('ted_talks.csv')
    tokens = df['description'].map(tokenizer.tokenize)
    print('Number of Tokens: ', len(tokens))

    t1 = time.perf_counter()
    stemming = tokens.map(stem)
    t2 = time.perf_counter()
    print(f"The stemming calculation took {t2-t1:.3f} seconds")

    t3 = time.perf_counter()
    lemmatizing = tokens.map(lemmatize)
    t4 = time.perf_counter()
    print(f"The lemmatizing calculation took {t4-t3:.3f} seconds")

    idx = np.random.choice(stemming.index)
    print('Index: ', idx)
    print('Sentence: ', df.loc[idx, 'description'])
    print()

    print('The differneces between these two methods for above sentence: (stemmed | lemmatized)')
    for i in range(len(stemming[idx])):
        if stemming[idx][i] != lemmatizing[idx][i]:
            print(stemming[idx][i], '|', lemmatizing[idx][i])
