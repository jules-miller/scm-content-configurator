############### Utils ##########
# Static methods for various uses ##
####################################

import logging
import traceback

class Utils():
	"""
	Collection of miscellaneous static methods.
	"""
	def __init__(self):
		pass
	
	@staticmethod
	def DescToHtml(title: str, ruleId: str, chkContent: str, fixText: str) -> str:
		"""
		Creates a new description string based on the supplied args.
		title = name of fixlet
		ruleId = rule/vuln id
		chkContent = the VA Check Content or Source Check Content
		fixText = the VA Fix Text or Source Fix Text

		Returns the description in html format.
		"""
		chkContent = chkContent.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;') # convert html escape characters
		fixText = fixText.replace('&', '&amp;').replace('>', '&gt;').replace('<', '&lt;') # convert html escape characters
		chkContent = chkContent.replace(r'\n', '<br>') # convert newline characters to html break
		fixText = fixText.replace(r'\n', '<br>') # convert newline characters to html break
		chkContent = chkContent.replace(r'\r', '') # remove carriage return escape character
		fixText = fixText.replace(r'\r', '') # remove carriage return escape character

		value = fr"<b>{title}</b><br>{ruleId}<br><br><b>Check Content</b><br><br>{chkContent}<br><br><b>Fix Text</b><br>{fixText}"
		return value
	
	@staticmethod
	def NewBesFN(file: str) -> str:
		"""
		Generates a string containing the filePath with '_UPDATED' appended before the .bes file extension.
		filePath: the original bes file path

		Returns the new file path as a string
		"""
		fileInfo = file.rsplit("/", 1) # split string into file path and file name
		filePath = fileInfo[0]
		fileName = fileInfo[1].rsplit('.', 1) # split file name string into name and the extension
		newFilePath = filePath + '/' + f'{fileName[0]}_UPDATED.bes'
		return newFilePath
	
if __name__ =='__main__':
	pass