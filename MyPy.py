import wx
import wx.lib.dialogs
import wx.stc as stc
import keyword
import os
import locale
from Print import TextDocPrintout
from stcSpell import STCSpellCheck
from LangSyntax import LangSyntax
from xml.dom.minidom import parse
import xml.dom.minidom
import sys


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

FONTSIZE = 12			 

# Application Framework
class MainWindow(wx.Frame):
	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)
		self.log = kwargs
		self.dirname = ''
		self.filename = ''
	
		self.lineNumbersEnabled = True
		self.leftMarginWidth = 25

		# Initialize the application Frame and create the Styled Text Control
		
		self.SetTitle("My Py Editor")
		self.control = stc.StyledTextCtrl(self, style=wx.TE_MULTILINE | wx.TE_WORDWRAP) 
		self.control.spell = STCSpellCheck(self.control, language="en_US") #new
		self.control.syntax = LangSyntax(self.control, language="en_US")
		
		self.control.CmdKeyAssign(ord('='), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN) # Ctrl + = to zoom in
		self.control.CmdKeyAssign(ord('-'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT) # Ctrl + - to zoom out
		

		self.control.SetViewWhiteSpace(False)
		# Set margins
		self.control.SetMargins(5,0) # 5px margin on left inside of text control
		self.control.SetMarginType(1, stc.STC_MARGIN_NUMBER) # line numbers column
		self.control.SetMarginWidth(1, self.leftMarginWidth) # width of line numbers column


		# new code font 2517
		self.currentFont = self.control.GetFont()
		self.currentColor = wx.BLACK
		
		self.findData = wx.FindReplaceData()
		#self.findreplacedlg = None

		#new 1728
		self.Bind(wx.stc.EVT_STC_MODIFIED, self.OnModified)
            	self.Bind(wx.EVT_IDLE, self.OnIdle)
            	self.modified_count = 0
            	self.idle_count = 0
		
		
		# Create the status bar at the bottom
		self.CreateStatusBar()
		self.UpdateLineCol(self) # show the line #, row # in status bar
		self.StatusBar.SetBackgroundColour((220,220,220))

		# file menu
		filemenu = wx.Menu()
		menuNew = filemenu.Append(wx.ID_NEW, "&New", " Create a new document (Ctrl+N)")
		menuOpen = filemenu.Append(wx.ID_OPEN, "&Open", " Open an existing document (Ctrl+O)")
		menuSave = filemenu.Append(wx.ID_SAVE, "&Save", " Save the current document (Ctrl+S)")
		menuSaveAs = filemenu.Append(wx.ID_SAVEAS, "Save &As", " Save a new document (Alt+S)")
		filemenu.AppendSeparator()
		# new code
		pageSetupMenu = filemenu.Append(-1, "Page Setup...\tF5", "Setup page margins and etc.")
		printMenu = filemenu.Append(-1, "Print...\tF8", "Print the document")
		filemenu.AppendSeparator()
		menuClose = filemenu.Append(wx.ID_EXIT, "&Close", " Close the application (Ctrl+W)")

		# initialize the print data (new code)
		self.pdata = wx.PrintData()
		self.pdata.SetPaperId(wx.PAPER_LETTER)
		self.pdata.SetOrientation(wx.PORTRAIT)
		self.margins = (wx.Point(15,15), wx.Point(15,15))
		
		#Edit menu
		editmenu = wx.Menu()
		menuUndo = editmenu.Append(wx.ID_UNDO, "&Undo", " Undo last action (Ctrl+Z)")
		menuRedo = editmenu.Append(wx.ID_REDO, "&Redo", " Redo last action (Ctrl+Y)")
		editmenu.AppendSeparator()
		menuSelectAll = editmenu.Append(wx.ID_SELECTALL, "&Select All", " Select the entire document (Ctrl+A)")
		menuCopy = editmenu.Append(wx.ID_COPY, "&Copy", " Copy selected text (Ctrl+C)")
		menuCut = editmenu.Append(wx.ID_CUT, "C&ut", " Cut selected text (Ctrl+X)")
		menuPaste = editmenu.Append(wx.ID_PASTE, "&Paste", " Pasted text from the clipboard (Ctrl+V)")

		# Preferences menu
		prefmenu = wx.Menu()
		menuLineNumbers = prefmenu.Append(wx.ID_ANY, "Toggle &Line Numbers", " Show/Hide the line numbers column")

		# help menu
		helpmenu = wx.Menu()
		menuHowTo = helpmenu.Append(wx.ID_ANY, "&How To...", " Get help using this")
		helpmenu.AppendSeparator()
		menuAbout = helpmenu.Append(wx.ID_ABOUT, "&About", " Read about the text editor and it's making")

		# new code font menu 130117
		view = wx.Menu()
		menuFont = view.Append(wx.ID_ANY, "&Font", "Choose Font")
		#menuFind = view.Append(wx.ID_ANY, "&Find", "Find...")	#new 0212
		
		menuFind = view.Append(wx.ID_ANY, "&Find...", "Find Text")
		menuReplace = view.Append(wx.ID_ANY, "Replace", "Replace Text")
		
		# new code lan repub17
		langMenu =wx.Menu()
		
		# syntax 
		syntaxMenu = wx.Menu()
		cppSyntaxMenu = syntaxMenu.Append(wx.ID_ANY, "&C++" , "C++ Syntax")
		pythonSyntaxMenu = syntaxMenu.Append(wx.ID_ANY, "&Python" , "Python Syntax")
		perlSyntaxMenu = syntaxMenu.Append(wx.ID_ANY, "&Perl", "perl Syntax")
		

		
		
		# Creating menubar
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu, "&File")
		menuBar.Append(editmenu, "&Edit")
		menuBar.Append(prefmenu, "&Preferences")
		menuBar.Append(view, "&View")	# new code 130117
		menuBar.Append(langMenu, "&Languages")
		menuBar.Append(syntaxMenu, "&Syntax")
		menuBar.Append(helpmenu, "&Help")
		
		#menuBar.Append(lang, "Languages")
		self.SetMenuBar(menuBar)

		# File event
		self.Bind(wx.EVT_MENU, self.OnNew, menuNew)
		self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
		self.Bind(wx.EVT_MENU, self.OnSave, menuSave)
		self.Bind(wx.EVT_MENU, self.OnSaveAs, menuSaveAs)
		self.Bind(wx.EVT_MENU, self.OnPageSetup, pageSetupMenu)
		#self.Bind(wx.EVT_MENU, self.OnPrintSetup, printSetupMenu)
		#self.Bind(wx.EVT_MENU, self.OnPrintPreview, printPreviewMenu)
		self.Bind(wx.EVT_MENU, self.OnPrint, printMenu)
		self.Bind(wx.EVT_MENU, self.OnClose, menuClose)

		# Edit event
		self.Bind(wx.EVT_MENU, self.OnUndo, menuUndo)
		self.Bind(wx.EVT_MENU, self.OnRedo, menuRedo)
		self.Bind(wx.EVT_MENU, self.OnSelectAll, menuSelectAll)
		self.Bind(wx.EVT_MENU, self.OnCopy, menuCopy)
		self.Bind(wx.EVT_MENU, self.OnCut, menuCut)
		self.Bind(wx.EVT_MENU, self.OnPaste, menuPaste)

		# Preference events
		self.Bind(wx.EVT_MENU, self.OnToggleLineNumbers, menuLineNumbers)

		# Help event
		self.Bind(wx.EVT_MENU, self.OnHowTo, menuHowTo)
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)

		# New code start Font Code
		self.Bind(wx.EVT_MENU, self.OnFont, menuFont)
		
		#
		self.Bind(wx.EVT_MENU, self.OnShowFind, menuFind)
		self.Bind(wx.EVT_MENU, self.OnShowFindReplace, menuReplace)
		
		#self.Bind(wx.EVT_FIND, self.OnFind)
		#self.Bind(wx.EVT_FIND_NEXT, self.OnFind)
		#self.Bind(wx.EVT_FIND_REPLACE, self.OnReplace)
		#self.Bind(wx.EVT_FIND_REPLACE_ALL, self.OnReplaceAll)
		#self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
		
		
		# Key
		self.control.Bind(wx.EVT_CHAR, self.OnCharEvent)
		self.control.Bind(wx.EVT_KEY_UP, self.UpdateLineCol)
		self.control.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		
		# Syntax
		self.Bind(wx.EVT_MENU, self.control.syntax.OnPythonSyntax, pythonSyntaxMenu)
		self.Bind(wx.EVT_MENU, self.control.syntax.OnPerlSyntax, perlSyntaxMenu)
		self.Bind(wx.EVT_MENU, self.control.syntax.OnCppSyntax, cppSyntaxMenu)

		# new 1728
		langs = self.control.spell.getAvailableLanguages()
		self.lang_id = {}
		for lang in langs:
			id = wx.NewId()
			self.lang_id = lang
			self.menuAdd(langMenu, lang, "Change Dictionary to %s" %lang, self.OnChangeLanguage, id=id)

		# display application
		self.Show()

		

	# New document
	def OnNew(self, e):
		self.filename = ""
		self.control.SetValue("")

	# Open existing document
	def OnOpen(self, e):
		try:
			dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.FD_OPEN)
			if (dlg.ShowModal() == wx.ID_OK):
				self.filename = dlg.GetFilename()
				self.dirname = dlg.GetDirectory()
				f = open(os.path.join(self.dirname, self.filename), 'r')
				self.control.SetValue(f.read())
				f.close()
			dlg.Destroy()
		except:
			dlg = wx.MessageDialog(self, " Couldn't open file", "Error 009", wx.ICON_ERROR)
			dlg.ShowModal()
			dlg.Destroy()

	# Save the document
	def OnSave(self, e):
		try:
			f = open(os.path.join(self.dirname, self.filename), 'w')
			f.write(self.control.GetValue())
			f.close()
		except:
			try:
				# If regular save fails, try the Save As method.
				dlg = wx.FileDialog(self, "Save file as", self.dirname, "Untitled", "*.*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
				if (dlg.ShowModal() == wx.ID_OK):
					self.filename = dlg.GetFilename()
					self.dirname = dlg.GetDirectory()
					f = open(os.path.join(self.dirname, self.filename), 'w')
					f.write(self.control.GetValue())
					f.close()
				dlg.Destroy()
			except:
				pass

	# Save as new document
	def OnSaveAs(self, e):
		try:
			dlg = wx.FileDialog(self, "Save file as", self.dirname, self.filename, "*.*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
			if (dlg.ShowModal() == wx.ID_OK):
				self.filename = dlg.GetFilename()
				self.dirname = dlg.GetDirectory()
				f = open(os.path.join(self.dirname, self.filename), 'w')
				f.write(self.control.GetValue())
				f.close()
			dlg.Destroy()
		except:
			pass

	# Terminate the program menu action
	def OnClose(self, e):
		self.Close(True)

	# Undo event menu action
	def OnUndo(self, e):
		self.control.Undo()

	# Redo event menu action
	def OnRedo(self, e):
		self.control.Redo()

	# Select All text menu action
	def OnSelectAll(self, e):
		self.control.SelectAll()

	# Copy selected text menu action
	def OnCopy(self, e):
		self.control.Copy()

	# Cut selected text menu action
	def OnCut(self, e):
		self.control.Cut()

	# Paste text from clipboard menu action
	def OnPaste(self, e):
		self.control.Paste()

	# Toggle Line numbers menu action
	def OnToggleLineNumbers(self, e):
		if (self.lineNumbersEnabled):
			self.control.SetMarginWidth(1,0)
			self.lineNumbersEnabled = False
		else:
			self.control.SetMarginWidth(1, self.leftMarginWidth)
			self.lineNumbersEnabled = True

	# How To menu
	def OnHowTo(self, e):
		dlg = wx.lib.dialogs.ScrolledMessageDialog(self, "Contact us How it Works. We don't think You need help if you try. It is Very Simple :). ", "How To..." , size=(400,400))
		dlg.ShowModal()
		dlg.Destroy()

	# Show About menu action
	def OnAbout(self, e):
		dlg = wx.MessageDialog(self, " This is My Py Beta Version 1.0.", "About" ,wx.OK)
		dlg.ShowModal()
		dlg.Destroy()

	# Update the Line/Col in status bar
	def UpdateLineCol(self, e):
		line = self.control.GetCurrentLine() + 1
		col = self.control.GetColumn(self.control.GetCurrentPos())
		stat = "Line %s, Column %s" % (line, col)
		self.StatusBar.SetStatusText(stat, 0)

	# Left mouse up
	def OnLeftUp(self, e):
		# This way if you click on another position in the text box
		# it will update the line/col number in the status bar (like it should)
		self.UpdateLineCol(self)
		e.Skip()

	# New Code Font Font Fuction
	def OnFont(self, e):
		data = wx.FontData()
		data.EnableEffects(True)
		data.SetColour(self.currentColor)
		data.SetInitialFont(self.currentFont)
		dlg = wx.FontDialog(self, data)
		
		if dlg.ShowModal() == wx.ID_OK:
			data = dlg.GetFontData()
			font = data.GetChosenFont()
			colour = data.GetColour()			
			self.currentFont = font
			self.currentColor = colour
			self.OnUpdateFont()			
		dlg.Destroy()
		
	def OnUpdateFont(self):
		self.control.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, self.currentFont)
	

	'''def _initFindDialog(self, mode):
		if self.findreplacedlg:
			self.findreplacedlg.Destroy()
			style = (wx.FR_NOUPDOWN | wx.FR_NOMATCHCASE | wx.FR_NOWHOLEWORD)
		if mode == wx.ID_REPLACE:
			style |= wx.FR_REPLACEDIALOG
		dlg = wx.FindReplaceDialog(self, self.findData, None, style)
		self.findreplacedlg = dlg'''
	
		
	'''def OnShowFind(self, e):
		event_id = e.GetId()
		if event_id in (wx.ID_FIND, wx.ID_REPLACE):
			self._initFindDialog(event_id)
			self.findreplacedlg.Show()
		else:
			e.Skip()
			
	def OnFind(self, e):
		findstr = self.findreplacedlg.GetFindString()
		if not self.FindString(findstr):
			wx.Bell()
			
	def OnReplace(self, e):
		replacestr = self.findData.GetReplaceString()
		fstring = self.findData.GetFindString()
		cpos = self.GetInsertionPoint()
		start, end = cpos, cpos
		if fstring:
			if self.FindString(fstring):
				start, end = self.control.GetSelection()
		self.control.Replace(start, end, replacestr)
		
	def OnReplaceAll(self, e):
		replacestr = self.findData.GetReplaceString()
		fstring = self.findData.GetFindString()
		text = self.control.GetValue()
		newtext = text.replace(fstring, replacestr)
		self.control.SetValue(newtext)
		
	def OnFindClose(self, e):
		if self.findreplacedlg:
			self.findreplacedlg.Destroy()
			self.findreplacedlg = None
			
	def FindString(self, findstring):
		text = self.control.GetValue()
		cselect = self.control.GetSelection()
		if (cselect[0]!= cselect[1]):
			cpos = max(cselect)
		else:
			cpos = self.control.GetInsertionPoint()
		if cpos == self.control.GetLastPosition():
			cpos = 0
		text = text.upper()
		findstring = findstring.upper()
		found = text.find(findstr, cpos)
		if found != -1:
			end = found + len(findstring)
			self.control.SetSelection(end, found)
			self.control.SetFocus()
			return True
		return False
	
	'''
	
	def BindFindEvents(self, e):
		e.Bind(wx.EVT_FIND, self.OnFind)
		e.Bind(wx.EVT_FIND_NEXT, self.OnFind)
		e.Bind(wx.EVT_FIND_REPLACE, self.OnFind)
		e.Bind(wx.EVT_FIND_REPLACE_ALL, self.OnFind)
		e.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
	
	def OnShowFind(self, e):
		dlg = wx.FindReplaceDialog(self, self.findData, "Find")
		self.BindFindEvents(dlg)
		dlg.Show(True)
		
	def OnShowFindReplace(self, e):
		dlg = wx.FindReplaceDialog(self, self.findData, "Find & Replace", wx.FR_REPLACEDIALOG)
		self.BindFindEvents(dlg)
		dlg.Show(True)
		
	def OnFind(self, e):
		map = {
			wx.wxEVT_COMMAND_FIND : "FIND",
			wx.wxEVT_COMMAND_FIND_NEXT : "FIND NEXT",
			wx.wxEVT_COMMAND_FIND_REPLACE : "REPLACE",
			wx.wxEVT_COMMAND_FIND_REPLACE_ALL : "REPLACE ALL",
		}
		
		event = e.GetEventType()
		
		if event in map:
			eventType = map[event]			
		else:
			eventType = "**Unknown Event Type**"
			
		if event in [wx.wxEVT_COMMAND_FIND_REPLACE, wx.wxEVT_COMMAND_FIND_REPLACE_ALL]:
			replaceText = "Replace Text: %s" % e.GetReplaceString()
		else:
			replaceText = ""
			
		self.log.write("%s -- Find text: %s %s Flags: %d \n" % (eventType, e.GetFindString(), replaceText, e.GetFlags()))
		
	
	def OnFindClose(self, e):
		self.log.write("FindReplaceDialog closing...\n")
		e.GetDialog().Destroy()
		
	
	
	
	# Char event
	def OnCharEvent(self, e):
		keycode = e.GetKeyCode()
		altDown = e.AltDown()		
		if (keycode == 14): # Ctrl + N
			self.OnNew(self)
		elif (keycode == 15): # Ctrl + O
			self.OnOpen(self)
		elif (keycode == 19): # Ctrl + S
			self.OnSave(self)
		elif (altDown and (keycode == 115)): # Alt + S
			self.OnSaveAs(self)
		elif (keycode == 23): # Ctrl + W
			self.OnClose(self)
		elif (keycode == 1): # Ctrl + A
			self.OnSelectAll(self)
		elif (keycode == 340): # F1
			self.OnHowTo(self)
		elif (keycode == 341): # F2
			self.OnAbout(self)
		else:
			e.Skip()
	
	
	# new code 172201
	def OnClearSelection(self, evt):
		evt.Skip()
		wx.CallAfter(self.control.SetInsertionPoint,
		             self.control.GetInsertionPoint())

    	def OnPageSetup(self, evt):
		data = wx.PageSetupDialogData()
		data.SetPrintData(self.pdata)

		data.SetDefaultMinMargins(True)
		data.SetMarginTopLeft(self.margins[0])
		data.SetMarginBottomRight(self.margins[1])

		dlg = wx.PageSetupDialog(self, data)
		if dlg.ShowModal() == wx.ID_OK:
		    data = dlg.GetPageSetupData()
		    self.pdata = wx.PrintData(data.GetPrintData()) # force a copy
		    self.pdata.SetPaperId(data.GetPaperId())
		    self.margins = (data.GetMarginTopLeft(),
		                    data.GetMarginBottomRight())
		dlg.Destroy()


    	def OnPrintSetup(self, evt):
		data = wx.PrintDialogData(self.pdata)
		dlg = wx.PrintDialog(self, data)
		dlg.GetPrintDialogData().SetSetupDialog(True)
		dlg.ShowModal();
		data = dlg.GetPrintDialogData()
		self.pdata = wx.PrintData(data.GetPrintData()) # force a copy
		dlg.Destroy()


    	def OnPrintPreview(self, evt):
		data = wx.PrintDialogData(self.pdata)
		text = self.control.GetValue() 
		printout1 = TextDocPrintout(text, "title", self.margins)
		printout2 = None #TextDocPrintout(text, "title", self.margins)
		preview = wx.PrintPreview(printout1, printout2, data)
		if not preview.Ok():
		    wx.MessageBox("Unable to create PrintPreview!", "Error")
		else:
		    # create the preview frame such that it overlays the app frame
		    frame = wx.PreviewFrame(preview, self, "Print Preview",
		                            pos=self.GetPosition(),
		                            size=self.GetSize())
		    frame.Initialize()
		    frame.Show()


    	def OnPrint(self, evt):
		data = wx.PrintDialogData(self.pdata)
		printer = wx.Printer(data)
		text = self.control.GetValue() 
		printout = TextDocPrintout(text, "title", self.margins)
		useSetupDialog = True
		if not printer.Print(self, printout, useSetupDialog) \
		   and printer.GetLastError() == wx.PRINTER_ERROR:
		    wx.MessageBox(
		        "There was a problem printing.\n"
		        "Perhaps your current printer is not set correctly?",
		        "Printing Error", wx.OK)
		else:
		    data = printer.GetPrintDialogData()
		    self.pdata = wx.PrintData(data.GetPrintData()) # force a copy
		printout.Destroy()



	def menuAdd(self, menu, name, desc, fcn, id=-1, kind=wx.ITEM_NORMAL):
            if id == -1:
                id = wx.NewId()
            a = wx.MenuItem(menu, id, name, desc, kind)
            menu.AppendItem(a)
            wx.EVT_MENU(self, id, fcn)
            menu.SetHelpString(id, desc)

	def OnChangeLanguage(self, evt):
            id = evt.GetId()
            normalized = locale.normalize(self.lang_id[id])
            try:
                locale.setlocale(locale.LC_ALL, normalized)
                print("Changing locale %s, dictionary set to %s" % (normalized, self.lang_id[id]))
            except locale.Error:
                print("Can't set python locale to %s; dictionary set to %s" % (normalized, self.lang_id[id]))
            self.control.spell.setLanguage(self.lang_id[id])
            self.control.spell.clearAll()
            self.control.spell.checkCurrentPage()


	def OnModified(self, evt):
            mod = evt.GetModificationType()
            if mod & wx.stc.STC_MOD_INSERTTEXT or mod & wx.stc.STC_MOD_DELETETEXT:
                pos = evt.GetPosition()
                last = pos + evt.GetLength()
                self.control.spell.addDirtyRange(pos, last, evt.GetLinesAdded(), mod & wx.stc.STC_MOD_DELETETEXT)
               
            evt.Skip()

	def OnIdle(self, evt):
            self.idle_count += 1
            if self.idle_count > 10:
                self.control.spell.processIdleBlock()
                self.idle_count = 0		

				
app = wx.App()
frame = MainWindow(None, size=(800,600))
app.MainLoop()
