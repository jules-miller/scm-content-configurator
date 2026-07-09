# Changelog

### 07/02/25
	- v1.0 - original deployment
	- Built with:
		- Python 3.13
		- customtkinter==5.2.2
		- lxml==5.3.1
		- pandas==2.3.0
		- pillow==11.1.0
		- python-calamine==0.3.2

### 07/18/25
    - v1.1
    - updated UpdateScmMetadata() in the Execute class
        - changed how the json string conversion happens
        - this was to fix the json metdata from single quotes to double quotes around each key:value pair
		
### 12/15/25
    - v1.2
    - Python 3.14.0
        - customtkinter==5.2.2
        - pandas==2.3.3
        - lxml==6.0.2
        - openpyxl==3.1.5
        - python-calamine==0.6.1
    - In Execute.UpdateScmMeta() and UpdateDescription.Update(): 
        - removed the finally block altogether as it was not needed.
    - In Execute.InitializeXlsx()
        - Fixed bug where the exception output was not referenced correctly (added 'as e')
            - except Exception as e:
			- self._logger.error(f"Failed to create dataframe from xlsx file | {e}")
    - Fixed file path issues in the unit tests files 'test_execute.py', 'test_parse_bes.py', 'test_parse_xlsx.py', and 'test_updated_description'.  
        - All file paths referenced in this file are now relative to the parent directory.
        - Ex. besFile = (Path(__file__).parent / '../BESFiles/el9SiteTest.bes').resolve().as_posix()
