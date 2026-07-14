import os
import sys
import tkinter.messagebox
import PIL.Image
from lxml import etree
import traceback
import tkinter
import customtkinter
import time
import PIL
from pathlib import Path

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'Classes'))

from log_config import LogConfig
from parse_bes import ParseBes
from parse_xlsx import ParseXlsx
from execute import Execute
from utils import Utils
from file_button import FileButton

# Create Logs folder
try:
	os.mkdir(Path(__file__).parent / "Logs")
except FileExistsError:
	pass

logFile = 'Logs/main.log'
logSetup = LogConfig('main', 20000000, 5)
mainLogger = logSetup.ConfigureLogger()
mainLogger.info(50 * "#")
mainLogger.info("### STARTING SCM FIXLET UPDATE UTILITY ###")

### Initialize GUI ###
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")
app = customtkinter.CTk() # creates main window instance
app.title("SCM Fixlet Updater")
app.geometry("900x350") # main window dimensions

# set logo image
try:
	app.iconbitmap('logo_sm.ico')
except Exception:
	mainLogger.warning("Unable to set icon")
	mainLogger.error(traceback.format_exc())

headerLbl = customtkinter.CTkLabel(app, text="SCM Fixlet Updater")
headerLbl.configure(font=('Tahoma', 25), text_color="white smoke")
headerLbl.place(relx=0.5, y=30, anchor="center")

# Set va logo in app window
imagePath = 'va-logo.png'
pilImage = PIL.Image.open(imagePath)
ctkImage = customtkinter.CTkImage(pilImage, size=(160, 36))
vaLbl = customtkinter.CTkLabel(app, image=ctkImage, text="")
vaLbl.place(x=20, y=10)

# Create Checkboxes
updateDescrBoxStat = customtkinter.BooleanVar() # stores the checked vs unchecked state
rmSiteRelBoxStat = customtkinter.BooleanVar() # stores the checked vs unchecked state
rmActionBoxStat = customtkinter.BooleanVar() # stores the checked vs unchecked state
replPareBoxStat = customtkinter.BooleanVar() # stores the checked vs unchecked state
updateTitleBoxStat = customtkinter.BooleanVar() # stores the checked vs unchecked state

updateDescrBox = customtkinter.CTkCheckBox(app, text="Update Description", font=('Tahoma', 14), text_color="white smoke", variable=updateDescrBoxStat).place(x=60, y=195)
rmSiteRelBox = customtkinter.CTkCheckBox(app, text="Remove Site Relevance", font=('Tahoma', 14), text_color="white smoke", variable=rmSiteRelBoxStat).place(x=260, y=195)
rmActionBox = customtkinter.CTkCheckBox(app, text="Remove Action Script", font=('Tahoma', 14), text_color="white smoke", variable=rmActionBoxStat).place(x=460, y=195)
replPareBox = customtkinter.CTkCheckBox(app, text="Replace Parenthesized Part", font=('Tahoma', 14), text_color="white smoke", variable=replPareBoxStat).place(x=660, y=195)
updateTitleBox = customtkinter.CTkCheckBox(app, text="Update Title", font=('Tahoma', 14), text_color="white smoke", variable=updateTitleBoxStat).place(x=60, y=235)

#####################################################################
def OpenReadme() -> None:
	if getattr(sys, 'frozen', False):           # Running as EXE built with pyinstaller
		exePath = os.path.dirname(sys.executable)
	elif __file__:                              # Running as script
		exePath = Path(__file__).parent  # since this is running from the classes dir
	readmeFile = os.path.join(exePath, 'README.txt')

	if os.path.isfile(readmeFile):
		os.startfile(readmeFile)
	else:
		tkinter.messagebox.showerror("ERROR", f"README File Not Found!")

