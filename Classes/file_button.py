import tkinter
import tkinter.filedialog
import customtkinter

class FileButton():
	def __init__(self, master, buttonTxt: str, fileType: str, placement: tuple, width: int):
		"""
		Creates a frame that glues the button and entry widgets together.
		The button will laumch the select file dialog window.

		Args:
			master: the parent widget (root/app object)
			buttonTxt: text to display in the button widget
			filyType: file extension that is use in SelectFile method
			placement: x, y pixel positions
			width: entry widget width
		"""
		# Create initial settings
		self._app = master
		self._buttonTxt = buttonTxt
		self._fileType = fileType
		self._x, self._y = placement
		self._width = width
		self._frame = customtkinter.CTkFrame(self._app)
		self._frame.pack(pady=5,anchor="center")
		self._frame.place(x=self._x, y=self._y)
		self._filePath = ''

		# Create entry and button
		self._entry = customtkinter.CTkEntry(self._frame, width=self._width)
		self._button = customtkinter.CTkButton(self._frame, text=self._buttonTxt, command=lambda: self._SelectFile())
		self._button.pack(side="left")
		self._entry.pack(side="left")

	## Getters ##
	@property
	def filePath(self):
		return self._filePath
	
	## Setters ##
	@filePath.setter
	def filePath(self, value: str):
		if type(value) != str:
			raise TypeError
		self._filePath = value


	def _SelectFile(self) -> None:
		filePath = tkinter.filedialog.askopenfilename(title=f"Select a {self._fileType} file.", filetypes=((f"{self._fileType} files", f"*.{self._fileType}"), ("All files", "*.*")))
		self._entry.configure(state="normal")
		self._entry.delete(0, customtkinter.END)
		self._entry.insert(0, filePath)
		self._entry.configure(state="readonly")
		self._filePath = filePath


if __name__ == "__main__":
	customtkinter.set_appearance_mode("Dark")
	customtkinter.set_default_color_theme("green")
	app = customtkinter.CTk() # creates main window instance
	app.title("SCM Description Updater")
	app.geometry("1000x500") # main window dimensions

	# Create file selector frames
	xlsxFrame = FileButton(app, "Select XLSX File", "xlsx", (50, 100), 700)
	besFrame = FileButton(app, "Select BES File", "bes", (50, 135), 700)

	app.mainloop()
