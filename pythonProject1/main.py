import os
import subprocess
import piexif
from tkinter import Tk, Label, Button, StringVar, END, LEFT, RIGHT, Y, SINGLE, Listbox, Scrollbar, Canvas, messagebox
from tkinter.filedialog import askdirectory
from PIL import Image
from tqdm import tqdm
import ttkbootstrap as ttkb


class MetadataRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Metadata Remover")
        self.root.geometry("600x400")

        # Use ttkbootstrap for styling and apply dark theme
        self.style = ttkb.Style()
        self.style.theme_use('darkly')  # Apply the dark theme

        # Configure styles for widgets
        self.style.configure('TLabel', font=('Arial', 12), padding=6, foreground='white')
        self.style.configure('TProgressbar', thickness=30)  # Use default progress bar style

        # Create and place the status label at the top
        self.status_var = StringVar()
        self.status_var.set("Select a folder to start processing.")
        self.status_label = ttkb.Label(root, textvariable=self.status_var, wraplength=550)
        self.status_label.pack(pady=10, anchor="center")

        # Create and place the progress bar with default style
        self.progress = ttkb.Progressbar(root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(padx=10, pady=5, fill="x")

        # Create a canvas to overlay the progress text on the progress bar
        self.canvas = Canvas(root, width=500, height=20, bg='black', highlightthickness=0)
        self.canvas.pack(padx=10, pady=5, fill="x")

        # Create a container frame to hold the console and scrollbar
        self.console_frame = ttkb.Frame(root, padding=5)
        self.console_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Create and place the console with a scrollbar in the container frame
        self.console = Listbox(self.console_frame, selectmode=SINGLE, relief='sunken', bd=0, highlightthickness=0,
                               fg='white', bg='#3d3d3d')
        self.console.pack(side=LEFT, fill="both", expand=True)

        self.scrollbar = Scrollbar(self.console_frame, command=self.console.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.console.config(yscrollcommand=self.scrollbar.set)

        # Create a frame to hold the buttons
        self.button_frame = ttkb.Frame(root, padding=5)
        self.button_frame.pack(padx=10, pady=10, side="bottom")

        # Create and place the browse button and copy log button side by side
        self.browse_button = ttkb.Button(self.button_frame, text="Select Folder", command=self.select_folder)
        self.browse_button.pack(side="left", padx=5)

        self.copy_button = ttkb.Button(self.button_frame, text="Copy Log", command=self.copy_log)
        self.copy_button.pack(side="left", padx=5)

    def select_folder(self):
        folder_selected = askdirectory(title="Select Folder")
        if folder_selected:
            self.process_directory(folder_selected)
        else:
            self.console.insert(END, "No folder selected.\n")

    def remove_metadata(self, file_path):
        try:
            # Check for file type and handle accordingly
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                # Remove EXIF metadata from JPEG files
                piexif.remove(file_path)
                # Save the image to ensure metadata is stripped
                with Image.open(file_path) as img:
                    img.save(file_path)
                self.console.insert(END, f"Removed metadata from: {file_path}\n")
            elif file_path.lower().endswith(('.mp4', '.mov')):
                # Remove metadata from video files using ffmpeg
                temp_file = file_path + '.tmp.mp4'
                try:
                    result = subprocess.run([
                        'ffmpeg', '-i', file_path, '-map_metadata', '-1',
                        '-c:v', 'copy', '-c:a', 'copy', temp_file
                    ], capture_output=True, text=True)

                    if result.returncode == 0:
                        # Replace original file with new file
                        os.replace(temp_file, file_path)
                        self.console.insert(END, f"Removed metadata from: {file_path}\n")
                    else:
                        self.console.insert(END, f"Failed to remove metadata from: {file_path}\n")
                        self.console.insert(END, result.stderr + "\n")
                except FileNotFoundError:
                    self.console.insert(END, "ffmpeg not found. Ensure ffmpeg is installed and in your PATH.\n")
                except Exception as e:
                    self.console.insert(END, f"Error processing {file_path}: {e}\n")
            else:
                self.console.insert(END, f"Unsupported file type: {file_path}\n")
        except Exception as e:
            self.console.insert(END, f"Error processing {file_path}: {e}\n")

    def process_directory(self, directory):
        files_to_process = []

        # Collect all files to process
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path.lower().endswith(('.jpg', '.jpeg', '.mp4', '.mov')):
                    files_to_process.append(file_path)

        # Set up the progress bar
        self.progress["maximum"] = len(files_to_process)
        self.progress["value"] = 0

        # Process each file and show progress
        for index, file_path in enumerate(tqdm(files_to_process, desc="Processing files", unit="file"), start=1):
            self.remove_metadata(file_path)
            self.progress["value"] = index
            self.update_progress_text(index, len(files_to_process))
            self.root.update_idletasks()

        # Show the completion message box
        self.show_completion_message()

    def update_progress_text(self, current, total):
        percentage = int((current / total) * 100)
        text = f"{percentage}% ({current}/{total})"

        # Clear the canvas and draw the progress text
        self.canvas.delete("all")
        self.canvas.create_text(250, 10, text=text, fill='white', font=('Arial', 10))

    def show_completion_message(self):
        result = messagebox.askokcancel("Processing Complete", "All files processed successfully. Do you want to exit?")

        if result:  # If user pressed OK
            self.root.quit()  # Quit the application

    def copy_log(self):
        # Copy all items from the Listbox to the clipboard
        log_content = "\n".join(self.console.get(0, END))
        self.root.clipboard_clear()
        self.root.clipboard_append(log_content)
        self.root.update()  # Make sure the clipboard content is updated


def main():
    root = Tk()
    app = MetadataRemoverApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
