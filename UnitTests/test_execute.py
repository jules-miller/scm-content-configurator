import unittest
from unittest.mock import patch
import os
import sys
from lxml import etree
from pathlib import Path

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from execute import Execute

logSetup = LogConfig('execute_unittesting', 20000000, 5)
testLogger = logSetup.ConfigureLogger()
testLogger.info(50 * '#')
testLogger.info("######### Starting Execute Unit Testing #########")

logFile = 'execute_unittesting.log'
besFile = (Path(__file__).parent / '../BESFiles/el9SiteTest.bes').resolve().as_posix()
besFileNotXml = (Path(__file__).parent / "../BESFiles/el9SiteTestNotXml.bes").resolve().as_posix()
besFileScmMissing = (Path(__file__).parent / "../BESFiles/el9SiteTestScmMissing.bes").resolve().as_posix()
invalidBes = (Path(__file__).parent / "../BESFiles/el9SiteTest.txt").resolve().as_posix()
xlsxFile = (Path(__file__).parent /  "../BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2.xlsx").resolve().as_posix()
invalidXlsx = (Path(__file__).parent /  "../BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2.csv").resolve().as_posix()
xlsxFormatErr = (Path(__file__).parent /  "../BCM Controls/invalidFormat.xlsx").resolve().as_posix()

class TestExecute(unittest.TestCase):
	# Test class instantiation
	def test_InitExecute(self):
		instance = Execute(testLogger, besFile)
		self.assertEqual(instance._besFile, besFile)
		self.assertEqual(instance._xlsxFile, '')
		self.assertEqual(instance._outputFile, '')
		self.assertEqual(instance._besInstance, None)
		self.assertEqual(instance._parseXlsx, None)
		self.assertEqual(instance._errCt, 0)
		
	# InitialzeBes success
	def test_InitBesSuccess(self):
		instance = Execute(testLogger, besFile)
		result = instance.InitialzeBes()
		self.assertEqual(result, 0)
		self.assertNotEqual(instance.besInstance, None)

	# InitialzeBes bes file not found
	def test_InitBesMissingBes(self):
		instance = Execute(testLogger, f'{besFile}error')
		result = instance.InitialzeBes()
		self.assertEqual(result, 3)

	# Test incorrect bes file  type
	def test_InitBesType(self):
		instance = Execute(testLogger, invalidBes)
		result = instance.InitialzeBes()
		self.assertEqual(result, 4)

	# Test parsing a bes file that is not in xml format
	def test_InitBesParseErr(self):
		instance = Execute(testLogger, besFileNotXml)
		result = instance.InitialzeBes()
		self.assertEqual(result, 5)
		
	# Test InitializeXlsx Success
	def test_InitXlsxSuccess(self):
		instance = Execute(testLogger, besFile)
		result = instance.InitializeXlsx(xlsxFile)
		self.assertEqual(result, 0)
		self.assertNotEqual(instance.parseXlsx, None)
		
	# Test missingy xlsx file 
	def test_UpdateMissingXlsx(self):
		instance = Execute(testLogger, besFile)
		result = instance.InitializeXlsx(f'{xlsxFile}error')
		self.assertEqual(result, 7)

	# Test incorrect xlsx file type
	def test_UpdateXlsxType(self):
		instance = Execute(testLogger, besFile)
		result = instance.InitializeXlsx(invalidXlsx)
		self.assertEqual(result, 8)

	# Test xlsx file does not actually contain data in xlsx format
	def test_UpdateXlsxInvalidFormat(self):
		instance = Execute(testLogger, besFile)
		result = instance.InitializeXlsx(xlsxFormatErr)
		self.assertEqual(result, 10)
	
	# Test UpdateDescription complete
	def test_UpdateDescrComplete(self):
		instance = Execute(testLogger, besFile)
		besInstance = instance.InitialzeBes()
		parseXlsx = instance.InitializeXlsx(xlsxFile)
		result = instance.UpdateScmMeta()
		self.assertEqual(result, 'Process Complete')

	# test successful update descr with includeTitle=True
	def test_UpdateDescrInclTitle(self):
		instance = Execute(testLogger, besFile)
		besInstance = instance.InitialzeBes()
		parseXlsx = instance.InitializeXlsx(xlsxFile, includeTitle=True)
		result = instance.UpdateScmMeta()
		self.assertEqual(result, 'Process Complete')
		
	# Test UpdateDescription Failed to parse scm metadata
	def test_UpdateDescrParseErr(self):
		instance = Execute(testLogger, besFile)
		besInstance = instance.InitialzeBes()
		parseXlsx = instance.InitializeXlsx(xlsxFile)
		instance.besInstance._tree = None  # reset tree to none - this should never happen during normal runtime
		result = instance.UpdateScmMeta()
		self.assertEqual(result, 'Failed to parse scm metadata in BES file.')

	# Test UpdateDescription complete with errors
	def test_UpdateDescrCompErr(self):
		instance = Execute(testLogger, besFile)
		besInstance = instance.InitialzeBes()
		parseXlsx = instance.InitializeXlsx(xlsxFile)
		instance._errCt += 1  
		result = instance.UpdateScmMeta()
		self.assertEqual(result, 'Process Complete with Errors')

if __name__ == '__main__':
	unittest.main()