def VerifyInitBes(initBes: int) -> int:
	"""
	Verifies return code of initBes
	Args:
		initBes: the initialize bes object (instantiates ParseBes) should be an int return code
	"""
	match initBes:
		case 3:
			tkinter.messagebox.showerror("ERROR", f"File Not Found: {besFrame.filePath}\n\nLog File: {logFile}")
			return 3
		case 4:
			tkinter.messagebox.showerror("ERROR", f"Wrong File Type: {besFrame.filePath}\nBES file required.\n\nLog File: {logFile}")
			return 4
		case 5:
			tkinter.messagebox.showerror("ERROR", f"Failed to parse BES file: {besFrame.filePath}\n\nLog File: {logFile}")
			return 5
		case _:
			return 0

def VerifyInitXlsx(initXlsx: int) -> int:
	"""
	Verifies return code of initXlsx
	Args:
		initXlsx: the initialize xlsx object (instantiates ParseXlsx) should be an int return code
	"""
	match initXlsx:
			case 7:
				tkinter.messagebox.showerror("ERROR", f"File Not Found: {xlsxFrame.filePath}\n\nLog File: {logFile}")
				return 7
			case 8:
				tkinter.messagebox.showerror("ERROR", f"Wrong File Type: {xlsxFrame.filePath}\nxlsx file required.\n\nLog File: {logFile}")
				return 8
			case 9:
				tkinter.messagebox.showerror("ERROR", f"Failed to setup xlsx file parsing.\n\nLog File: {logFile}")
				return 9
			case 10:
				tkinter.messagebox.showerror("ERROR", f"Failed to create dataframe from xlsx file\n\nLog File: {logFile}")
				return 10
			case _:
				return 0

