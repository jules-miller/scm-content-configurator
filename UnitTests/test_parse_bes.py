import unittest
from unittest.mock import patch
import os
import sys
from lxml import etree
from pathlib import Path

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from parse_bes import ParseBes

logSetup = LogConfig('parse_bes_unittesting', 20000000, 5)
testLogger = logSetup.ConfigureLogger()
testLogger.info(50 * '#')
testLogger.info("######### Starting ParseBes Unit Testing #########")

besFile = (Path(__file__).parent / '../BESFiles/el9SiteTest.bes').resolve().as_posix()
disaFile = (Path(__file__).parent / '../BESFiles/disa_el9_test.bes').resolve().as_posix()
missingValuesFile = (Path(__file__).parent / '../BESFiles/el9SiteTestMissingVal.bes').resolve().as_posix()
missingFile = (Path(__file__).parent / '../BESFiles/el9SiteTestMissing.bes').resolve().as_posix()
invalidFile = (Path(__file__).parent / '../BESFiles/el9SiteTest.txt').resolve().as_posix()
missingRulesFile = (Path(__file__).parent / '../BESFiles/el9SiteTest_missing_rules.bes').resolve().as_posix()

class TestParseBes(unittest.TestCase):
	# Test _CheckFile success
	def test_CheckFileSuccess(self):
		instance = ParseBes(testLogger, besFile)
		self.assertEqual(instance.file, besFile)

	# Test _CheckFile missing file
	def test_CheckFileMissing(self):
		with self.assertRaises(FileNotFoundError):
			ParseBes(testLogger, missingFile)

	# Test_CheckFile invalid file format
	def test_CheckFileInvalid(self):
		with self.assertRaises(TypeError):
			ParseBes(testLogger, invalidFile)
	
	# Test _GetRoot success
	def test_GetRoot(self):
		instance = ParseBes(testLogger, besFile)
		self.assertEqual(type(instance.tree), etree._ElementTree)
		self.assertEqual(type(instance.root), etree._Element)

	# Test _GetTitle success
	def test_GetTitle(self):
		instance = ParseBes(testLogger, besFile)
		titles = instance._GetTitle()
		self.assertEqual(len(titles), 3)

	# Test _GetRule success str
	def test_GetRuleStr(self):
		value = "V-214267"
		instance = ParseBes(testLogger, besFile)
		result = instance._GetRule(value)
		self.assertEqual(result, value)

	# Test _GetRule success dictionary
	def test_GetRuleDict(self):
		value = {'disa_vulid' : "V-214267"}
		instance = ParseBes(testLogger, besFile)
		result = instance._GetRule(value)
		self.assertEqual(result, value['disa_vulid'])

	# Test _GetRule - rule not found
	def test_GetRuleNotFound(self):
		value = "invalidRule"
		instance = ParseBes(testLogger, besFile)
		result = instance._GetRule(value)
		self.assertEqual(result, 'notFound')

	# Test ReadMime - success
	def test_ReadMimeSuccess(self):
		expectedValue = "No CCEs provided"
		instance = ParseBes(testLogger, besFile)
		for element in instance.tree.findall('.//Fixlet'): # iterates through each Fixlet tag
			for subElement in element: # iterates through each subtag in the Fixlet tag
					scmCtrlVal = instance.ReadMime(element, instance.scmCtrlMime)
		self.assertEqual(scmCtrlVal, expectedValue)

	# Test ReadMime - no value found
	def test_ReadMimeNotFound(self):
		expectedValue = ""
		instance = ParseBes(testLogger, besFile)
		for element in instance.tree.findall('.//Fixlet'): # iterates through each Fixlet tag
			for subElement in element: # iterates through each subtag in the Fixlet tag
					scmCtrlVal = instance.ReadMime(element, 'missingField')
		self.assertEqual(scmCtrlVal, expectedValue)

	# Test ConvertJson - success
	def test_ConvertJsonSuccess(self):
		value = '{"key1":"value1","key2":"value2"}'
		expectedResult = {"key1":"value1","key2":"value2"}
		instance = ParseBes(testLogger, besFile)
		result = instance.ConvertJson(value)
		self.assertEqual(type(result), dict)
		self.assertEqual(result, expectedResult)

	# Test ConvertJson - failed to convert data
	def test_ConvertJsonFail(self):
		value = 'test.string.'
		expectedResult = ''
		instance = ParseBes(testLogger, besFile)
		result = instance.ConvertJson(value)
		self.assertEqual(type(result), str)
		self.assertEqual(result, expectedResult)

	# Test ParseScmData success
	def test_ParseScmDataSuccess(self):
		firstTitle = 'RHEL 9 system accounts must not have an interactive login shell.'
		firstRuleID = 'V-258046'
		instance = ParseBes(testLogger, besFile)
		result = instance.ParseScmData()
		self.assertEqual(len(result), 3)
		self.assertEqual(type(result[firstTitle]), dict)
		self.assertEqual(result[firstTitle]['RuleID'], firstRuleID)

	# Test ParseScmData - unable to obtain rule id
	def test_ParseScmDataErr(self):
		instance = ParseBes(testLogger, missingRulesFile)
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			result = instance.ParseScmData()
		self.assertIn("ERROR:parse_bes_unittesting:Unable to obtain rule id for RHEL 9 system accounts must not have an interactive login shell.", cm.output)
		self.assertIn("ERROR:parse_bes_unittesting:Continuing to next element.", cm.output)

	# Test UpdatedScmMetadata success
	def test_UpdateScmMetadataSuccess(self):
		instance = ParseBes(testLogger, besFile)
		title = 'RHEL 9 must require users to provide a password for privilege escalation.'
		value = 'test value 1'
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			result = instance.UpdateScmMetadata(title, value)
		self.assertIn(f"INFO:parse_bes_unittesting:Successfully updated the value of {instance.scmMetaMime} for fixlet '{title}'", cm.output)

	# Test WriteBesSuccess
	def test_WriteBesSuccess(self):
		instance = ParseBes(testLogger, besFile)
		outputFile = (Path(__file__).parent / '../BESFiles/outputTest.bes').resolve().as_posix()
		# delete file before running test
		try:
			os.remove(outputFile)
		except Exception:
			pass
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			instance.WriteBes(outputFile)
			result = os.path.isfile(outputFile)
			self.assertEqual(result, True)
		self.assertIn(f"INFO:parse_bes_unittesting:Output written to '{outputFile}'", cm.output)
	
	def test_WriteBesFailure(self):
		instance = ParseBes(testLogger, besFile)
		outputFile = 123
		# delete file before running test
		try:
			os.remove(outputFile)
		except Exception:
			pass
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			instance.WriteBes(outputFile)
			result = os.path.isfile(outputFile)
			self.assertEqual(result, False)
		self.assertIn(f"ERROR:parse_bes_unittesting:Failed to write output to '{outputFile}'", cm.output[0])

	# Test RemoveSiteRelevance success
	def test_RemoveSiteRelevanceSuccess(self):
		instance = ParseBes(testLogger, besFile)
		title = 'RHEL 9 must require users to provide a password for privilege escalation.'
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			result = instance.RemoveSiteRelevance()
		self.assertIn(f"INFO:parse_bes_unittesting:Removed site level relevance for fixlet '{title}'", cm.output)

	# Test RemoveSiteRelevance no site level relevance found
	def test_RemoveSiteRelevanceNone(self):
		instance = ParseBes(testLogger, missingValuesFile)
		result = instance.RemoveSiteRelevance()  # any exceptions thrown will fail the unit test
		self.assertEqual(None, result)

	# Test RemoveActionScript success
	def test_RemoveActionScriptSuccess(self):
		instance = ParseBes(testLogger, disaFile)
		title = 'RHEL 9 must require users to provide a password for privilege escalation.'
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			result = instance.RemoveActionScript()
		self.assertIn(f"INFO:parse_bes_unittesting:Removed default action for fixlet '{title}'", cm.output)

	# Test RemoveActionScript no action script found
	def test_RemoveActionScriptNone(self):
		instance = ParseBes(testLogger, besFile)
		result = instance.RemoveActionScript() # any exceptions thrown will fail the unit test
		self.assertEqual(None, result)

	# Test ReplaceRelevance success
	def test_ReplaceRelevanceSuccess(self):
		instance = ParseBes(testLogger, disaFile)
		title = 'RHEL 9 system accounts must not have an interactive login shell.'
		oldStr = 'parenthesized part of'
		newStr = 'parenthesized parts 1 of'
		with self.assertLogs(testLogger, level='DEBUG') as cm:
			result = instance.ReplaceRelevance(oldStr, newStr)
		self.assertIn(f"INFO:parse_bes_unittesting:Replaced '{oldStr}' with '{newStr}' in fixlet: {title}", cm.output)

	# Test ReplaceRelevance nothing to replace
	def test_ReplaceRelevanceNone(self):
		instance = ParseBes(testLogger, besFile)
		oldStr = 'parenthesized part of'
		newStr = 'parenthesized parts 1 of'
		result = instance.ReplaceRelevance(oldStr, newStr) # any exceptions thrown will fail the unit test
		self.assertEqual(None, result)

if __name__ == '__main__':
	unittest.main()