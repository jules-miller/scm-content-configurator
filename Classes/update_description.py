import os
import sys
import tkinter.messagebox
from lxml import etree
import logging
import traceback
import tkinter

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'Classes'))

from parse_bes import ParseBes
from parse_xlsx import ParseXlsx
from utils import Utils

class UpdateDescription:
	"""
	Contains the method that completes the entire description update process for a given bes file.
	"""
	def __init__(self, logger: logging.Logger):
		self._logger = logger
		self._outputFile = ''
		self._errCt = 0
	
	### Getters ###
	@property
	def outputFile(self):
		return self._outputFile
	
	@property
	def errCt(self):
		return self._errCt

	### SCM Description Updater ###
	def Update(self, logFile: str, xlsxFile: str, besFile: str) -> int:
		"""
		Handles the full SCM description update process.
		Return values:
			0: success
			1: xlsx file not specified
			2: bes file not specified
			3: bes file not found
			4: bes file has incorrect type (not a .bes file)
			5: failed to parse bes file
			6: failed to parse scm metadata in bes file
			7: xlsx file not found
			8: xlsx file has incorrect type (not a .xlsx file)
			9: failed to instantiate xlsx parser
			10: failed to create dataframe from xlsx file
		"""
		# Validate args
		if not len(xlsxFile) > 0:
			return 1
		if not len(besFile) > 0:
			return 2

		# Set output file
		self._outputFile = Utils.NewBesFN(besFile)

		### Setup ParseBes ###
		try:
			besInstance = ParseBes(self._logger, besFile)
		except FileNotFoundError as e:
			self._logger.error(f"Aborting process. - {e}")
			return 3
		except TypeError as e:
			self._logger.error(f"Aborting process. - {e}")
			return 4
		except etree.ParseError as e:
			self._logger.error(f"Failed to parse bes file: {besFile} - {e}")
			return 5

		try:
			self._logger.info(f"Parsing BES File: {besFile}")
			scmData = besInstance.ParseScmData()
		except Exception as e:
			self._logger.error(f"Failed to parse scm metadata | {e}")
			self._logger.error(traceback.format_exc())
			return 6

		### Setup ParseXlsx ###
		try:
			parseXlsx = ParseXlsx(self._logger, xlsxFile) # Instantiate ParseXlsx
		except FileNotFoundError as e:
			self._logger.error(f"Aborting process. - {e}")
			return 7
		except TypeError as e:
			self._logger.error(f"Aborting process. - {e}")
			return 8
		except Exception as e:
			self._logger.error(f"Failed to instantiate xlsx parser | {e}")
			self._logger.error(traceback.format_exc())
			return 9

		try:
			self._logger.info(f"Parsing xlsx file: {xlsxFile}")
			controlsDF = parseXlsx.GetControlsDF() # Create the security controls matrix dataframe
			if parseXlsx.controlsDF.empty:
				self._logger.error("Security Controls dataframe failed to create! Unable to continue. Exiting now.")
				return 10
		except Exception:
			self._logger.error(f"Failed to create dataframe from xlsx file | {e}")
			self._logger.error(traceback.format_exc())
			return 10

		# Iterate through each fixlet found in scmData
		self._logger.info("### Starting Content Iteration Process ###")
		for key, value in scmData.items():
			title = key
			ruleID = value['RuleID']
			
			# grab the description from the xlsx for the given rule found in the bes file
			try:
				descr = parseXlsx.GetDesc(ruleID) 
			except Exception as e:
				self._logger.error(f"Failed to obtain description from xlsx for rule: {ruleID}. Skipping to next fixlet. | {e}")
				self._logger.error(traceback.format_exc())
				self._errCt += 1
				continue

			if type(descr) == str:
				self._logger.warning("Skipping to next fixlet due to no description output from xlsx file.")
				self._errCt += 1
				continue

			# convert the description to html format
			formattedDescr = Utils.DescToHtml(title, ruleID, descr['chkContent'], descr['fixText'])
			# update the scm metadata content with the new description
			value['scmMeta']['description'] = formattedDescr
			# convert scm metadata content from a dictionary back to a string  + remove escape characters for single quotes and double backslashes
			metaUpdate = str(value['scmMeta']).replace(r"\'", r"'").replace("\\\\\\\\", "\\\\").replace("\\\\", "\\")
			# update the x-fixlet-scm-metadata MIMEField with the updated scm metadata content
			besInstance.UpdateScmMetadata(title, metaUpdate)

		# write the updated xml tree to a new bes file
		besInstance.WriteBes(self._outputFile)
		if self._errCt > 0 or besInstance.errCt > 0:
			return 11
		else:
			return 0