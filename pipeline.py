"""
Pipeline for text processing implementation
"""
import re

from pathlib import Path
from pymystem3 import Mystem
import pymorphy2

from core_utils.article import Article
from constants import ASSETS_PATH


class EmptyDirectoryError(Exception):
    """
    No data to process
    """


class InconsistentDatasetError(Exception):
    """
    Corrupt data:
        - numeration is expected to start from 1 and to be continuous
        - a number of text files must be equal to the number of meta files
        - text files must not be empty
    """


class MorphologicalToken:
    """
    Stores language params for each processed token
    """

    def __init__(self, original_word):
        self.original_word = original_word
        self.normalized_form = ''
        self.tags_mystem = ''
        self.tags_pymorphy = ''

    def get_cleaned(self):
        """
        Returns lowercased original form of a token
        """
        return self.original_word.lower()

    def get_single_tagged(self):
        """
        Returns normalized lemma with MyStem tags
        """
        return f'{self.normalized_form}<{self.tags_mystem}>'

    def get_multiple_tagged(self):
        """
        Returns normalized lemma with PyMorphy tags
        """
        return f'{self.normalized_form}<{self.tags_mystem}>({self.tags_pymorphy})'


class CorpusManager:
    """
    Works with articles and stores them
    """

    def __init__(self, path_to_raw_txt_data: str):
        self.path_to_raw_txt_data = path_to_raw_txt_data
        self._storage = {}
        self._scan_dataset()

    def _scan_dataset(self):
        """
        Register each dataset entry
        """
        path = Path(self.path_to_raw_txt_data)

        for file in path.glob('*'):
            if '_raw.txt' in file.name:
                article_id = int(re.search(r'\d+_raw', file.name)[0][:-4])
                self._storage[article_id] = Article(url=None, article_id=article_id)

    def get_articles(self):
        """
        Returns storage params
        """
        return self._storage


class TextProcessingPipeline:
    """
    Process articles from corpus manager
    """

    def __init__(self, corpus_manager: CorpusManager):
        self.corpus_manager = corpus_manager

    def run(self):
        """
        Runs pipeline process scenario
        """
        articles = self.corpus_manager.get_articles().values()
        for article in articles:
            raw_text = article.get_raw_text()

            cleaned_tokens = []
            single_tagged_tokens = []
            multiple_tagged_tokens = []

            for token in self._process(raw_text):
                cleaned_tokens.append(token.get_cleaned())
                single_tagged_tokens.append(token.get_single_tagged())
                multiple_tagged_tokens.append(token.get_multiple_tagged())

            article.save_as(' '.join(cleaned_tokens), kind='cleaned')
            article.save_as(' '.join(single_tagged_tokens), kind='single_tagged')
            article.save_as(' '.join(multiple_tagged_tokens), kind='multiple_tagged')

    def _process(self, raw_text: str):
        """
        Processes each token and creates MorphToken class instance
        """
        pattern = re.compile(r'[а-яА-Яa-zA-z ё]')
        for symbol in raw_text:
            if not pattern.match(symbol):
                clean_text = raw_text.replace(symbol, '')

        analyzed_text = Mystem().analyze(clean_text)
        morph = pymorphy2.MorphAnalyzer()
        tokens = []
        for token in analyzed_text:
            if 'analysis' not in token:
                continue
            if not token['analysis']:
                continue

        for token in analyzed_text:
            morphological_token = MorphologicalToken(original_word=token['text'])
            morphological_token.normalized_form = token['analysis'][0]['lex']
            morphological_token.tags_mystem = token['analysis'][0]['gr']
            tokens.append(morphological_token)
            morphological_token.tags_pymorphy = morph.parse(token['text'])[0].tag

        return tokens


def validate_dataset(path_to_validate):
    """
    Validates folder with assets
    """
    if isinstance(path_to_validate, str):
        path_to_validate = Path(path_to_validate)

    if not path_to_validate.exists():
        raise FileNotFoundError

    if not path_to_validate.is_dir():
        raise NotADirectoryError

    dataset = list(path_to_validate.glob('*'))
    if not dataset:
        raise EmptyDirectoryError

    json_counter = 0
    raw_counter = 0

    for file in sorted(path_to_validate.glob('*'), key=lambda x: int(x.name[:x.name.find('_')])):
        if file.name.endswith('raw.txt'):
            raw_counter += 1

            if f'{raw_counter}_raw' not in file.name:
                raise InconsistentDatasetError

            with open(file, 'r', encoding='utf-8') as this_file:
                text = this_file.read()
            if not text:
                raise InconsistentDatasetError

        if file.name.endswith('meta.json'):
            json_counter += 1

    if json_counter != raw_counter:
        raise InconsistentDatasetError


def main():
    # YOUR CODE HERE
    validate_dataset(ASSETS_PATH)
    corpus_manager = CorpusManager(ASSETS_PATH)
    pipeline = TextProcessingPipeline(corpus_manager)
    pipeline.run()


if __name__ == "__main__":
    main()