##########################################################
# Create the execute function
def ExecuteActions():
	startTime = time.perf_counter()
	# Verify at least one checkbox has been checked
	if any((updateDescrBoxStat.get(), rmActionBoxStat.get(), rmSiteRelBoxStat.get(), replPareBoxStat.get(), updateTitleBoxStat.get())):
		if updateTitleBoxStat.get() == True and updateDescrBoxStat.get() == False: # update title can't happen without also updating the description
			tkinter.messagebox.showerror("ERROR", "You must check 'Update Description' if checking 'Update Title'.")
			return
		if not len(besFrame.filePath) > 0: # verify a BES File was selected
			tkinter.messagebox.showerror("ERROR", "You must specify a bes file.")
			return
		
		mainLogger.info("## Starting update processes ##")
		mainLogger.info(f"Update Description: {updateDescrBoxStat.get()}")
		mainLogger.info(f"Update Title: {updateTitleBoxStat.get()}")
		mainLogger.info(f"Remove Actions: {rmActionBoxStat.get()}")
		mainLogger.info(f"Remove Site Relevance: {rmSiteRelBoxStat.get()}")
		mainLogger.info(f"Replace Parenthesized Part Relevance: {replPareBoxStat.get()}")
		execute = Execute(mainLogger, besFrame.filePath)
		initBes = execute.InitialzeBes()# initialize reading the bes file - all possible gui actions require the bes file
		initBesResult = VerifyInitBes(initBes)
		if initBesResult != 0:
			return
	else:
		tkinter.messagebox.showerror("ERROR", "You must select at least one checkbox.")
		return
	
	exeButton.configure(text="Please Wait...")
	app.update_idletasks()  # Force GUI update

	# Create objects for each action
	updateDescr = None
	rmSiteRele = None
	rmAction = None
	replPare = None
	updateTitle = None
	
	if updateDescrBoxStat.get() == True:
		if not len(xlsxFrame.filePath) > 0: # verify a BES File was selected
			tkinter.messagebox.showerror("ERROR", "You must specify a xlsx file.")
			exeButton.configure(text="Execute")
			app.update_idletasks()  # Force GUI update
			return
		if updateTitleBoxStat.get() == True:
			initXlsx = execute.InitializeXlsx(xlsxFrame.filePath, includeTitle=True) # initialize reading the xlsx file
			initXlsxResult = VerifyInitXlsx(initXlsx)
			if initXlsxResult != 0:
				exeButton.configure(text="Execute")
				app.update_idletasks()  # Force GUI update
				return
			mainLogger.info(f"Running process to update scm descriptions and titles in '{besFrame.filePath}' based off data in '{xlsxFrame.filePath}'")
		else:
			initXlsx = execute.InitializeXlsx(xlsxFrame.filePath) # initialize reading the xlsx file
			initXlsxResult = VerifyInitXlsx(initXlsx)
			if initXlsxResult != 0:
				exeButton.configure(text="Execute")
				app.update_idletasks()  # Force GUI update
				return
			mainLogger.info(f"Running process to update scm descriptions in '{besFrame.filePath}' based off data in '{xlsxFrame.filePath}'")
		updateDescr = execute.UpdateScmMeta()
		if updateTitleBoxStat.get() == True:
			updateTitle = updateDescr

	if rmSiteRelBoxStat.get() == True:
		mainLogger.info(f"Running process to remove site level relevance in '{besFrame.filePath}'")
		execute.besInstance.RemoveSiteRelevance()
		rmSiteRele = 'Process Complete'

	if rmActionBoxStat.get() == True:
		mainLogger.info(f"Running process to remove actions in '{besFrame.filePath}'")
		execute.besInstance.RemoveActionScript()
		rmAction = 'Process Complete'

	if replPareBoxStat.get() == True:
		mainLogger.info(f"Running process to replace 'parenthesized part(s) of' in '{besFrame.filePath}'")
		execute.besInstance.ReplaceRelevance('parenthesized parts of', 'parenthesized parts 1 of')
		execute.besInstance.ReplaceRelevance('parenthesized part of', 'parenthesized parts 1 of')
		replPare = 'Process Complete'
	
	execute.besInstance.WriteBes(execute.outputFile) # write the updated xml tree to a new bes file
	endTime = time.perf_counter()
	elapsedTime = endTime - startTime
	tkinter.messagebox.showinfo("RESULTS", f"UPDATE DESCRIPTION: {updateDescr}\nUPDATE TITLE: {updateTitle}\nRM SITE RELEVANCE: {rmSiteRele}\nRM ACTION: {rmAction}\nREPLACE PAREN PART: {replPare}\n\nOUTPUT FILE: {execute.outputFile}\n\nLOG FILE: {logFile}\n\nELAPSED TIME: {elapsedTime}")
	mainLogger.info(f"## All processes complete. Elapsed time: {elapsedTime} ##")
	exeButton.configure(text="Execute") # reset button text

##########################################################
exeButton = customtkinter.CTkButton(master=app, text="Execute", command=lambda: ExecuteActions())
exeButton.place(relx=0.5, y=290, anchor="center")

readmeButton = customtkinter.CTkButton(master=app, text="Open README", command=lambda: OpenReadme())
readmeButton.place(x=750, y=10)

footerLbl = customtkinter.CTkLabel(app, text="NOTE: Ensure you have removed hidden data from the XLSX file before executing. This will drastically reduce execution times.\n Open XLSX in Excel > File > Info > Check for Issues > Inspect Document > Remove 'Custom XML Data' and 'Hidden Rows and Columns'")
footerLbl.configure(font=('Tahoma', 12), text_color="DarkOrange2")
footerLbl.place(relx=0.5, y=330, anchor="center")

# Create the select file buttons and entry fields - store in a frame
try:
	xlsxFrame = FileButton(app, "Select XLSX File", "xlsx", (40, 100), 700) # xlsx file selector button/entry
	besFrame = FileButton(app, "Select BES File", "bes", (40, 135), 700) # bes file selector button/entry
	app.mainloop() # Start the application event loop
except Exception as e:
	mainLogger.error(f"Failed to initialize GUI - {e}")
	mainLogger.error(traceback.format_exc())

