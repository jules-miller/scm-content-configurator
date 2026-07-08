import logging
from logging.handlers import RotatingFileHandler
import traceback
from pathlib import Path
import sys
import os

class LogConfig:
	
	def __init__(self, loggerName: str, maxSize: int, maxKeep: int) -> None:
		self.loggerName = loggerName # This will double as the name of the log file
		self.maxSize = maxSize
		self.maxKeep = maxKeep

	def ConfigureLogger(self) -> logging.Logger:
		if getattr(sys, 'frozen', False):           # Running as EXE built with pyinstaller
			exePath = os.path.dirname(sys.executable)
		elif __file__:                              # Running as script
			exePath = Path(__file__).parent / "../" # since this is running from the classes dir
			
		#logFile = Path(__file__).parent / f"../Logs/{self.loggerName}.log"
		logFile = os.path.join(exePath, f"Logs/{self.loggerName}.log")

		l = logging.getLogger(self.loggerName)
		formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
		fileHandler = RotatingFileHandler(logFile, maxBytes=self.maxSize, backupCount=self.maxKeep)
		fileHandler.setFormatter(formatter)

		l.setLevel(logging.INFO)
		l.addHandler(fileHandler)
		
		logger = logging.getLogger(self.loggerName)

		return logger
	
if __name__ == "__main__":
	import os
	os.makedirs(Path(__file__).parent / f"../Logs", exist_ok=True)

	from log_config import LogConfig
	logSetup = LogConfig('log_config_test', 20000000, 5)
	testLogger = logSetup.ConfigureLogger()
	testLogger.info("log config info test")