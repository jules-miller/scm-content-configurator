import unittest
from unittest.mock import patch
import sys
import os
import logging
from pathlib import Path

import pandas.core
import pandas.core.frame
import pandas.core.series

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from parse_xlsx import ParseXlsx

logSetup = LogConfig('parse_xlsx_unittesting', 20000000, 5)
testLogger = logSetup.ConfigureLogger()
testLogger.info(50 * '#')
testLogger.info("######### Starting ParseXlsx Unit Testing #########")

xlsxFile = (Path(__file__).parent / '../BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2.xlsx').resolve().as_posix()
titleMissingXlsxFile = (Path(__file__).parent / '../BCM Controls/Windows_Server_2019_STIG-Controls Checklist-V1R3_TITLE_MISSING.xlsx').resolve().as_posix()
solXlsxFile = (Path(__file__).parent / '../BCM Controls/Copy of Solaris_11_SPARC_STIG-Controls Checklist-V1R16.xlsx').resolve().as_posix()
invalidFormatFile = (Path(__file__).parent / '../BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2.csv').resolve().as_posix()
missingFile = (Path(__file__).parent / '../BCM Controls/Copy of RHEL_9_STIG-Controls Checklist-V1R2_MISSING.xlsx').resolve().as_posix()

class TestParseXlsx(unittest.TestCase):
    # Test _CheckFile success
    def test_CheckFileSuccess(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        self.assertEqual(instance.file, xlsxFile)

    # Test _CheckFile missing file
    def test_CheckFileMissing(self):
        with self.assertRaises(FileNotFoundError):
            ParseXlsx(testLogger, missingFile)

    # Test_CheckFile invalid file format
    def test_CheckFileInvalid(self):
        with self.assertRaises(TypeError):
            ParseXlsx(testLogger, invalidFormatFile)

    # Test _ValidateType success
    def test_ValidateTypeSuccess(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance._ValidateType('string', str, 'test string')

    # Test _ValidateType incorrect data dtype
    def test_ValidateTypeError(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        with self.assertRaises(TypeError):
            instance._ValidateType('string', list, 'test string')

    # Test _ValidateSheetName success
    def test_ValidateSheetNameSuccess(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance._ValidateSheetName(instance.controlsSheet) 

    # Test _ValidateSheetName - missing sheet name
    def test_ValidateSheetNameError(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        with self.assertRaises(ValueError):
            instance._ValidateSheetName('sheet does not exist')

    # Test _ValidateColumns success
    def test_ValidateColumnsSuccess(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance._ValidateColumns(instance.controlsSheet, instance.ruleColSet)

    # Test _ValidateColumns  - missing column
    def test_ValidateColumnsError(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        with self.assertRaises(ValueError):
            instance._ValidateColumns(instance.controlsSheet, list(instance.vulnColSet.keys()))

    # Test _CreateDataframe success
    def test_CreateDataframeSuccess(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        dataframe = instance._CreateDataframe(instance.controlsSheet, list(instance.ruleColSet.keys()))
        self.assertEqual(type(dataframe), pandas.core.frame.DataFrame)

    # Test _ParseCellData success
    def test_ParseCellDataSuccess(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        dataFrame = instance._CreateDataframe(instance.controlsSheet, list(instance.ruleColSet.keys()))
        cellData = instance._ParseCellData(dataFrame, instance.controlsIDHeader, 'V-258241', 'Source Check Content')
        self.assertEqual(type(cellData), pandas.core.series.Series)
        self.assertGreater(len(cellData), 0)

    # Test _ParseCellData invalid dataframe arg
    def test_ParseCellDataInvalidDf(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        with self.assertRaises(TypeError):
            instance._ParseCellData('invaliddf', instance.controlsIDHeader, 'V-258241', 'Source Check Content')

    # Test _ParseCellData  - empty dataframe
    def test_ParseCellDataEmptyDf(self):
        emptyFrame = pandas.core.frame.DataFrame([])
        instance = ParseXlsx(testLogger, xlsxFile)
        with self.assertRaises(ValueError):
            instance._ParseCellData(emptyFrame, instance.controlsIDHeader, 'V-258241', 'Source Check Content')

    # Test _IsCellEmpty - False
    def test_IsCellEmptyFalse(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        dataFrame = instance._CreateDataframe(instance.controlsSheet, list(instance.ruleColSet.keys()))
        cellData = instance._ParseCellData(dataFrame, instance.controlsIDHeader, 'V-258241', 'Source Check Content')
        emptyCheck = instance._IsCellEmpty(cellData)
        self.assertEqual(emptyCheck, False)

    # Test _IsCellEmpty - True
    def test_IsCellEmptyTrue(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        dataFrame = instance._CreateDataframe(instance.controlsSheet, list(instance.ruleColSet.keys()))
        cellData = instance._ParseCellData(dataFrame, instance.controlsIDHeader, 'V-258241', 'VA Check Content')
        emptyCheck = instance._IsCellEmpty(cellData)
        self.assertEqual(emptyCheck, True)

    # Test GrabCellValeStr - len > 0
    def test_GrabCellValueStr(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        dataFrame = instance._CreateDataframe(instance.controlsSheet, list(instance.ruleColSet.keys()))
        cellData = instance._ParseCellData(dataFrame, instance.controlsIDHeader, 'V-258241', 'Source Check Content')
        convertToStr = instance.GrabCellValueStr(cellData)
        self.assertEqual(type(convertToStr), str)
        self.assertGreater(len(convertToStr), 0)

    # Test GrabCellValeStr - empty string
    def test_GrabCellValueStrEmpty(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        dataFrame = instance._CreateDataframe(instance.controlsSheet, list(instance.ruleColSet.keys()))
        cellData = instance._ParseCellData(dataFrame, instance.controlsIDHeader, 'V-258241', 'VA Check Content')
        convertToStr = instance.GrabCellValueStr(cellData)
        self.assertEqual(type(convertToStr), str)
        self.assertEqual(len(convertToStr), 0)
    
    # Test _SetTitleCol - VA Rule Title - use rhel xlsx
    def test_SetTitleColVA(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance._SetTitleCol()
        self.assertEqual(instance._titleHeader, 'VA Rule Title')

    # Test _SetTitleCol - Rule Title - use solaris xlsx
    def test_SetTitleColDef(self):
        instance = ParseXlsx(testLogger, solXlsxFile)
        instance._SetTitleCol()
        self.assertEqual(instance._titleHeader, 'Rule Title')

    # Test _SetTitleCol - Title col missing
    def test_SetTitleColNone(self):
        instance = ParseXlsx(testLogger, titleMissingXlsxFile)
        instance._SetTitleCol()
        self.assertEqual(instance._titleHeader, '')

    # Test GetControlsDF - success
    def test_GetControlsDFSuccess(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        self.assertEqual(type(instance.controlsDF), pandas.core.frame.DataFrame)
        self.assertEqual(instance.controlsIDHeader, 'Rule ID')

    # Test GetControlsDF - success with includeTitle = True
    def test_GetControlsDFTitle(self):
        instance = ParseXlsx(testLogger, xlsxFile, includeTitle=True)
        with self.assertLogs(testLogger) as cm1:
            instance.GetControlsDF()
            self.assertEqual(type(instance.controlsDF), pandas.core.frame.DataFrame)
            self.assertEqual(instance.controlsIDHeader, 'Rule ID')
            self.assertEqual(instance._titleHeader, 'VA Rule Title')
        self.assertIn(f"INFO:parse_xlsx_unittesting:Successfully created dataframe | Sheet: {instance.controlsSheet} | Columns: ['Rule ID', 'Source Check Content', 'VA Check Content', 'Source Fix Text', 'VA Fix Text', 'VA Rule Title']", cm1.output)

    # Test GetControlsDF - mock self.ruleColSet class var to force value error - rule id and vuln id missing
    @patch.object(ParseXlsx, "ruleColSet", {"vuln id": str})
    def test_GetControlsDFValueErr(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        with self.assertLogs(testLogger, level='DEBUG') as cm:
            result = instance.GetControlsDF()
            self.assertEqual(result, 'ParseError')
        self.assertIn("ERROR:parse_xlsx_unittesting:One or more required columns are missing from the xlsx file. Aborting process.", cm.output)

    # Test GetDesc Success
    def test_GetDesc(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        desc = instance.GetDesc('V-258240')
        self.assertIn('Verify the OpenSSL library is configured to use only VA-approved TLS encryption', desc['chkContent'])
        self.assertIn('Configure the RHEL 9 OpenSSL library to use only VA-approved TLS encryption', desc['fixText'])

    # Test GetDesc - no data found
    def test_GetDescDataMissing(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        desc = instance.GetDesc('missingRule')
        self.assertEqual(desc, 'ruleNotFound')

    # Test GetDesc - dfNotSet
    def test_GetDescDFErr(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        desc = instance.GetDesc('V-258240')
        self.assertEqual(desc, 'dfNotSet')

    # Test GetDesc - VA content
    def test_GetDescDFVA(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        desc = instance.GetDesc('V-258240')
        self.assertIn('Verify the OpenSSL library is configured to use only VA-approved TLS encryption', desc['chkContent'])
        self.assertIn('Configure the RHEL 9 OpenSSL library to use only VA-approved TLS', desc['fixText'])

    # Test GetDesc - Source content failover because VA content is missing
    def test_GetDescDFSource(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        desc = instance.GetDesc('V-258241')
        self.assertIn('Verify that the RHEL 9 cryptography policy has been configured correctly with', desc['chkContent'])
        self.assertIn('Configure the operating system to implement FIPS mode with the following command', desc['fixText'])
    
    # Test _DoesRuleExist True
    def test_DoesRuleExistTrue(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        desc = instance._DoesRuleExist('V-258241')
        self.assertEqual(desc, True)

    # Test _DoesRuleExist False
    def test_DoesRuleExistFalse(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        desc = instance._DoesRuleExist('doesnotexist')
        self.assertEqual(desc, False)

    # test GetTitle success - VA Rule Title
    def test_GetTitleVA(self):
        instance = ParseXlsx(testLogger, xlsxFile, includeTitle=True)
        instance.GetControlsDF()
        self.assertEqual(type(instance.controlsDF), pandas.core.frame.DataFrame)
        self.assertEqual(instance.controlsIDHeader, 'Rule ID')
        self.assertEqual(instance._titleHeader, 'VA Rule Title')
        title = instance.GetTitle('V-258240')
        expectedTitle = 'RHEL 9 must implement VA-approved TLS encryption in the OpenSSL package.'
        self.assertEqual(title, expectedTitle)

    # test GetTitle success Rule Title
    def test_GetTitleDefRule(self):
        instance = ParseXlsx(testLogger, solXlsxFile, includeTitle=True)
        instance.GetControlsDF()
        self.assertEqual(type(instance.controlsDF), pandas.core.frame.DataFrame)
        self.assertEqual(instance.controlsIDHeader, 'Vuln ID')
        self.assertEqual(instance._titleHeader, 'Rule Title')
        title = instance.GetTitle('V-216455')
        expectedTitle = 'The operating system must implement transaction recovery for transaction-based systems.'
        self.assertEqual(title, expectedTitle)

    # test GetTitle - rule not found
    def test_GetTitleRuleMissing(self):
        instance = ParseXlsx(testLogger, xlsxFile)
        instance.GetControlsDF()
        title = instance.GetTitle('missingRule')
        self.assertEqual(title, 'ruleNotFound')

    # test GetTitle dfNotSet
    def test_GetTitleDFErr(self):
        instance = ParseXlsx(testLogger, xlsxFile, includeTitle=True)
        title = instance.GetTitle('V-258240')
        self.assertEqual(title, 'dfNotSet')


if __name__ == '__main__':
	unittest.main()