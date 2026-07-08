# SCM Content Configurator

## Summary
The SCM Content Configurator tool automates the update/modification of a BES file based on the selected actions (Update Description, Update Title, Remove Site Relevance, Remove Action Script, Replace Parenthesized Part).  This is intended for BigFix Compliance fixlets or sites.

*NOTE: Ensure you have removed hidden data from the XLSX file before executing. This will drastically reduce execution times. Open XLSX in Excel > File > Info > Check for Issues > Inspect Document > Remove 'Custom XML Data' and 'Hidden Rows and Columns'*

## Screenshots

## Usage
Select XLSX File: The security controls Excel file pulled from the Baseline Configuration Management site. ** Must be in XLSX format **

Select BES File: The BES file exported from the Console for a given site. This can be a single Fixlet or an entire site's worth of fixlets concatenated together in a single BES file.

### Update Description
A XLSX and BES file must be specified.  Updates the description in the SCM Metadata MIMEField based off data in the security controls XLSX file.
### Update Title
A XLSX and BES file must be specified.  Updates the title in the SCM Metadata MIMEField (both the title key and the title set in the first line of the description) and the main Title tag in the fixlet based off data in the security controls XLSX file. ** Update Description must also be checked to run this.  Update Title can not be executed without also running Update Description.
### Remove Site Relevance
Removes all relevance containing 'proxy agent context'.  Only site level relevance should contain 'proxy agent context' in compliance fixlets.
### Remove Action Script
Removes all DefaultAction and Action data.
### Replace Parenthesized Part
Replaces 'parenthesized parts of' and 'parenthesized part of' with 'parenthesized parts 1 of' in relevance.
### Execute
Starts the processing based off the selected actions (checkboxes).

## Build Details:
Install modules from the requirements.txt file in your python environment, Then build the executable with the command below.

`pyinstaller.exe --clean --uac-admin --noconsole --onedir --icon="./va_logo_small.ico" -n SCMFixletUpdater.exe --hidden-import=numpy --version-file .\scmFixletUpdater_version_file.txt -p "Classes" --add-data "./va_logo_sm.ico:." --add-data "./va-logo.png:." --add-data "./README.txt:." --hidden-import=numpy._core._exceptions --contents-directory "." .\main.py`

Instead of applying all the switches in the build command above, the args can be placed in the SCMFixletUpdater.exe.spec file if needed.
Ensure the 'scmFixletUpdater_version_file.txt' file is updated prior to building.

Ensure your current working directory contains the icon and files specified in '--add-data' if using the exact command listed above.

## Changelog

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
