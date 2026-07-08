############### ParseBes ############################
# Methods for parsing and writing to BES XML files ##
#####################################################

from lxml import etree
import json
import os
import logging
import traceback
from typing import Union
from pathlib import Path

class ParseBes:
	"""
	Contains methods for parsing and writing to BES XML files.
	FileNotFoundError will be raised if the file passed to the constructor is missing.
	Reads the file and builds the element tree on instantiation.
	"""
	
	# Class Var
	

	# Constructor
	def __init__(self, logger: logging.Logger, file: str) -> None:
		self._logger = logger
		self._file = self._CheckFile(file)
		self._scmMetaMime = 'x-fixlet-scm-metadata'
		self._scmCtrlMime = 'x-fixlet-scm-control'
		self._root = None
		self._tree = None
		self._GetRoot()
		self._errCt = 0
		
	### Getters ###
	@property
	def errCt(self):
		return self._errCt
	
	@property
	def file(self):
		return self._file
	
	@property
	def scmMetaMime(self):
		return self._scmMetaMime
	
	@property
	def scmCtrlMime(self):
		return self._scmCtrlMime
	
	@property
	def root(self):
		return self._root
	
	@property
	def tree(self):
		return self._tree
	
	### Methods ###
	def _CheckFile(self, file: str) -> str:
		"""
		Checks that the bes file exists.
		Raises FileNotFoundError if file is missing.
		Raises TypeErrir if not valid file format (.bes)
		Returns the file.
		"""
		if not os.path.isfile(file):
			self._logger.error(f"File not found: {file}")
			raise FileNotFoundError
		
		filePath = Path(file)
		if filePath.suffix != '.bes':
			self._logger.error(f"Invalid file format (.bes is required): {file}")
			raise TypeError
		
		return file
	
	def _GetRoot(self) -> etree._Element:
		"""
		Reads the .bes file into an element tree and returns the root.
		"""
		parser = etree.XMLParser(strip_cdata=False) # create parser to preserve CDATA
		tree = etree.parse(self._file, parser=parser)
		root = tree.getroot()

		self._tree = tree
		self._root = root

		return root
	
	def _GetTitle(self) -> list:
		"""
		Parses the 'Title' tag for the given Fixlet.
		Returns a list containing all titles in the fixlet.
		"""
		titles = []
		items = self._root.findall('.//Title')
		for title in items:
			titles.append(title.text)
		
		return titles

	def _GetRule(self, value: Union[str, dict]) -> str:
		"""
		Parses the Rule ID/Vuln ID (Ex. V-214290)
		Returns the Rule ID as text (str).
		Returns 'notFound' if no id is found.
		"""
		if type(value) == str:
			if value.startswith('V-') or value.startswith('VA-'):
				return(value)
		
		if type(value) == dict:
			if 'disa_vulid' in value:
				id = str(value['disa_vulid'])
				if id.startswith('V-'):
					return id
				if id.startswith('xccdf'):
					index = id.find('V-')
					if index != -1:
						id = id[index:] # remove the xccdf substring, leaving only the rule/vuln id.
						return id
			
		return 'notFound'


	def ReadMime(self, element: etree._Element, name: str ) -> str:
		"""
		Parses the passed element for all child MIMEFields that match the passed name.
		Only find MIMEFields for the passed element - does not loop though entire file
		Returns the Value tag where the passed Name arg matches.
		"""
		items = element.findall('MIMEField')
		for item in items:
			if item.find('Name').text == name:
				value = item.find('Value').text
		
		try:
			value
		except NameError:
			value = ''
		
		return value
	
	def ParseScmData(self) -> dict:
		"""
		Loops through all fixlets in the bes file.
		Parses SCM related data.
		Returns data in a dictionary.

		Example return dictionary:
		{'fixlet title 1': {'Rule ID': 'V-214267', 'scmMeta': {'title': 'fixlet title', 'description': 'compliance description', 'disa_vulid': 'V-214267'}}}
		This is a dictionary containing a dictionary as the value which also contains yet another dictionary as one of the subKeys values.
		"""
		results = {}
		for element in self._tree.findall('.//Fixlet'): # iterates through each Fixlet tag
			for subElement in element: # iterates through each subtag in the Fixlet tag
				if subElement.tag == 'Title': 
					data = {}
					title = subElement.text # assign the title
					sourceId = element.find('SourceID').text # assign the SourceID for Rule ID processing

					try:
						scmCtrlVal = self.ReadMime(element, self._scmCtrlMime) # assign the x-fixlet-scm-control MIMEField for rule id processing
						scmMetadata = self.ReadMime(element, self._scmMetaMime) # assing the x-fixlet-scm-metadata for multiple processing use cases
					except Exception as e:
						self._logger.error(f"Error reading MIMEField for {title}.")
						self._logger.error(f"Continuing to next element.")
						self._logger.error(traceback.format_exc)
						self._errCt += 1
						continue # skip to next iteration

					scmMetadata = self.ConvertJson(scmMetadata) # convert metadata to a dictionary (this should already be a string in json format)
					
					try: # attempt to locate the rule/vuln id
						ruleCheck1 = self._GetRule(scmCtrlVal) 
						ruleCheck2 = self._GetRule(sourceId)
						ruleCheck3 = self._GetRule(scmMetadata)
					except Exception as e:
						self._logger.error(f"Error parsing rule id for {title}")
						self._logger.error(f"Continuing to next element.")
						self._logger.error(traceback.format_exc)
						self._errCt += 1
						continue
					
					# verify rule/vuln id results and add to the data dictionary if applicable
					if ruleCheck1 != 'notFound':
						data['RuleID'] = ruleCheck1
					elif ruleCheck2 != 'notFound':
						data['RuleID'] = ruleCheck2
					elif ruleCheck3 != 'notFound':
						data['RuleID'] = ruleCheck3

					if 'RuleID' not in data:
						self._logger.error(f"Unable to obtain rule id for {title}")
						self._logger.error(f"Continuing to next element.")
						self._errCt += 1
						continue
					
					self._logger.info(f"Found Rule ID '{data['RuleID']}' for '{title}'")
					data['scmMeta'] = scmMetadata
					results[title] = data

		return results

	def ConvertJson(self, value: str) -> Union[dict, str]:
		"""
		Arg must be a string in json format.
		Returns dictionary.
		"""
		try:
			value = json.loads(value)
		except json.decoder.JSONDecodeError as e:
			self._logger.error(f"Unable to convert value to json: {value} | {e}")
			value = ''
		return value

	def UpdateScmMetadata(self, title: str, value: str) -> None:
		"""
		Updates the 'x-fixlet-scm-metadata' MIMEField for the passed fixlet.
		title = name of <Title> tag for a given fixlet
		value = string value that will replace 'x-fixlet-scm-metadata' <value> tag. Should be CDATA format.
		"""
		for element in self._tree.findall('.//Fixlet'): # iterates through each Fixlet tag
			for subElement in element: # iterates through each subtag in the Fixlet tag
				if subElement.tag == 'Title' and subElement.text == title:
					items = element.findall('MIMEField')
					for item in items:
						if item.find('Name').text == self._scmMetaMime:
							valueTag = item.find('Value')
							if valueTag is not None:
								valueTag.text = etree.CDATA(value)
								self._logger.info(f"Successfully updated the value of {self._scmMetaMime} for fixlet '{title}'")
								break

	def RemoveSiteRelevance(self) -> None:
		"""
		Removes site level relevance for all fixlets in the bes file
		Uses 'proxy agent context' string as an identifier in the Relevance tag
		"""
		for element in self._tree.findall('.//Fixlet'): # iterates through each Fixlet tag
			for subElement in element: # iterates through each subtag in the Fixlet tag
				if subElement.tag == 'Title': 
					title = subElement.text # assign the title
					for item in element.findall('Relevance'): # for the given element(fixlet) loop through all Relevance tags
						if 'proxy agent context' in item.text:
							item.getparent().remove(item) # removing this way allows for the site level relevance to exist along with multiple Relevance tags in any order
							self._logger.info(f"Removed site level relevance for fixlet '{title}'")
	
	def RemoveActionScript(self) -> None:
		"""
		Removes DefaultAction and Action tags for all fixlets in the bes file
		"""
		for element in self._tree.findall('.//Fixlet'): # iterates through each Fixlet tag
			for subElement in element: # iterates through each subtag in the Fixlet tag
				if subElement.tag == 'Title': 
					title = subElement.text # assign the title
					defAction = element.find('DefaultAction')
					if defAction is not None:
						element.remove(defAction)
						self._logger.info(f"Removed default action for fixlet '{title}'")
					for item in element.findall('Action'): # for the given element(fixlet) loop through all Action tags
						item.getparent().remove(item)
						self._logger.info(f"Removed action for fixlet '{title}'")
	
	def ReplaceRelevance(self, oldStr: str, newStr: str) -> None:
		for element in self._tree.findall('.//Fixlet'): # iterates through each Fixlet tag
			for subElement in element: # iterates through each subtag in the Fixlet tag
				if subElement.tag == 'Title': 
					title = subElement.text # assign the title
					for item in element.findall('Relevance'): # for the given element(fixlet) loop through all Relevance tags
						relevanceValue = str(item.text)
						if oldStr in relevanceValue:
							relevanceValue = relevanceValue.replace(oldStr, newStr)
							self._logger.info(f"Replaced '{oldStr}' with '{newStr}' in fixlet: {title}")
							item.text = etree.CDATA(relevanceValue)

	def WriteBes(self, outputFile: str) -> None:
		"""
		Writes the current tree to the passed output file.
		If UpdateScmMetadata was executed prior to executing this method, the tree will contain these updates.
		"""
		try:
			self._tree.write(outputFile, encoding="utf-8", xml_declaration=True)
			self._logger.info(f"Output written to '{outputFile}'")
		except Exception as e:
			self._logger.error(f"Failed to write output to '{outputFile}' | {e}")
			self._logger.error(traceback.format_exc())
			self._errCt += 1
	
