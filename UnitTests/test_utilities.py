import unittest
import os
import sys

# Append the Classes directory to Python's path so that it can find the module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../Classes'))

from log_config import LogConfig
from utils import Utils

logSetup = LogConfig('utilities_unittesting', 20000000, 5)
testLogger = logSetup.ConfigureLogger()
testLogger.info(50 * '#')
testLogger.info("######### Starting Utilities Unit Testing #########")

title = 'RHEL 9 must require users to provide a password for privilege escalation.'
ruleId = 'V-258106'
chkContent = r'Verify the OpenSSL library is configured to use only VA-approved TLS encryption:\n'
fixText = r'Configure the RHEL 9 OpenSSL library to use only VA-approved TLS encryption by editing the following line in the "/etc/crypto-policies/back-ends/opensslcnf.config" file:\n\n'

class TestUtils(unittest.TestCase):
  
    def test_DescToHtmlSuccess(self):
        result = Utils.DescToHtml(title, ruleId, chkContent, fixText)
        self.assertIn(f'<b>{title}</b>', result)
        self.assertIn(ruleId, result)
        self.assertIn(chkContent.replace(r'\n', '<br>'), result)

    def test_NewBesFN(self):
        expectedResult = "C:/TestPath1/TestPath2/file1_UPDATED.bes"
        result = Utils.NewBesFN("C:/TestPath1/TestPath2/file1.bes")
        self.assertEqual(result, expectedResult)

if __name__ == '__main__':
	unittest.main()