import os
import sys
from lxml import etree
import logging
import traceback
import tkinter
import json

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'Classes'))

from parse_bes import ParseBes
from parse_xlsx import ParseXlsx
from utils import Utils

class Execute():
	"""
	Contains methods to execute various actions on a .bes file.
	"""
	def __init__(self, logger: logging.Logger, besFile: str):
		self._logger = logger
		self._xlsxFile = ''
		self._besFile = besFile
		self._outputFile = ''
		self._parseXlsx = None
		self._besInstance = None
		self._errCt = 0

	### Getters ###
	@property
	def outputFile(self):
		return self._outputFile
	
	@property
	def parseXlsx(self):
		return self._parseXlsx
	
	@property
	def besInstance(self):
		return self._besInstance

	### Methods ###
	def InitialzeBes(self) -> int:
		"""
		Instantiates ParseBes
		Return values:
			0: success
			3: bes file not found
			4: bes file has incorrect type (not a .bes file)
			5: failed to parse bes file
		"""
		try:
			self._besInstance = ParseBes(self._logger, self._besFile)
		except FileNotFoundError as e:
			self._logger.error(f"Aborting process. - {e}")
			return 3
		except TypeError as e:
			self._logger.error(f"Aborting process. - {e}")
			return 4
		except etree.ParseError as e:
			self._logger.error(f"Failed to parse bes file: {self._besFile} - {e}")
			return 5
		
		# Set output file
		self._outputFile = Utils.NewBesFN(self._besFile)
		return 0

	def InitializeXlsx(self, xlsxFile: str, includeTitle: bool = False) -> int:
		"""
		Instantiates ParseXlsx and reads the file into a dataframe.
		Return values:
			0: success
			7: xlsx file not found
			8: xlsx file has incorrect type (not a .xlsx file)
			9: failed to instantiate xlsx parser
			10: failed to create dataframe from xlsx file
		"""
		self._xlsxFile = xlsxFile
		try:
			if includeTitle == True:
				self._parseXlsx = ParseXlsx(self._logger, self._xlsxFile, includeTitle=True) # Instantiate ParseXlsx
			else:
				self._parseXlsx = ParseXlsx(self._logger, self._xlsxFile) # Instantiate ParseXlsx
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
			self._logger.info(f"Parsing xlsx file: {self._xlsxFile}")
			controlsDF = self._parseXlsx.GetControlsDF() # Create the security controls matrix dataframe
			if self._parseXlsx.controlsDF.empty:
				self._logger.error("Security Controls dataframe failed to create! Unable to continue. Exiting now.")
				return 10
		except Exception as e:
			self._logger.error(f"Failed to create dataframe from xlsx file | {e}")
			self._logger.error(traceback.format_exc())
			return 10
		
		return 0
	
	def UpdateScmMeta(self) -> str:
		"""
		Handles the SCM Metadata update process that includes the description.
		Return values:
			'Process Complete'
			'Failed to parse scm metadata in BES file.'
			'Process Complete with Errors'
		"""
		try:
			self._logger.info(f"Parsing BES File: {self._besFile}")
			scmData = self._besInstance.ParseScmData()
		except Exception as e:
			self._logger.error(f"Failed to parse scm metadata | {e}")
			self._logger.error(traceback.format_exc())
			return 'Failed to parse scm metadata in BES file.'
		
		# Iterate through each fixlet found in scmData
		#self._logger.info("### Starting Content Iteration Process ###")
		for key, value in scmData.items():
			title = key
			ruleID = value['RuleID']
			
			# grab the description from the xlsx for the given rule found in the bes file
			try:
				descr = self._parseXlsx.GetDesc(ruleID) 
			except Exception as e:
				self._logger.error(f"Failed to obtain description from xlsx for rule: {ruleID}. Skipping to next fixlet. | {e}")
				self._logger.error(traceback.format_exc())
				self._errCt += 1
				continue
			
			if type(descr) == str:
				self._logger.warning("Skipping to next fixlet due to no description output from xlsx file.")
				self._errCt += 1
				continue

			# grab the title from the xlsx for the given rule
			if self._parseXlsx._includeTitle == True:
				try:
					xlsxTitle = self._parseXlsx.GetTitle(ruleID)
				except Exception as e:
					self._logger.error(f"Failed to obtain title from xlsx for rule: {ruleID}. | {e}")
					self._logger.error(traceback.format_exc())
					self._errCt += 1
					xlsxTitle = 'DataMissing'
				
				if xlsxTitle not in ['DataMissing', 'dfNotSet', 'ParseError', 'ruleNotFound']:
					value['scmMeta']['title'] = xlsxTitle # update scmMetadata title value
					xpathTitle = etree.XPath('//Fixlet[Title = $var]/Title')
					titleVal = xpathTitle(self._besInstance.root, var=title)
					titleVal[0].text = xlsxTitle # Update the fixlet <Title> value
					self._logger.info(f"Successfully updated the title values for {ruleID}")
					title = xlsxTitle # update title object so the new title is set in the scmMetadata description

			# convert the description to html format
			formattedDescr = Utils.DescToHtml(title, ruleID, descr['chkContent'], descr['fixText'])
			# update the scm metadata content with the new description
			value['scmMeta']['description'] = formattedDescr.replace(r"\'", r"'").replace("\\\\\\\\", "\\\\").replace("\\\\", "\\")
			
			# convert scm metadata content from a dictionary back to a string  + remove escape characters for single quotes and double backslashes
			metaUpdate = json.dumps(value['scmMeta']) # convert to json compliant string

			# update the x-fixlet-scm-metadata MIMEField with the updated scm metadata content
			xpathVal = etree.XPath('//Fixlet[Title = $var]/MIMEField[Name = "x-fixlet-scm-metadata"]/Value') # 5 seconds faster than calling UpdateScmMetadata on el9
			scmValue = xpathVal(self._besInstance.root, var=title) # 5 seconds faster than calling UpdateScmMetadata on el9
			scmValue[0].text = etree.CDATA(metaUpdate)
			self._logger.info(f"Successfully updated the value of {self._besInstance._scmMetaMime} for {ruleID}")
			#self._besInstance.UpdateScmMetadata(title, metaUpdate) # will work in all cases, slightly slower

		if self._errCt > 0 or self._besInstance.errCt > 0:
			return 'Process Complete with Errors'
		else:
			return 'Process Complete'