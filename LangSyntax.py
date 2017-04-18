import wx
import wx.lib.dialogs
import wx.stc as stc
import keyword
import os
import locale
from Print import TextDocPrintout
from stcSpell import STCSpellCheck
import enchant
import sys
from xml.dom.minidom import parse
import xml.dom.minidom

# Font face data depending on OS
if wx.Platform == '__WXMSW__':
    faces = { 'times': 'Times New Roman',
              'mono' : 'Courier New',
              'helv' : 'Arial',
              'other': 'Comic Sans MS',
              'size' : 10,
              'size2': 8,
             }
elif wx.Platform == '__WXMAC__':
    faces = { 'times': 'Times New Roman',
              'mono' : 'Monaco',
              'helv' : 'Arial',
              'other': 'Comic Sans MS',
              'size' : 12,
              'size2': 10,
             }
else:
    faces = { 'times': 'Times',
              'mono' : 'Courier',
              'helv' : 'Helvetica',
              'other': 'new century schoolbook',
              'size' : 12,
              'size2': 10,
             }

FONTSIZE = 10	

class LangSyntax(object):
	def __init__(self, control, *args, **kwargs):
		self.control = control
		self.normalStylesFore = dict()
		self.normalStylesBack = dict()
		self.langStylesFore = dict()
		self.langStylesBack = dict()
		
	def OnPythonSyntax(self, e):
		self.control.SetLexer(stc.STC_LEX_PYTHON)
		self.control.SetKeyWords(0," ".join(keyword.kwlist))
		self.control.SetViewWhiteSpace(False)
		self.control.SetProperty("fold", "1")
		self.control.SetProperty("tab.timmy.whinge.level", "1")
		# Set all the theme settings
		self.ParseSettings("settings.xml")
		self.PythonSetStyling()
	
	def OnPerlSyntax(self, e):
		self.control.SetLexer(stc.STC_LEX_PERL)
		self.control.SetKeyWords(0," ".join(keyword.kwlist))
		self.control.SetViewWhiteSpace(False)
		self.control.SetProperty("fold", "1")
		self.control.SetProperty("tab.timmy.whinge.level", "1")
		self.ParseSettings("settings.xml")
		self.PerlSetStyling()

	def OnCppSyntax(self, e):
		self.control.SetLexer(stc.STC_LEX_CPP)
		self.control.SetKeyWords(0," ".join(keyword.kwlist))
		self.control.SetViewWhiteSpace(False)
		self.control.SetProperty("fold", "1")
		self.control.SetProperty("tab.timmy.whinge.level", "1")
		self.ParseSettings("settings.xml")
		self.CppSetStyling()

