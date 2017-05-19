import nltk




class Analyzer():
    """Implements sentiment analysis."""

    def __init__(self, positives, negatives):

        """Initialize Analyzer."""
        """__init__ loads positive and negative words into memory in such a way that analyze can access them"""
        f_neg = open('negative-words.txt', 'r')
        f_pos = open('positive-words.txt', 'r')
        
        neg_list = []
        pos_list = []
        
        for line in f_neg:
            if not(line.startswith(";")):
                a = str.strip(line)
                if len(a) > 1:
                    neg_list.append(a)
        
        for line in f_pos:
            if not(line.startswith(";")):
                a = str.strip(line)
                if len(a) > 1:
                    pos_list.append(a)
                    
        self.negatives = neg_list
        self.positives = pos_list
        

    def analyze(self, text):
        """Analyze text for sentiment, returning its score."""
        """assign each word in text a value: 1 if the word is in positives, -1 if the word is in negatives, 
        and 0 otherwise consider the sum of those values to be the entire text’s score"""
        score = 0
        for e in self.positives:
            if text == e:
                score +=1

        for y in self.negatives:
            if text == y:
                score += -1
                
        return score
            