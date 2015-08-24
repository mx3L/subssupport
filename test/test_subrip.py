import os
import sys
import unittest

test = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(test, '..', 'plugin'))

from parsers import SubRipParser, MicroDVDParser

PARSERS = [SubRipParser, MicroDVDParser]

cheers_text ="""
2
00:00:04,604 --> 00:00:06,205
Quite a night,                  
huh, Norm?                      

3
00:00:06,272 --> 00:00:08,640
                        Yep.    
    Yeah.                       

4
00:00:08,708 --> 00:00:12,077
        I can't believe         
  old Sammy wants to be a dad.  

5
00:00:12,178 --> 00:00:14,213
              Yep.              

6
00:00:14,280 --> 00:00:16,548
  He's got to be real careful   
    about choosing a mother.
"""


class TestSubRipBlockParser (unittest.TestCase):
    def setUp(self):
      self.parser = SubRipParser()
      
    def test_cheers(self):
        for s in self.parser.parse(cheers_text):
            print s
        
        
        
