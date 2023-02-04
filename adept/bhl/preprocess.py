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
        text = self.strip_new_lines(text)
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

    def strip_new_lines(self, text):
        text = text.strip('\n')
        text = text.strip('\r')  
        return text    
    
    
class BHLParagraphizer:   
    
    def __init__(self, text):
        self.__paragraphs = []

        lines = text.split('\n')
        line_lens = np.array([len(l) for l in lines if len(l) and not l.endswith('.')])

        try:
            self.median_line_length = np.median(line_lens)
            self.max_line_length = np.max(line_lens)        
        except ValueError:
            print('Page has no lines without fullstop ')
        else:
            self.abnormal_line_length = self.median_line_length - (self.max_line_length - self.median_line_length) - 10
            paragraphs = self.split_newline_paragraphs(text)
            self.__paragraphs = self.split_line_length_paragraphs(paragraphs)
        
    def split_newline_paragraphs(self, text):
        """
        Loop through and split text on double new lines - but check 
        that the paragraph starts with a capital
        """
        paras = []

        for para in text.split('\n\n'):

            para = para.strip()

            # If para continains no text, skip it         
            if not len(para):
                continue

            if paras:
                last_para = paras[-1]

                # If the first word of the paragraph isn't capitalised, and the last para doesn't end with a . -> append to previous para             
                if not para[0].isupper() and not last_para.endswith('.'):           
                    paras[-1] += ' ' + para
                    continue

            paras.append(para)

        return paras  
    
    def split_line_length_paragraphs(self, paragraphs):
        
        new_paragraphs = []
        self._line_buffer = []
        
        def _commit_line_buffer():
            if self._line_buffer:
                new_paragraphs.append('\n'.join(self._line_buffer))
                self._line_buffer = []   

        for para in paragraphs: 

            lines = para.split('\n')

            for i, line in enumerate(lines):
                
                self._line_buffer.append(line)
                
                next_i = i+1
                # If this is the last line in the paragraph, do not examine further         
                if next_i < len(lines):
                    
                    next_line = lines[next_i]
                    next_word = next_line.split()[0]   
                    next_word_is_capitalised = next_word[0].isupper() or next_word[0].isnumeric()

                    # If line len plus next word is less that the median (it could have fitted on a single line)
                    line_with_next_word_below_median = (len(line) + len(next_word)) < self.median_line_length
                    
                    if line.endswith('.') and not self._endswith_ellipsis(line) and next_word_is_capitalised:          
                        if line_with_next_word_below_median:
                            _commit_line_buffer()

                    elif len(line) < self.abnormal_line_length and line_with_next_word_below_median and next_word_is_capitalised:
                        _commit_line_buffer()
                        pass

            # End of lines loop             
            _commit_line_buffer()
                        
        return new_paragraphs
    
    @staticmethod
    def _endswith_ellipsis(text):
        # Regex to match dots and white space at end of string  
        # TODO: A single regex can do this.     
        # TODO: Move to helpers     
        if match := re.search('([\. ]+)$', text):
            # Remove whitespace and see if match len 2 or more                  
            return len(match.group(0).replace(' ', '')) > 1
        
        return False    
    
    def __iter__(self):
        return iter(self.__paragraphs)       