# Parses an XML settings file for styling and configuring the text editor
	def ParseSettings(self, settings_file):
		# Open XML document using minidom parser
		DOMTree = xml.dom.minidom.parse(settings_file)
		collection = DOMTree.documentElement # Root element
		
		# Get all the styles in the collection
		styles = collection.getElementsByTagName("style")
		for s in styles:
			item = s.getElementsByTagName("item")[0].childNodes[0].data
			color = s.getElementsByTagName("color")[0].childNodes[0].data
			side = s.getElementsByTagName("side")[0].childNodes[0].data
			sType = s.getAttribute("type")
			if sType == "normal":
				if side == "Back": # background
					self.normalStylesBack[str(item)] = str(color)
				else:
					self.normalStylesFore[str(item)] = str(color)
			elif sType == "langsyntaxstyle":
				if side == "Back":
					self.langStylesBack[str(item)] = str(color)
				else:
					self.langStylesFore[str(item)] = str(color)			
	

	# Python Setting the styles
	def PythonSetStyling(self):
		# Set the general foreground and background for normal and python styles
		pSFore = self.langStylesFore
		pSBack = self.langStylesBack
		nSFore = self.normalStylesFore
		nSBack = self.normalStylesBack

		# Python styles
		self.control.StyleSetBackground(stc.STC_STYLE_DEFAULT, nSBack["Main"])
		self.control.SetSelBackground(True, "#333333")

		# Default
		self.control.StyleSetSpec(stc.STC_P_DEFAULT, "fore:%s,back:%s" % (pSFore["Default"], pSBack["Default"]))
		self.control.StyleSetSpec(stc.STC_P_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)

		# Comments
		self.control.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:%s,back:%s" % (pSFore["Comment"], pSBack["Comment"]))
		self.control.StyleSetSpec(stc.STC_P_COMMENTLINE, "face:%(other)s,size:%(size)d" % faces)

		# Number
		self.control.StyleSetSpec(stc.STC_P_NUMBER, "fore:%s,back:%s" % (pSFore["Number"], pSBack["Number"]))
		self.control.StyleSetSpec(stc.STC_P_NUMBER, "size:%(size)d" % faces)

		# String
		self.control.StyleSetSpec(stc.STC_P_STRING, "fore:%s,back:%s" % (pSFore["String"], pSBack["Number"]))
		self.control.StyleSetSpec(stc.STC_P_STRING, "face:%(helv)s,size:%(size)d" % faces)

		# Single-quoted string
		self.control.StyleSetSpec(stc.STC_P_CHARACTER, "fore:%s,back:%s" % (pSFore["SingleQuoteString"], pSBack["SingleQuoteString"]))
		self.control.StyleSetSpec(stc.STC_P_CHARACTER, "face:%(helv)s,size:%(size)d" % faces)

		# Keyword
		self.control.StyleSetSpec(stc.STC_P_WORD, "fore:%s,back:%s" % (pSFore["Keyword"], pSBack["Keyword"]))
		self.control.StyleSetSpec(stc.STC_P_WORD, "bold,size:%(size)d" % faces)

		# Triple quotes
		self.control.StyleSetSpec(stc.STC_P_TRIPLE, "fore:%s,back:%s" % (pSFore["TripleQuote"], pSBack["TripleQuote"]))
		self.control.StyleSetSpec(stc.STC_P_TRIPLE, "size:%(size)d" % faces)

		# Triple double quotes
		self.control.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:%s,back:%s" % (pSFore["TripleDoubleQuote"], pSBack["TripleDoubleQuote"]))
		self.control.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "size:%(size)d" % faces)

		# Class name definition
		self.control.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:%s,back:%s" % (pSFore["ClassName"], pSBack["ClassName"]))
		self.control.StyleSetSpec(stc.STC_P_CLASSNAME, "bold,underline,size:%(size)d" % faces)

		# Function name definition
		self.control.StyleSetSpec(stc.STC_P_DEFNAME, "fore:%s,back:%s" % (pSFore["FunctionName"], pSBack["FunctionName"]))
		self.control.StyleSetSpec(stc.STC_P_DEFNAME, "bold,size:%(size)d" % faces)

		# Operators
		self.control.StyleSetSpec(stc.STC_P_OPERATOR, "fore:%s,back:%s" % (pSFore["Operator"], pSBack["Operator"]))
		self.control.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)

		# Identifiers
		self.control.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:%s,back:%s" % (pSFore["Identifier"], pSBack["Identifier"]))
		self.control.StyleSetSpec(stc.STC_P_IDENTIFIER, "face:%(helv)s,size:%(size)d" % faces)

		# Comment blocks
		self.control.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:%s,back:%s" % (pSFore["CommentBlock"], pSBack["CommentBlock"]))
		self.control.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "size:%(size)d" % faces)

		# End of line where string is not closed
		self.control.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:%s,back:%s" % (pSFore["StringEOL"], pSBack["StringEOL"]))
		self.control.StyleSetSpec(stc.STC_P_STRINGEOL, "face:%(mono)s,eol,size:%(size)d" % faces)

		# Caret/Insertion Point
		self.control.SetCaretForeground(pSFore["Caret"])
		self.control.SetCaretLineBackground(pSBack["CaretLine"])
		self.control.SetCaretLineVisible(True)


	# Perl Setting the styles
	def PerlSetStyling(self):
		# Set the general foreground and background for normal and python styles
		pSFore = self.langStylesFore
		pSBack = self.langStylesBack
		nSFore = self.normalStylesFore
		nSBack = self.normalStylesBack

		# Python styles
		self.control.StyleSetBackground(stc.STC_STYLE_DEFAULT, nSBack["Main"])
		self.control.SetSelBackground(True, "#333333")

		# Default
		self.control.StyleSetSpec(stc.STC_PL_DEFAULT, "fore:%s,back:%s" % (pSFore["Default"], pSBack["Default"]))
		self.control.StyleSetSpec(stc.STC_PL_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)

		# Comments
		self.control.StyleSetSpec(stc.STC_PL_COMMENTLINE, "fore:%s,back:%s" % (pSFore["Comment"], pSBack["Comment"]))
		self.control.StyleSetSpec(stc.STC_PL_COMMENTLINE, "face:%(other)s,size:%(size)d" % faces)

		# Number
		self.control.StyleSetSpec(stc.STC_PL_NUMBER, "fore:%s,back:%s" % (pSFore["Number"], pSBack["Number"]))
		self.control.StyleSetSpec(stc.STC_PL_NUMBER, "size:%(size)d" % faces)

		# String
		self.control.StyleSetSpec(stc.STC_PL_STRING, "fore:%s,back:%s" % (pSFore["String"], pSBack["Number"]))
		self.control.StyleSetSpec(stc.STC_PL_STRING, "face:%(helv)s,size:%(size)d" % faces)


		# Single-quoted string
		self.control.StyleSetSpec(stc.STC_PL_CHARACTER, "fore:%s,back:%s" % (pSFore["SingleQuoteString"], pSBack["SingleQuoteString"]))
		self.control.StyleSetSpec(stc.STC_PL_CHARACTER, "face:%(helv)s,size:%(size)d" % faces)

		# Keyword
		self.control.StyleSetSpec(stc.STC_PL_WORD, "fore:%s,back:%s" % (pSFore["Keyword"], pSBack["Keyword"]))
		self.control.StyleSetSpec(stc.STC_PL_WORD, "bold,size:%(size)d" % faces)


		# Operators
		self.control.StyleSetSpec(stc.STC_PL_OPERATOR, "fore:%s,back:%s" % (pSFore["Operator"], pSBack["Operator"]))
		self.control.StyleSetSpec(stc.STC_PL_OPERATOR, "bold,size:%(size)d" % faces)

		# Identifiers
		self.control.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:%s,back:%s" % (pSFore["Identifier"], pSBack["Identifier"]))
		self.control.StyleSetSpec(stc.STC_P_IDENTIFIER, "face:%(helv)s,size:%(size)d" % faces)


		# Caret/Insertion Point
		self.control.SetCaretForeground(pSFore["Caret"])
		self.control.SetCaretLineBackground(pSBack["CaretLine"])
		self.control.SetCaretLineVisible(True)

	# Cpp Setting the styles
	def CppSetStyling(self):
		# Set the general foreground and background for normal and python styles
		pSFore = self.langStylesFore
		pSBack = self.langStylesBack
		nSFore = self.normalStylesFore
		nSBack = self.normalStylesBack

		# Python styles
		self.control.StyleSetBackground(stc.STC_STYLE_DEFAULT, nSBack["Main"])
		self.control.SetSelBackground(True, "#333333")

		# Default
		self.control.StyleSetSpec(stc.STC_C_DEFAULT, "fore:%s,back:%s" % (pSFore["Default"], pSBack["Default"]))
		self.control.StyleSetSpec(stc.STC_C_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)

		# Comments
		self.control.StyleSetSpec(stc.STC_C_COMMENTLINE, "fore:%s,back:%s" % (pSFore["Comment"], pSBack["Comment"]))
		self.control.StyleSetSpec(stc.STC_C_COMMENTLINE, "face:%(other)s,size:%(size)d" % faces)

		# Number
		self.control.StyleSetSpec(stc.STC_C_NUMBER, "fore:%s,back:%s" % (pSFore["Number"], pSBack["Number"]))
		self.control.StyleSetSpec(stc.STC_C_NUMBER, "size:%(size)d" % faces)

		# String
		self.control.StyleSetSpec(stc.STC_C_STRING, "fore:%s,back:%s" % (pSFore["String"], pSBack["Number"]))
		self.control.StyleSetSpec(stc.STC_C_STRING, "face:%(helv)s,size:%(size)d" % faces)


		# Single-quoted string
		self.control.StyleSetSpec(stc.STC_C_CHARACTER, "fore:%s,back:%s" % (pSFore["SingleQuoteString"], pSBack["SingleQuoteString"]))
		self.control.StyleSetSpec(stc.STC_C_CHARACTER, "face:%(helv)s,size:%(size)d" % faces)

		# Keyword
		self.control.StyleSetSpec(stc.STC_C_WORD, "fore:%s,back:%s" % (pSFore["Keyword"], pSBack["Keyword"]))
		self.control.StyleSetSpec(stc.STC_C_WORD, "bold,size:%(size)d" % faces)


