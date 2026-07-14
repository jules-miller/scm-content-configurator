############### ParseXlsx ###################################
# Methods for reading and parsing Excel xlsx spreadsheets \ ##
# containg STIG controls                                   ##
# Used to parse Security Matrix Controls sheets            ##
#############################################################

import pandas
import os
import logging
import traceback
from typing import Union
from pathlib import Path

import pandas.core
import pandas.core.frame
import pandas.core.series

class ParseXlsx:
	"""
	Contains methods for reading and parsing Excel xlsx spreadsheets.
	FileNotFoundError will be raised if the xlsx file passed to the constructor is missing.
	"""
	# Class Var
	#ruleColSet = ['Rule ID', 'Source Check Content', 'VA Check Content', 'Source Fix Text', 'VA Fix Text']
	ruleColSet = {'Rule ID': str, 'Source Check Content': str, 'VA Check Content': str, 'Source Fix Text': str, 'VA Fix Text': str}
	#vulnColSet = ['Vuln ID', 'STIG Check Content', 'VA Check Content', 'STIG Fix Text', 'VA Fix Text']
	vulnColSet = {'Vuln ID': str, 'STIG Check Content': str, 'VA Check Content': str, 'STIG Fix Text': str, 'VA Fix Text': str}
	controlsSheet = 'Security Controls Matrix'

	# Constructor
	def __init__(self, logger: logging.Logger, file: str, includeTitle: bool = False) -> None:
		self._logger = logger
		self._file = self._CheckFile(file)
		self._controlsDF = pandas.core.frame.DataFrame([])
		self._controlsIDHeader = 'Rule ID'
		self._defChkContHeader = 'Source Check Content'
		self._defFixTxtHeader = 'Source Fix Text'
		self._includeTitle = includeTitle
		self._titleHeader = ''

	### Getters ###
	@property
	def file(self):
		return self._file
	
	@property
	def controlsDF(self):
		return self._controlsDF
	
	@property
	def controlsIDHeader(self):
		return self._controlsIDHeader
	
	@property
	def defChkContHeader(self):
		return self._defChkContHeader
	
	@property
	def defFixTxtHeader(self):
		return self._defFixTxtHeader
	
	### Setters ###
	@controlsDF.setter
	def controlsDF(self, value: pandas.core.frame.DataFrame):
		if type(value) != pandas.core.frame.DataFrame:
			raise TypeError
		self._controlsDF = value

	@controlsIDHeader.setter
	def controlsIDHeader(self, value: str):
		if type(value) != str:
			raise TypeError
		self._controlsIDHeader = value

	@defChkContHeader.setter
	def defChkContHeader(self, value: str):
		if type(value) != str:
			raise TypeError
		self._defChkContHeader = value

	@defFixTxtHeader.setter
	def defFixTxtHeader(self, value: str):
		if type(value) != str:
			raise TypeError
		self._defFixTxtHeader = value

	
	### Methods ###
	def _CheckFile(self, file: str) -> str:
		"""
		Checks that the xlsx file exists.
		Raises FileNotFoundError if file is missing.
		Returns the file if the file exists.
		"""
		if not os.path.isfile(file):
			self._logger.error(f"File not found: {file}")
			raise FileNotFoundError
		
		filePath = Path(file)
		if filePath.suffix != '.xlsx':
			self._logger.error(f"Invalid file format (.xlsx is required): {file}")
			raise TypeError
		
		return file
		
	def _ValidateType(self, value, dataType, object: str) -> None:
		"""
		Args:
		value - value to validate
		dataType - the expected data type
		object - friendly name of what the value represents (for logging)

		Validates the data type of the specified value.
		Raises TypeError if data type is invalid.
		"""
		if type(value) != dataType:
			self._logger.error(f"Data type incorrect for {object}: {value} is not {dataType}")
			raise TypeError
	
	def _ValidateSheetName(self, sheetName: str) -> None:
		"""
		Raises a ValueError if the sheet name does not exist
		"""
		excelObj = pandas.ExcelFile(self._file)
		if sheetName not in excelObj.sheet_names:
			self._logger.error(f"Sheet '{sheetName}' is missing from file: {self._file}")
			raise ValueError
		
	def _ValidateColumns(self, sheetName: str, columns: list) -> None:
		"""
		Raises a ValueError if a column does not exist
		"""
		headers = pandas.read_excel(self._file, sheet_name=sheetName, nrows=0)
		for column in columns:
			if column not in headers.columns:
				self._logger.warning(f"Column '{column}' missing from file: {self._file}")
				raise ValueError
		
	def _CreateDataframe(self, sheetName: str, columns: list = None, colDtypes: dict = None) -> pandas.core.frame.DataFrame:
		"""
		Args:
		sheetName: str -  the name of the Excel sheet (tab) to parse
		columns: list - a list of columns to include in the dataframe (all columns by default)
		colDtype: dict - contains mapping of columns names to their data types
		Returns a pandas dataframe object.
		"""

		# Validate data types of sheetName and columns
		self._ValidateType(value=sheetName, dataType=str, object='Sheet/tab name')
		self._ValidateType(value=columns, dataType=list, object='Columns')

		# Validate the sheet name and columns exist
		self._ValidateSheetName(sheetName)
		self._ValidateColumns(sheetName=sheetName, columns=columns)

		# Create the dataframe
		try:
			dataFrame = pandas.read_excel(self._file, sheet_name=sheetName, usecols=columns, dtype=colDtypes, engine='calamine')
			self._logger.info(f"Successfully created dataframe | Sheet: {sheetName} | Columns: {columns}")
		except Exception as e:
			self._logger.error(f"Error creating dataframe for sheet: {sheetName} - {e}")
			self._logger.error(traceback.format_exc())
			raise RuntimeError

		return dataFrame
	
	def _ParseCellData(self, dataframe: pandas.core.frame.DataFrame, colMatch: str, valMatch: str, colToGet: str) -> pandas.core.series.Series:
		"""
		Finds the row where the colMatch equals the valMatch.
		Then, reads the cell in colToGet column for that aforementioned row.

		Returns the series object for the given row and column

		Args:
		dataframe - the dataframe created in CreateDataFrame
		colMatch: str - The column to match
		valMatch: str - The value to match in colMatch
		colToGet: str - The column whose cell data to return for the matched row
		"""
		
		# Validate dataframe
		if type(dataframe) != pandas.core.frame.DataFrame:
			self._logger.error("_ParseCellData: Invalid dataframe argument data type. Aborting process.")
			raise TypeError
		if dataframe.empty:
			self._logger.error("Dataframe is empty. Aborting process.")
			raise ValueError
		
		# Validate columns exist
		self._ValidateColumns(self.controlsSheet, [colMatch, colToGet])

		# Create the series object with the column data where the colMatch matched the valMatch
		data = dataframe[dataframe[colMatch] == valMatch][colToGet]

		return data
	
	def _IsCellEmpty(self, seriesObj: pandas.core.series.Series) -> bool:
		"""
		Returns True if the seriesObj contains valid data
		Returns False otherwise
		"""
		if seriesObj.hasnans:
			return True
		if seriesObj.empty:
			return True
		else:
			return False

	def _DoesRuleExist(self, ruleId: str) -> bool:
		"""
		Returns True if the rule exists in the xlsx file.
		Returns False if the rule does not exist in the xlsx file.
		"""
		if self.controlsDF.empty:
			return False
		if (self.controlsDF[self._controlsIDHeader] == ruleId).any():
			return True
		else:
			return False

	def GrabCellValueStr(self, seriesObj: pandas.core.series.Series) -> str:
		"""
		Returns the cell data in string format.
		Returns empty string if the cell data is empty. This is to prevent NaN string values.
		The return data is ready to be converted to html if needed
		"""
		if self._IsCellEmpty(seriesObj) == False:
			value = str(seriesObj.values)[1:-1] # Remove brackets beginning and end
			value = value.replace(r"\'", r"'") # replace escaped single quotes with a literal single quote
		else:
			value = ''
		return value
	
	def _SetTitleCol(self) -> None:
		"""
		Searches through the possible Title column headers and sets self._titleHeader to the relevant field.
		"""
		try:
			self._ValidateColumns(self.controlsSheet, ['VA Rule Title'])
			self._titleHeader = 'VA Rule Title'
		except ValueError:
			try:
				self._logger.info('VA Rule Title column missing.  Checking for existence of default Source Rule Title and Rule Title columns')
				self._ValidateColumns(self.controlsSheet, ['Source Rule Title'])
				self._titleHeader = 'Source Rule Title'
			except ValueError:
				try:
					self._ValidateColumns(self.controlsSheet, ['Rule Title'])
					self._titleHeader = 'Rule Title'
				except ValueError:
					self._logger.warning("No valid title columns found!")


	def GetControlsDF(self) -> Union[str, None]:
		"""
		Creates the Security Controls Matrix dataframe.
		Sets the dataframe in the controlsDF class var.
		
		Returns 'ParseError' if Rule ID or Vuln ID is missing, or if dataframe creation failed.
		"""
		
		# Verify that one of the column sets exist. Spreadsheets will either have Rule ID or Vuln ID
		ruleCols = list(self.ruleColSet.keys()) # convert keys from self.ruleColSet to a list (names of columns)
		vulnCols = list(self.vulnColSet.keys()) # convert keys from self.vulnColSet to a list (names of columns)
		colSetToUse = []
		dTypeToUse = {}
		try:
			self._ValidateColumns(self.controlsSheet, ruleCols)
			colSetToUse = ruleCols
			dTypeToUse = self.ruleColSet
		except ValueError:
			try:
				self._ValidateColumns(self.controlsSheet, vulnCols)
				colSetToUse = vulnCols
				dTypeToUse = self.vulnColSet
				self._controlsIDHeader = 'Vuln ID'
				self._defChkContHeader = 'STIG Check Content'
				self._defFixTxtHeader = 'STIG Fix Text'
			except ValueError:
				self._logger.error("One or more required columns are missing from the xlsx file. Aborting process.")
				return "ParseError"
		if self._includeTitle == True:
			self._SetTitleCol() # Set the relevant Title header to be appended to the colSetToUse
			if len(self._titleHeader) > 0: # self._titleHeader will only be greater than 0 if a valid title columns was set
				colSetToUse.append(self._titleHeader) # update columns
				dTypeToUse[self._titleHeader] = str # update data types
		try:
			dataFrame = self._CreateDataframe(self.controlsSheet, colSetToUse, dTypeToUse)
			self.controlsDF = dataFrame
		except ValueError:
			self._logger.error(f"Encountered error while creating the dataframe. Aborting process.")
			return "ParseError"
		
	def GetTitle(self, ruleID: str) -> str:
		"""
		The public method that will obtain the Title for a given ruleID based of the column set in self._titleheader.
		
		Returns a string containing the check title
		Returns 'dfNotSet' if the Security Controls DF was not created.
		Returns ParseError if exception is encounted when parsing cell data.
		Returns DataMissing if the Title column is empty - _ParseCellData returned an empty cell
		Returns ruleNotFound if the ruleID is missing from xlsx file
		"""
		if self.controlsDF.empty:
			self._logger.error("Security Controls dataframe not created. Run GetControlsDF first.")
			return 'dfNotSet'
		
		if self._DoesRuleExist(ruleID) == False:
			self._logger.warning(f"RuleID not found in xlsx file: {ruleID}")
			return 'ruleNotFound'
		
		try:
			titleData = self._ParseCellData(self.controlsDF, self._controlsIDHeader, ruleID, self._titleHeader)
		except Exception:
			self._logger.error(f"Failed to parse '{self._titleHeader}' for {ruleID}")
			return 'ParseError'

		# check if the title column contains any data
		if self._IsCellEmpty(titleData) == False:
			self._logger.info(f"{self._titleHeader} found for {ruleID}")
		else:
			self._logger.info(f"{self._titleHeader} empty for {ruleID}.")
			return "DataMissing"
		
		# Convert to str
		titleData = self.GrabCellValueStr(titleData)
		titleData = titleData[1:-1] # Remove single quotes beginning and end

		# Check for empty results
		if len(titleData) == 0:
			self._logger.info(f"'{self._titleHeader}' empty for {ruleID}.")
			return "DataMissing"

		return titleData
		
	def GetDesc(self, ruleID: str) -> Union[dict, str]:
		"""
		The public method that will obtain and concatenate the relevant Check Content and Fix Text.
		
		Returns a dictionary the Check Content and Fix Text columns if present. Ex. {'chkContent': 'check text string', 'fixText': 'fix text string'}
		Returns 'dfNotSet' if the Security Controls DF was not created.
		Returns ParseError if exception is encounted when parsing cell data.
		Returns DataMissing if checkData or fixData is empty - _ParseCellData returned an empty cell
		Returns ruleNotFound if ruleid is missing from xlsx file
		"""
		if self.controlsDF.empty:
			self._logger.error("Security Controls dataframe not created. Run GetControlsDF first.")
			return 'dfNotSet'
		
		if self._DoesRuleExist(ruleID) == False:
			self._logger.warning(f"RuleID not found in xlsx file: {ruleID}")
			return 'ruleNotFound'
		
		try:
			checkData = self._ParseCellData(self.controlsDF, self._controlsIDHeader, ruleID, 'VA Check Content')
		except Exception:
			self._logger.error(f"Failed to parse 'VA Check Content' for {ruleID}")
			return 'ParseError'

		# if Check Content contains data, grab the Fix Text column as well
		if self._IsCellEmpty(checkData) == False:
			self._logger.info(f"VA Check Content found for {ruleID}")
			try:
				fixData = self._ParseCellData(self.controlsDF, self._controlsIDHeader, ruleID, 'VA Fix Text')
				if self._IsCellEmpty(fixData) == True: # Use the Source Fix Text if the Fix Text is empty but Check Content exists
					fixData = self._ParseCellData(self.controlsDF, self._controlsIDHeader, ruleID, self._defFixTxtHeader)
					self._logger.info(f"VA Fix Text is missing for {ruleID}. Using {self.defFixTxtHeader} instead.")
			except Exception:
				self._logger.error(f"Failed to parse 'VA Fix Text' for {ruleID}")
				return 'ParseError'
		else:
			self._logger.info(f"VA Check Content empty for {ruleID}. Using {self._defChkContHeader} instead.")
			try:
				checkData = self._ParseCellData(self.controlsDF, self._controlsIDHeader, ruleID, self._defChkContHeader)
				fixData = self._ParseCellData(self.controlsDF, self._controlsIDHeader, ruleID, self._defFixTxtHeader)
			except Exception:
				self._logger.error(f"Failed to parse {self._defChkContHeader} and {self.defFixTxtHeader} for {ruleID}")
				return 'ParseError'
		
		# Convert to str
		checkData = self.GrabCellValueStr(checkData)
		fixData = self.GrabCellValueStr(fixData)

		# Check for empty results
		if len(checkData) == 0 or len(fixData) == 0:
			return "DataMissing"

		# Create dictionary and return - [1:-1] is intended to remove leading and trailing single quotes
		results = {'chkContent': checkData[1:-1], 'fixText': fixData[1:-1]}
		return results


if __name__ == "__main__":
	import sys
	import os
	from pathlib import Path
	os.makedirs(Path(__file__).parent / f"../Logs", exist_ok=True)

	from log_config import LogConfig
	logSetup = LogConfig('parse_xlsx_test', 20000000, 5)
	testLogger = logSetup.ConfigureLogger()

	testLogger.info(50 * '#')
	testLogger.info("######### Starting ParseXlsx Test #########")

	from parse_xlsx import ParseXlsx
	xlsxFile = "BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2.xlsx"
	try:
		parseXlsx = ParseXlsx(testLogger, xlsxFile) # Instantiate ParseXlsx
	except Exception as e:
		sys.exit(1)

	try:
		controlsDF = parseXlsx.GetControlsDF() # Create the security controls matrix dataframe
	except Exception:
		sys.exit(1)

	if controlsDF == 'ParseError':
		sys.exit(1)

	rules = ['V-258240', 'V-258241', 'V-258046'] # 258240 contains check content, 258241 does NOT contain va check content

	# Loop through each rule id and grab the content if applicable
	for rule in rules:
		try:
			desc = parseXlsx.GetDesc(rule)
		except Exception:
			desc = 'Encountered exception'
		finally:
			print(f"Description for {rule}:\n", desc)
