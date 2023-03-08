import numpy as np
import re

      
class BHLPreprocess:  
    
    # Match whitesapce, but excluding \r and \n
    _whitespace_regex = re.compile(r'(?:(?!\n)\s)+') 
    _variety_regex = re.compile(r'(\s)[v|y]a[v|r][,|.]\s?', re.IGNORECASE)
    # Join words that are broken across sentences
    _paragraph_hypenation_regex = re.compile(r'(\w)-[\s\n]+')
    # New lines not following a full stop with negative look behind
    _sentence_break_regex = re.compile(r'(?<!\.|\n)[\n]+')

    def __call__(self, text):
        text = self.normalise_variety(text)
        text = self.replace_paragraph_hyphenation(text)
        text = self.remove_sentence_new_lines(text)
        text = self.remove_extra_spaces(text)
        return text

    def normalise_variety(self, text):
        # Correct common mispellings of variety (var.)
        # var, => var.
        # yar. => var.
        # yav, => var.
        return self._variety_regex.sub(r'\g<1>var. ', text)

    def replace_paragraph_hyphenation(self, text):
        return self._paragraph_hypenation_regex.sub(r'\g<1>', text)

    def remove_sentence_new_lines(self, text):
        return self._sentence_break_regex.sub(' ', text)

    def remove_extra_spaces(self, text):
        return self._whitespace_regex.sub(' ', text)
      