####

		# PREPROCESSOR  quotes
		self.control.StyleSetSpec(stc.STC_C_PREPROCESSOR, "fore:%s,back:%s" % (pSFore["FunctionName"], pSBack["FunctionName"]))
		self.control.StyleSetSpec(stc.STC_C_PREPROCESSOR, "size:%(size)d" % faces)

		# GLOBAL Class name definition
		self.control.StyleSetSpec(stc.STC_C_GLOBALCLASS, "fore:%s,back:%s" % (pSFore["ClassName"], pSBack["ClassName"]))
		self.control.StyleSetSpec(stc.STC_C_GLOBALCLASS, "bold,underline,size:%(size)d" % faces)

		'''# Function name definition
		self.control.StyleSetSpec(stc.STC_P_DEFNAME, "fore:%s,back:%s" % (pSFore["FunctionName"], pSBack["FunctionName"]))
		self.control.StyleSetSpec(stc.STC_P_DEFNAME, "bold,size:%(size)d" % faces)'''

		# Operators
		self.control.StyleSetSpec(stc.STC_C_OPERATOR, "fore:%s,back:%s" % (pSFore["Operator"], pSBack["Operator"]))
		self.control.StyleSetSpec(stc.STC_C_OPERATOR, "bold,size:%(size)d" % faces)

		# Identifiers
		self.control.StyleSetSpec(stc.STC_C_IDENTIFIER, "fore:%s,back:%s" % (pSFore["Identifier"], pSBack["Identifier"]))
		self.control.StyleSetSpec(stc.STC_C_IDENTIFIER, "face:%(helv)s,size:%(size)d" % faces)


		# Caret/Insertion Point
		self.control.SetCaretForeground(pSFore["Caret"])
		self.control.SetCaretLineBackground(pSBack["CaretLine"])
		self.control.SetCaretLineVisible(True)
