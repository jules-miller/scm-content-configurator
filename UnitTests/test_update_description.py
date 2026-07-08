import unittest
from unittest.mock import patch
import os
import sys
from lxml import etree
from pathlib import Path

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from update_description import UpdateDescription

logSetup = LogConfig('update_description_unittesting', 20000000, 5)
testLogger = logSetup.ConfigureLogger()
testLogger.info(50 * '#')
testLogger.info("######### Starting UpdateDescription Unit Testing #########")

logFile = 'update_description_unittesting.log'
besFile = (Path(__file__).parent / '../BESFiles/el9SiteTest.bes').resolve().as_posix()
besFileNotXml = (Path(__file__).parent / '../BESFiles/el9SiteTestNotXml.bes').resolve().as_posix()
besFileScmMissing = (Path(__file__).parent / '../BESFiles/el9SiteTestScmMissing.bes').resolve().as_posix()
invalidBes = (Path(__file__).parent / '../BESFiles/el9SiteTest.txt').resolve().as_posix()
xlsxFile = (Path(__file__).parent / '../BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2.xlsx').resolve().as_posix()
invalidXlsx = (Path(__file__).parent / '../BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2.csv').resolve().as_posix()
xlsxFormatErr = (Path(__file__).parent / '../BCM Controls/invalidFormat.xlsx').resolve().as_posix()

class TestUpdateDescription(unittest.TestCase):
	# Test empty xlsx file arg
	def test_UpdateEmptyXlsxArg(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, '', besFile)
		self.assertEqual(result, 1)
	
	# Test empty bes file arg
	def test_UpdateEmptyBesArg(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, xlsxFile, '')
		self.assertEqual(result, 2)

	# Test missingy bes file 
	def test_UpdateMissingBes(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, xlsxFile, f'{besFile}error')
		self.assertEqual(result, 3)

	# Test incorrect bes file  type
	def test_UpdateBesType(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, xlsxFile, invalidBes)
		self.assertEqual(result, 4)

	# Test parsing a bes file that is not in xml format
	def test_UpdateParseErr(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, xlsxFile, besFileNotXml)
		self.assertEqual(result, 5)

	# Test parsing a bes file that is missing scm metadata section for one of the fixlets
	def test_UpdateScmMissing(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, xlsxFile, besFileScmMissing)
		self.assertEqual(result, 11) # ParseBes.ParseScmData() should handle this and skip to next fixlet if scm metadata is missing (errCt increase)
	
	# Test missingy xlsx file 
	def test_UpdateMissingXlsx(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, f'{xlsxFile}error', besFile)
		self.assertEqual(result, 7)

	# Test incorrect xlsx file type
	def test_UpdateXlsxType(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, invalidXlsx, besFile)
		self.assertEqual(result, 8)
	
	# Test success
	def test_UpdateSuccess(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, xlsxFile, besFile)
		self.assertEqual(result, 0)

	# Test xlsx file does not actually contain data in xlsx format
	def test_UpdateXlsxInvalidFormat(self):
		instance = UpdateDescription(testLogger)
		result = instance.Update(logFile, xlsxFormatErr, besFile)
		self.assertEqual(result, 10)
		

if __name__ == '__main__':
	unittest.main()