if __name__ == "__main__":
	import sys
	import os
	from pathlib import Path
	os.makedirs(Path(__file__).parent / f"../Logs", exist_ok=True)

	from log_config import LogConfig
	logSetup = LogConfig('parse_bes_test', 20000000, 5)
	testLogger = logSetup.ConfigureLogger()

	testLogger.info(50 * '#')
	testLogger.info("######### Starting ParseBes Test #########")

	from parse_bes import ParseBes
	el9File = "BESFiles/el9SiteTest.bes"
	win19File = "BESFiles/Ensure that an approved agent for collecting and sending logs is installed and running..bes"
	m2131WinFile = "BESFiles/Logging of default Windows Events must be enabled per M-21-31 Requirements.bes"
	iisFile = "BESFiles/The maximum number of requests an application pool can process for each IIS 10.0 website must be explicitly set..bes"
	apacheUnixFile = "BESFiles/Warning and error messages displayed to clients must be modified to minimize the identity of the Apache web server, patches, loaded modules, and directory paths.bes"

	try:
		fileRoot = ParseBes(testLogger, el9File)
	except FileNotFoundError as e:
		testLogger.error(f"Aborting process. - {e}")
	except TypeError as e:
		testLogger.error(f"Aborting process. - {e}")
	except etree.ParseError as e:
		testLogger.error(f"Failed to parse bes file: {el9File} - {e}")
	
	scmData = fileRoot.ParseScmData()
	print(scmData)
	print(scmData['RHEL 9 must require users to provide a password for privilege escalation.']['RuleID'])
	print(scmData['RHEL 9 must require users to provide a password for privilege escalation.']['scmMeta'])
	print('description: ', scmData['RHEL 9 must require users to provide a password for privilege escalation.']['scmMeta']['description'])
