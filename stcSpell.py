import os
import locale
import wx
import wx.stc
import sys
import enchant


class STCSpellCheck(object):
    # Class attributes to act as default values
    _spelling_lang = None
    _spelling_dict = None
    
    def __init__(self, stc, *args, **kwargs):
        self.stc = stc
        self.setIndicator(kwargs.get('indicator', 2),
                          kwargs.get('indicator_color', "#FF0000"),
                          kwargs.get('indicator_style', wx.stc.STC_INDIC_SQUIGGLE))
        self.setMinimumWordSize(kwargs.get('min_word_size', 3))
        if 'language' in kwargs:
            # Don't set default language unless explicitly specified -- it
            # might have already been set through the class method
            self.setDefaultLanguage(kwargs['language'])
        if 'check_region' in kwargs:
            # optional function to specify if the region should be spell
            # checked.  Function should return True if the position should
            # be spell-checked; False if it doesn't make sense to spell check
            # that part of the document
            self._spell_check_region = kwargs['check_region']
        else:
            self._spell_check_region = lambda s: True
        self._spelling_debug = False
        
        self._spelling_last_idle_line = -1
        self.dirty_range_count_per_idle = 5
        
        self._no_update = False
        self._last_block = -1
        
        self.clearDirtyRanges()

    def setIndicator(self, indicator=None, color=None, style=None):
        indicators = {0: wx.stc.STC_INDIC0_MASK,
                      1: wx.stc.STC_INDIC1_MASK,
                      2: wx.stc.STC_INDIC2_MASK
                      }
        if indicator is not None:
            if indicator not in indicators:
                indicator = 0
            # The current view may have fewer than 3 indicators
            bitmax = 7 - self.stc.GetStyleBits()
            if indicator > bitmax:
                indicator = bitmax
            self._spelling_indicator = indicator
        self._spelling_indicator_mask = indicators[self._spelling_indicator]
        
        if color is not None:
            self._spelling_color = color
        self.stc.IndicatorSetForeground(self._spelling_indicator,
                                    self._spelling_color)
    
        if style is not None:
            if style > wx.stc.STC_INDIC_MAX:
                style = wx.stc.STC_INDIC_MAX
            self._spelling_style = style
        self.stc.IndicatorSetStyle(self._spelling_indicator,
                               self._spelling_style)
    
    @classmethod
    def getAvailableLanguages(cls):
        try:
            return enchant.list_languages()
        except NameError:
            pass
        return []
    
    @classmethod
    def _getDict(cls, lang):
        try:
            d = enchant.Dict(lang)
        except:
            # Catch all exceptions, because if pyenchant isn't available, you
            # can't catch the enchant.DictNotFound error.
            d = None
        return d

    def setCheckRegion(self, func):
        self.clearAll()
        self._spell_check_region = func

    @classmethod
    def setDefaultLanguage(cls, lang):
        cls._spelling_lang = lang
        cls._spelling_dict = cls._getDict(lang)
    
    def setLanguage(self, lang):
        # Note that this instance variable will shadow the class attribute
        self._spelling_lang = lang
        self._spelling_dict = self._getDict(lang)
    
    def hasDictionary(self):
        return self._spelling_dict is not None

    @classmethod
    def isEnchantOk(cls):
        """Returns True if enchant is available"""
        return 'enchant' in globals()

    @classmethod
    def reloadEnchant(cls, libpath=u''):
        try:
            if libpath and os.path.exists(libpath):
                os.environ['PYENCHANT_LIBRARY_PATH'] = libpath

            if cls.isEnchantOk():
                reload(enchant)
            else:
                mod = __import__('enchant', globals(), locals())
                globals()['enchant'] = mod
        except ImportError:
            return False
        else:
            return True

    def getLanguage(self):
        return self._spelling_lang
    
    def setMinimumWordSize(self, size):
        self._spelling_word_size = size
    
    def clearAll(self):
        """Clear the stc of all spelling indicators."""
        self.stc.StartStyling(0, self._spelling_indicator_mask)
        self.stc.SetStyling(self.stc.GetLength(), 0)
    
    def checkRange(self, start, end):
        spell = self._spelling_dict
        if not spell:
            return
        
        # Remove any old spelling indicators
        mask = self._spelling_indicator_mask
        count = end - start
        if count <= 0:
            if self._spelling_debug:
                print("No need to check range: start=%d end=%d count=%d" % (start, end, count))
            return
        self.stc.StartStyling(start, mask)
        self.stc.SetStyling(count, 0)
        
        text = self.stc.GetTextRange(start, end) # note: returns unicode
        unicode_index = 0
        max_index = len(text)
        
        last_index = 0 # last character in text a valid raw byte position
        last_pos = start # raw byte position corresponding to last_index
        while unicode_index < max_index:
            start_index, end_index = self.findNextWord(text, unicode_index, max_index)
            if end_index >= 0:
                if end_index - start_index >= self._spelling_word_size:
                    if self._spelling_debug:
                        print("checking %s at text[%d:%d]" % (repr(text[start_index:end_index]), start_index, end_index))
                    if not spell.check(text[start_index:end_index]):
                        
                        last_pos += len(text[last_index:start_index].encode('utf-8'))
                        
                        # find the length of the word in raw bytes
                        raw_count = len(text[start_index:end_index].encode('utf-8'))
                        
                        if self._spell_check_region(last_pos):
                            if self._spelling_debug:
                                print("styling text[%d:%d] = (%d,%d) to %d" % (start_index, end_index, last_pos, last_pos + raw_count, mask))
                            self.stc.StartStyling(last_pos, mask)
                            self.stc.SetStyling(raw_count, mask)
                        elif self._spelling_debug:
                            print("not in valid spell check region.  styling position corresponding to text[%d:%d] = (%d,%d)" % (start_index, end_index, last_pos, last_pos + raw_count))
                        last_pos += raw_count
                        last_index = end_index
                unicode_index = end_index
            else:
                break

    def checkAll(self):
        """Perform a spell check on the entire document."""
        return self.checkRange(0, self.stc.GetLength())
    
    def checkSelection(self):
        """Perform a spell check on the currently selected region."""
        return self.checkRange(self.stc.GetSelectionStart(), self.stc.GetSelectionEnd())
    
    def checkLines(self, startline=-1, count=-1):
        if startline < 0:
            startline = self.stc.GetFirstVisibleLine()
        start = self.stc.PositionFromLine(startline)
        if count < 0:
            count = self.stc.LinesOnScreen()
        endline = startline + count
        if endline > self.stc.GetLineCount():
            endline = self.stc.GetLineCount() - 1
        end = self.stc.GetLineEndPosition(endline)
        if self._spelling_debug:
            print("Checking lines %d-%d, chars %d=%d" % (startline, endline, start, end))
        return self.checkRange(start, end)
    
    def checkCurrentPage(self):
        """Perform a spell check on the currently visible lines."""
        return self.checkLines()
    
    def findNextWord(self, utext, index, length):
        while index < length:
            if utext[index].isalpha():
                end = index + 1
                while end < length and utext[end].isalpha():
                    end += 1
                return (index, end)
            index += 1
        return (-1, -1)
    
    def startIdleProcessing(self):
        self._spelling_last_idle_line = 0
        
    def processIdleBlock(self):
        self.processDirtyRanges()
        if self._spelling_last_idle_line < 0:
            return
        if self._spelling_debug:
            print("Idle processing page starting at line %d" % self._spelling_last_idle_line)
        self.checkLines(self._spelling_last_idle_line)
        self._spelling_last_idle_line += self.stc.LinesOnScreen()
        if self._spelling_last_idle_line > self.stc.GetLineCount():
            self._spelling_last_idle_line = -1
            return False
        return True

    def processCurrentlyVisibleBlock(self):
        self.processDirtyRanges()

        self._spelling_last_idle_line = self.stc.GetFirstVisibleLine()
        curr_block = self._spelling_last_idle_line + self.stc.LinesOnScreen()
        if self._no_update or curr_block == self._last_block:
            return

        self.checkLines(self._spelling_last_idle_line)
        self._spelling_last_idle_line += self.stc.LinesOnScreen()
        self._last_block = self._spelling_last_idle_line
        return True

    def getSuggestions(self, word):
        spell = self._spelling_dict
        if spell and len(word) >= self._spelling_word_size:
            words = spell.suggest(word)
            if self._spelling_debug:
                print("suggestions for %s: %s" % (word, words))
            return words
        return []
    
    def checkWord(self, pos=None, atend=False):
        if pos is None:
            pos = self.stc.GetCurrentPos()
        if atend:
            end = pos
        else:
            end = self.stc.WordEndPosition(pos, True)
        start = self.stc.WordStartPosition(pos, True)
        if self._spelling_debug:
            print("%d-%d: %s" % (start, end, self.stc.GetTextRange(start, end)))
        self.checkRange(start, end)
    
    def addDirtyRange(self, start, end, lines_added=0, deleted=False):
        count = end - start
        if deleted:
            count = -count
        if start == self.current_dirty_end:
            self.current_dirty_end = end
        elif start >= self.current_dirty_start and start < self.current_dirty_end:
            self.current_dirty_end += count
        else:
            ranges = []
            if self.current_dirty_start >= 0:
                ranges.append((self.current_dirty_start, self.current_dirty_end))
            for range_start, range_end in self.dirty_ranges:
                if start < range_start:
                    range_start += count
                    range_end += count
                ranges.append((range_start, range_end))
            self.dirty_ranges = ranges
                
            self.current_dirty_start = start
            self.current_dirty_end = end
        
        # If there has been a change before the word that used to be under the
        # cursor, move the pointer so it matches the text
        if start < self.current_word_start:
            self.current_word_start += count
            self.current_word_end += count
        elif start <= self.current_word_end:
            self.current_word_end += count
            # Prevent nonsensical word end if lots of text have been deleted
            if self.current_word_end < self.current_word_start:
                #print("word start = %d, word end = %d" % (self.current_word_start, self.current_word_end))
                self.current_word_end = self.current_word_start
            
        if lines_added > 0:
            start = self.current_dirty_start
            line = self.stc.LineFromPosition(start)
            while True:
                line_end = self.stc.GetLineEndPosition(line)
                if line_end >= end:
                    #self.dirty_ranges.append((start, line_end))
                    if end > start:
                        self.current_dirty_start = start
                        self.current_dirty_end = end
                    else:
                        self.current_dirty_start = self.current_dirty_end = -1
                    break
                self.dirty_ranges.append((start, line_end))
                line += 1
                start = self.stc.PositionFromLine(line)
            
        if self._spelling_debug:
            print("event: %d-%d, current dirty range: %d-%d, older=%s" % (start, end, self.current_dirty_start, self.current_dirty_end, self.dirty_ranges))
    
    def clearDirtyRanges(self, ranges=None):
        """Throw away all dirty ranges
        
        """
        self.current_dirty_start = self.current_dirty_end = -1
        self.current_word_start = self.current_word_end = -1
        if ranges is not None:
            self.dirty_ranges = ranges
        else:
            self.dirty_ranges = []
    
    def processDirtyRanges(self):
        cursor = self.stc.GetCurrentPos()
        
        # Check that the cursor has moved off the current word and if so check
        # its spelling
        if self.current_word_start > 0:
            if cursor < self.current_word_start or cursor > self.current_word_end:
                self.checkRange(self.current_word_start, self.current_word_end)
                self.current_word_start = -1
        
        # Check spelling around the region currently being typed
        if self.current_dirty_start >= 0:
            range_start, range_end = self.processDirtyRange(self.current_dirty_start, self.current_dirty_end)
            
            # If the cursor is in the middle of a word, remove the spelling
            # markers
            if cursor >= range_start and cursor <= range_end:
                word_start = self.stc.WordStartPosition(cursor, True)
                word_end = self.stc.WordEndPosition(cursor, True)
                mask = self._spelling_indicator_mask
                self.stc.StartStyling(word_start, mask)
                self.stc.SetStyling(word_end - word_start, 0)
                
                if word_start != word_end:
                    self.current_word_start = word_start
                    self.current_word_end = word_end
                else:
                    self.current_word_start = -1
            self.current_dirty_start = self.current_dirty_end = -1
        
        # Process a chunk of dirty ranges
        needed = min(len(self.dirty_ranges), self.dirty_range_count_per_idle)
        ranges = self.dirty_ranges[0:needed]
        self.dirty_ranges = self.dirty_ranges[needed:]
        for start, end in ranges:
            if self._spelling_debug:
                print("processing %d-%d" % (start, end))
            self.processDirtyRange(start, end)
    
    def processDirtyRange(self, start, end):
        range_start = self.stc.WordStartPosition(start, True)
        range_end = self.stc.WordEndPosition(end, True)
        if self._spelling_debug:
            print("processing dirty range %d-%d (modified from %d-%d): %s" % (range_start, range_end, start, end, repr(self.stc.GetTextRange(range_start, range_end))))
        self.checkRange(range_start, range_end)
        return range_start, range_end


