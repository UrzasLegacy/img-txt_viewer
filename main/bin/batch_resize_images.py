"""

########################################
#                                      #
#          Batch Resize Images         #
#                                      #
#   Version : v1.06                    #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################

Description:
-------------
This GUI script allows you to resize all images in the selected directory.
Resize operations: Resize to* Resolution, Percentage, Width, Height, Shorter Side, Longer Side
Resize conditions: Upscale and Downscale, Upscale Only, Downscale Only

"""


################################################################################################################################################
#region -  Imports


import os
import sys
import ctypes
import argparse
import tkinter as tk
from tkinter import ttk, Toplevel, filedialog, messagebox, TclError
from tkinter.scrolledtext import ScrolledText
from PIL.PngImagePlugin import PngInfo
from PIL import Image

import subprocess


myappid = 'ImgTxtViewer.Nenotriple'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


#endregion
################################################################################################################################################
#region - CLASS: AboutWindow


class AboutWindow(Toplevel):
    info_dict = {
        "Info": "",

        "Supported Filetypes:":     "jpg, jpeg, png, webp, bmp, tif, tiff\n",

        "Resize to Resolution:":    "Resize to a specific width and height ignoring aspect ratio.\n\n(The following 'Resize to' options preserve aspect ratio)",
        "Resize to Percentage:":    "Resize the image by a percent scale.",
        "Resize to Width:":         "Target the image width and resize it.",
        "Resize to Height:":        "Target the image height and resize it.",
        "Resize to Shorter side:":  "Resize the shorter side of the image.",
        "Resize to Longer side:":   "Resize the longer side of the image.\n",

        "Quality:":                 "Used to control the output quality of JPG and WEBP images. A higher value results in a higher quality output. (Ignored for PNG)\n",

        "Upscale and Downscale:":   "Resize the image to the new dimensions regardless of whether they're larger or smaller than the original dimensions.",
        "Upscale Only:":            "Resize the image if the new dimensions are larger than the original dimensions.",
        "Downscale Only:":          "Resize the image if the new dimensions are smaller than the original dimensions.\n",

        "Filetype:":                "Select 'AUTO' to output with the same filetype as the input image. Alternatively, choose a specific filetype to force all images to be saved with the chosen type.\n",

        "Use Output Folder:":       "When enabled, a new folder will be created in the image directory called 'Resize Output' where images will be saved.",
        "Overwrite Files:":         "When disabled, conflicting files will have '_#' append to the filename. If enabled, files with the same basename will be overwritten.",
        "Save PNG Info:":           "When enabled, this option will automatically save any PNG chunk info to the resized output if saving as PNG. If converting from PNG to another type, then a text file will be created containing the PNG info."
    }


    def __init__(self, master=None):
        super().__init__(master=master)
        self.title("About")
        self.geometry("400x675")
        self.minsize(300, 100)
        self.create_info_text()
        self.create_other_widgets()


    def create_info_text(self):
        self.info_text = ScrolledText(self)
        self.info_text.pack(expand=True, fill='both')
        for first_header, (header, section) in enumerate(AboutWindow.info_dict.items()):
            if first_header == 0:
                self.info_text.insert("end", header + "\n", "first_header")
            else:
                self.info_text.insert("end", header + "\n", "header")
            self.info_text.insert("end", section + "\n", "section")
        self.info_text.tag_config("first_header", font=("Segoe UI Semibold", 18), justify='center')
        self.info_text.tag_config("header", font=("Segoe UI", 9, "bold"))
        self.info_text.tag_config("section", font=("Segoe UI", 9))
        self.info_text.config(state='disabled', wrap="word", height=1)


    def create_other_widgets(self):
        frame = tk.Frame(self)
        frame.pack(fill="x")

        self.made_by_label = tk.Label(frame, text=f"Created by: https://github.com/Nenotriple (2023-2024)", font=("Segoe UI", 10))
        self.made_by_label.pack(side="left", expand=True, pady=10)


#endregion
################################################################################################################################################
#region - CLASS: ResizeImages


class ResizeImages(tk.Frame):
    def __init__(self, master=None, folder_path=None):
        super().__init__(master)
        self.master = master
        self.pack(fill="both", expand=True)
        self.folder_path = folder_path

        self.about_window = None
        self.files_processed = 0

        self.supported_filetypes = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")

        self.setup_ui()


#endregion
################################################################################################################################################
#region -  Interface


    def setup_ui(self):
        self.frame_main = tk.Frame(self)
        self.frame_main.pack(fill="both")

        self.create_top_row()
        self.create_control_row()
        self.create_bottom_row()

        self.resize_mode_var.trace_add('write', self.update_entries)


    def create_top_row(self):
        self.frame_top_row = tk.Frame(self.frame_main)
        self.frame_top_row.pack(fill="both")

        self.entry_directory = tk.Entry(self.frame_top_row)
        self.entry_directory.insert(0, os.path.normpath(self.folder_path) if self.folder_path else "...")
        self.entry_directory.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        self.entry_directory.bind("<Return>", lambda event: self.select_folder(self.entry_directory.get()))
        self.entry_directory.bind("<Button-1>", lambda event: self.entry_directory.delete(0, "end") if self.entry_directory.get() == "..." else None)

        self.select_button = tk.Button(self.frame_top_row, width=8, overrelief="groove", text="Browse...", command=self.select_folder)
        self.select_button.pack(side="left", padx=2, pady=2)

        self.open_button = tk.Button(self.frame_top_row, width=8, overrelief="groove", text="Open", command=self.open_folder)
        self.open_button.pack(side="left", padx=2, pady=2)


    def create_control_row(self):
        self.frame_control_row = tk.Frame(self.frame_main, borderwidth=2, relief="groove")
        self.frame_control_row.pack(side="top", fill="x", padx=2, pady=2)


        ##### Checkbuttons
        self.frame_checkbuttons = tk.Frame(self.frame_control_row)
        self.frame_checkbuttons.pack(side="bottom", fill="x", padx=2, pady=2)

        separator = ttk.Separator(self.frame_checkbuttons, orient="horizontal")
        separator.pack(fill="x", padx=2, pady=2)

            # Use output folder
        self.use_output_folder_var = tk.IntVar(value=1)
        self.use_output_folder_checkbutton = tk.Checkbutton(self.frame_checkbuttons, overrelief="groove", text="Use Output Folder", variable=self.use_output_folder_var)
        self.use_output_folder_checkbutton.pack(side="left", fill="x", padx=2, pady=2)

            # Overwrite files
        self.overwrite_files_var = tk.IntVar(value=0)
        self.use_output_folder_checkbutton = tk.Checkbutton(self.frame_checkbuttons, overrelief="groove", text="Overwrite Output", variable=self.overwrite_files_var)
        self.use_output_folder_checkbutton.pack(side="left", fill="x", padx=2, pady=2)

            # Save Chunk Info
        self.save_png_info_var = tk.BooleanVar(value=False)
        self.save_png_info_checkbutton = tk.Checkbutton(self.frame_checkbuttons, overrelief="groove", text="Save PNG Info", variable=self.save_png_info_var)
        self.save_png_info_checkbutton.pack(side="left", fill="x", padx=2, pady=2)


        ##### Resize Settings
        self.frame_resize_settings = tk.Frame(self.frame_control_row)
        self.frame_resize_settings.pack(side="left", anchor="center", expand=True, padx=2, pady=2)

            # Resize Mode
        self.frame_resize_mode = tk.Frame(self.frame_resize_settings)
        self.frame_resize_mode.pack(side="top", anchor="w", padx=2, pady=2)

        self.resize_mode_label = tk.Label(self.frame_resize_mode, width=10, text="Resize To:")
        self.resize_mode_label.pack(side="left", padx=2, pady=2)

        self.resize_mode_var = tk.StringVar()
        self.resize_mode = ttk.Combobox(self.frame_resize_mode, width=21, textvariable=self.resize_mode_var, values=["Resolution", "Percentage", "Width", "Height", "Shorter Side", "Longer Side"], state="readonly")
        self.resize_mode.set("Resolution")
        self.resize_mode.pack(side="left", padx=2, pady=2)

            # Resize Condition
        self.frame_resize_condition = tk.Frame(self.frame_resize_settings)
        self.frame_resize_condition.pack(side="top", anchor="w", padx=2, pady=2)

        self.resize_condition_label = tk.Label(self.frame_resize_condition, width=10, text="Condition:")
        self.resize_condition_label.pack(side="left", padx=2, pady=2)

        self.resize_condition_var = tk.StringVar()
        self.resize_condition = ttk.Combobox(self.frame_resize_condition, width=21, textvariable=self.resize_condition_var, values=["Upscale and Downscale", "Upscale Only", "Downscale Only"], state="readonly")
        self.resize_condition.set("Upscale and Downscale")
        self.resize_condition.pack(side="left", padx=2, pady=2)

            # Filetype
        self.frame_filetype = tk.Frame(self.frame_resize_settings)
        self.frame_filetype.pack(side="top", anchor="w", padx=2, pady=2)

        self.filetype_label = tk.Label(self.frame_filetype, width=10, text="Filetype:")
        self.filetype_label.pack(side="left", padx=2, pady=2)

        self.filetype_var = tk.StringVar()
        self.filetype = ttk.Combobox(self.frame_filetype, width=6, textvariable=self.filetype_var, values=["AUTO", "JPEG", "PNG", "WEBP"], state="readonly")
        self.filetype.set("AUTO")
        self.filetype.pack(side="left", padx=2, pady=2)
        self.filetype_var.trace_add("write", self.update_quality_widgets)


        ##### Sizes
        self.frame_sizes = tk.Frame(self.frame_control_row)
        self.frame_sizes.pack(side="left", anchor="center", expand=True, padx=2, pady=2)

            # Width Frame
        self.width_frame = tk.Frame(self.frame_sizes)
        self.width_frame.pack()
        self.width_label = tk.Label(self.width_frame, text="Width:", width=5)
        self.width_label.pack(side="left", padx=2, pady=2)
        self.width_entry = tk.Entry(self.width_frame, width=20)
        self.width_entry.pack(side="left", padx=2, pady=2)

            # Height Frame
        self.height_frame = tk.Frame(self.frame_sizes)
        self.height_frame.pack()
        self.height_label = tk.Label(self.height_frame, text="Height:", width=5)
        self.height_label.pack(side="left", padx=2, pady=2)
        self.height_entry = tk.Entry(self.height_frame, width=20)
        self.height_entry.pack(side="left", padx=2, pady=2)

            # Quality Frame
        self.frame_quality = tk.Frame(self.frame_sizes)
        self.frame_quality.pack(fill="x")
        self.quality_label = tk.Label(self.frame_quality, text="Quality:", width=5)
        self.quality_label.pack(side="left", padx=2, pady=2)
        self.quality_var = tk.IntVar(value=100)
        self.original_quality = self.quality_var.get()
        self.quality_scale = tk.Scale(self.frame_quality, length=1, showvalue=False, variable=self.quality_var, orient="horizontal", from_=20, to=100)
        self.quality_scale.pack(side="left", fill="x", expand=True)
        self.quality_value_label = tk.Label(self.frame_quality, textvariable=self.quality_var, width=3)
        self.quality_value_label.pack(side="left", padx=2, pady=2)


    def create_bottom_row(self):
        self.frame_bottom_row = tk.Frame(self.frame_main)
        self.frame_bottom_row.pack(side="bottom", fill="both", expand=True)


        ##### Buttons
        self.frame_buttons = tk.Frame(self.frame_bottom_row)
        self.frame_buttons.pack(fill="x")

            # Resize Button
        self.button_resize = tk.Button(self.frame_buttons, overrelief="groove", text="Resize!", command=self.resize)
        self.button_resize.pack(side="left", fill="x", expand=True, padx=2, pady=2)

            # Cancel Button
        self.button_cancel = tk.Button(self.frame_buttons, overrelief="groove", width=8, state="disabled", text="Cancel", command=lambda: setattr(self, 'stop', True))
        self.button_cancel.pack(side="left", fill="x", padx=2, pady=2)


        # Percent Bar
        self.percent_complete = tk.StringVar()
        self.percent_bar = ttk.Progressbar(self.frame_bottom_row, value=0)
        self.percent_bar.pack(fill="x", padx=2, pady=2)


        #### Message row
        self.frame_message_row = tk.Frame(self.frame_bottom_row)
        self.frame_message_row.pack(side="top", fill="x")

            # Message
        self.label_message = tk.Label(self.frame_message_row, text="Select a directory...")
        if self.folder_path:
            self.update_message_text(filecount=True)
        self.label_message.pack(side="left", padx=2)

            # Help
        self.button_help = tk.Button(self.frame_message_row, text="?", width=2, relief="groove", overrelief="raised", command=self.toggle_about_window)
        self.button_help.pack(side="right", padx=2, pady=2)


#endregion
################################################################################################################################################
#region -  Misc


    def update_quality_widgets(self, *args):
        if self.filetype_var.get() == "PNG":
            self.original_quality = self.quality_var.get()
            self.quality_scale.config(state="disabled")
            self.quality_label.config(state="disabled")
            self.quality_value_label.config(state="disabled")
            self.quality_var.set(100)
        else:
            self.quality_scale.config(state="normal")
            self.quality_label.config(state="normal")
            self.quality_value_label.config(state="normal")
            self.quality_var.set(self.original_quality)


    def update_entries(self, *args):
        mode = self.resize_mode_var.get()
        if mode == "Resolution":
            self.width_entry.config(state="normal")
            self.width_label.config(state="normal")
            self.height_entry.config(state="normal")
            self.height_label.config(state="normal")
            self.resize_condition_label.config(state="normal")
            self.resize_condition.config(state="readonly")
            self.width_label.config(text="Width:")
            self.height_label.config(text="Height:")

        elif mode == "Percentage":
            self.width_entry.config(state="normal")
            self.width_label.config(state="normal")
            self.height_entry.delete(0, 'end')
            self.height_entry.config(state="disabled")
            self.height_label.config(state="disabled")
            self.resize_condition_label.config(state="normal")
            self.resize_condition.config(state="disabled")
            self.width_label.config(text="%")
            self.height_label.config(text="-")

        elif mode in ["Width", "Shorter Side", "Longer Side"]:
            self.width_entry.config(state="normal")
            self.width_label.config(state="normal")
            self.height_entry.delete(0, 'end')
            self.height_entry.config(state="disabled")
            self.height_label.config(state="disabled")
            self.resize_condition_label.config(state="normal")
            self.resize_condition.config(state="readonly")
            if mode == "Width":
                self.width_label.config(text="Width:")
            else:
                self.width_label.config(text="Size")
            self.height_label.config(text="-")

        elif mode in ["Height"]:
            self.width_entry.delete(0, 'end')
            self.width_entry.config(state="disabled")
            self.width_label.config(state="disabled")
            self.height_entry.config(state="normal")
            self.height_label.config(state="normal")
            self.resize_condition_label.config(state="normal")
            self.resize_condition.config(state="readonly")
            self.width_label.config(text="-")
            self.height_label.config(text="Height:")


    def update_message_text(self, filecount=None, text=None):
        if filecount:
            count = sum(1 for file in os.listdir(self.folder_path) if file.endswith(self.supported_filetypes))
            self.label_message.config(text=f"{count} {'Image' if count == 1 else 'Images'} Found")
        if text:
            self.label_message.config(text=text)


    def select_folder(self, path=None):
        try:
            if path:
                new_folder_path = path
            else:
                new_folder_path = filedialog.askdirectory()
            if new_folder_path:
                self.folder_path = new_folder_path
                self.entry_directory.delete(0, "end")
                self.entry_directory.insert(0, new_folder_path)
                self.update_message_text(filecount=True)
                self.button_resize.config(state="normal")
        except FileNotFoundError:
            self.update_message_text(text="The system cannot find the path specified.")


    def open_folder(self):
        try:
            os.startfile(self.folder_path)
        except FileNotFoundError:
            self.update_message_text(text="The system cannot find the path specified.")


    def get_output_folder_path(self):
        if self.use_output_folder_var.get() == 1:
            output_folder_path = os.path.join(self.folder_path, "Resize Output")
            if not os.path.exists(output_folder_path):
                os.makedirs(output_folder_path)
        else:
            output_folder_path = self.folder_path
        return output_folder_path


#endregion
################################################################################################################################################
#region -  Resize


    def resize_to_resolution(self, img, width, height):
        if width is None or height is None:
            messagebox.showinfo("Error", "Please enter a valid width and height.")
            return
        if not isinstance(width, int) or not isinstance(height, int):
            raise TypeError("Width and height must be integers.")
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be greater than 0.")
        img = img.resize((width, height), Image.LANCZOS)
        return img


    def resize_to_percentage(self, img, percentage):
        if percentage is None:
            messagebox.showinfo("Error", "Please enter a valid percentage")
            return
        if not isinstance(percentage, (int, float)):
            raise TypeError("Percentage must be a number.")
        if percentage <= 0:
            raise ValueError("Percentage must be greater than 0.")
        width = int(img.size[0] * percentage)
        height = int(img.size[1] * percentage)
        img = img.resize((width, height), Image.LANCZOS)
        return img


    def resize_to_width(self, img, width):
        if width is None:
            messagebox.showinfo("Error", "Please enter a valid width")
            return
        if not isinstance(width, int):
            raise TypeError("Width must be an integer.")
        if width <= 0:
            raise ValueError("Width must be greater than 0.")
        wpercent = (width/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((width, hsize), Image.LANCZOS)
        return img


    def resize_to_height(self, img, height):
        if height is None:
            messagebox.showinfo("Error", "Please enter a valid height")
            return
        if not isinstance(height, int):
            raise TypeError("Height must be an integer.")
        if height <= 0:
            raise ValueError("Height must be greater than 0.")
        hpercent = (height/float(img.size[1]))
        wsize = int((float(img.size[0])*float(hpercent)))
        img = img.resize((wsize, height), Image.LANCZOS)
        return img


    def resize_to_shorter_side(self, img, width):
        if width is None:
            messagebox.showinfo("Error", "Please enter a valid size")
            return
        if not isinstance(width, int):
            raise TypeError("Size must be an integer.")
        if width <= 0:
            raise ValueError("Size must be greater than 0.")
        if img.size[0] < img.size[1]:
            wpercent = (width/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((width, hsize), Image.LANCZOS)
        else:
            hpercent = (width/float(img.size[1]))
            wsize = int((float(img.size[0])*float(hpercent)))
            img = img.resize((wsize, width), Image.LANCZOS)
        return img


    def resize_to_longer_side(self, img, width):
        if width is None:
            messagebox.showinfo("Error", "Please enter a valid size")
            return
        if not isinstance(width, int):
            raise TypeError("Size must be an integer.")
        if width <= 0:
            raise ValueError("Size must be greater than 0.")
        if img.size[0] > img.size[1]:
            wpercent = (width/float(img.size[0]))
            hsize = int((float(img.size[1])*float(wpercent)))
            img = img.resize((width, hsize), Image.LANCZOS)
        else:
            hpercent = (width/float(img.size[1]))
            wsize = int((float(img.size[0])*float(hpercent)))
            img = img.resize((wsize, width), Image.LANCZOS)
        return img


    def should_resize(self, original_size, new_size):
        if original_size == new_size:
            return False
        resize_condition = self.resize_condition_var.get()
        if resize_condition == "Upscale Only":
            return new_size > original_size
        elif resize_condition == "Downscale Only":
            return new_size < original_size
        elif resize_condition == "Percentage":
            return True
        else:  # "Upscale and Downscale"
            return True


    def calculate_resize_mode(self, img, resize_mode, width, height):
        original_size = img.size
        if resize_mode == "Resolution":
            new_size = (width, height)
            if self.should_resize(original_size, new_size):
                img = self.resize_to_resolution(img, width, height)
        elif resize_mode == "Percentage":
            percentage = width / 100
            new_size = (int(original_size[0] * percentage), int(original_size[1] * percentage))
            if self.should_resize(original_size, new_size):
                img = self.resize_to_percentage(img, percentage)
        elif resize_mode == "Width":
            new_size = (width, original_size[1])
            if self.should_resize(original_size, new_size):
                img = self.resize_to_width(img, width)
        elif resize_mode == "Height":
            new_size = (original_size[0], height)
            if self.should_resize(original_size, new_size):
                img = self.resize_to_height(img, height)
        elif resize_mode == "Shorter Side":
            new_size = (width, width)
            if self.should_resize(original_size, new_size):
                img = self.resize_to_shorter_side(img, width)
        elif resize_mode == "Longer Side":
            new_size = (height, height)
            if self.should_resize(original_size, new_size):
                img = self.resize_to_longer_side(img, height)
        return img


    def get_resize_confirmation(self, output_folder_path):
        output_folder_message = f"Images will be saved to:\n{os.path.normpath(output_folder_path)}"
        default_message = "Are you sure you want to continue?"
        confirm_message = output_folder_message if self.use_output_folder_var.get() == 1 else default_message
        return confirm_message


    def get_entry_values(self):
        resize_mode = self.resize_mode_var.get()
        width_entry = self.width_entry.get()
        height_entry = self.height_entry.get()
        width = int(width_entry) if width_entry else None
        height = int(height_entry) if height_entry else None
        if (resize_mode == "Resolution" and (width is None or height is None)) or \
           (resize_mode in ["Percentage", "Width", "Height", "Shorter Side", "Longer Side"] and width is None):
            return
        return resize_mode, width, height


    def resize(self):
        self.percent_complete.set(0)
        self.stop = False
        self.files_processed = 0
        if self.folder_path is not None:
            if not self.stop:
                self.button_cancel.config(state="normal")
                self.button_resize.config(state="disabled")
            try:
                resize_mode, width, height = self.get_entry_values()
                image_files = [file for file in os.listdir(self.folder_path) if file.endswith(self.supported_filetypes)]
                total_images = len(image_files)
                output_folder_path = self.get_output_folder_path()
                confirm_message = self.get_resize_confirmation(output_folder_path)
                if messagebox.askokcancel("Confirmation", confirm_message):
                    self.master.focus_force()
                    for image_index, filename in enumerate(image_files):
                        if self.stop:
                            self.button_cancel.config(state="disabled")
                            break
                        try:
                            img = Image.open(os.path.join(self.folder_path, filename))
                            if img is None:
                                return
                            img = img.convert('RGB')
                            img = self.calculate_resize_mode(img, resize_mode, width, height)
                            if img is None:
                                return
                            dest_image_path = self.save_image(img, output_folder_path, filename, total_images)
                            src_image_path = os.path.join(self.folder_path, filename)
                            self.handle_metadata(filename, src_image_path, dest_image_path)
                            self.percent_complete.set((image_index + 1) / total_images * 100)
                            self.percent_bar['value'] = self.percent_complete.get()
                            self.percent_bar.update()
                        except Exception as e:
                            print(f"Error processing file {filename}: {str(e)}")
                    if not self.stop:
                        messagebox.showinfo("Done!", "Resizing finished.")
                        self.master.focus_force()
            except Exception as e:
                print(f"Error in resize function: {str(e)}")
            finally:
                self.button_resize.config(state="normal")


    def save_image(self, img, output_folder_path, filename, total_images):
        if 'icc_profile' in img.info:
            del img.info['icc_profile']
        filetype = self.filetype_var.get().lower()
        base_filename, original_extension = os.path.splitext(filename)
        if filetype == "auto":
            filetype = original_extension[1:]
        filename_with_new_extension = f"{base_filename}.{filetype}"
        counter = 1
        self.files_processed += 1
        if not self.overwrite_files_var.get():
            while os.path.exists(os.path.join(output_folder_path, filename_with_new_extension)):
                filename_with_new_extension = f"{base_filename}_{counter}.{filetype}"
                counter += 1
        img.save(os.path.join(output_folder_path, filename_with_new_extension), quality=self.quality_var.get(), optimize=True)
        self.update_message_text(text=f"Processed: {self.files_processed} of {total_images} images")
        if self.files_processed >= total_images:
            self.files_processed = 0
            self.update_message_text(text="Done!")
        return os.path.join(output_folder_path, filename_with_new_extension)


#endregion
################################################################################################################################################
#region -  Handle Metadata


    def handle_metadata(self, filename, src_image_path, output_image_path):
        if self.save_png_info_var.get():
            if filename.lower().endswith(".png"):
                if output_image_path.lower().endswith(".webp"):
                    self.copy_png_to_webp(src_image_path, output_image_path)
                else:
                    self.copy_png_metadata(src_image_path, output_image_path)
            if filename.lower().endswith(".webp"):
                self.copy_webp_metadata(src_image_path, output_image_path)


    # PNG
    def read_png_metadata(self, src_image_path):
        src_image = Image.open(src_image_path)
        metadata = src_image.info
        metadata_text = ""
        pnginfo = PngInfo()
        for key in metadata:
            if isinstance(metadata[key], bytes):
                value = metadata[key].decode('utf-8')
                pnginfo.add_text(key, value, 0)
            else:
                value = str(metadata[key])
                pnginfo.add_text(key, value, 0)
            metadata_text += f"{key}: {value}\n"
        return pnginfo, metadata_text


    def write_png_metadata(self, pnginfo, metadata_text, dest_image_path):
        dest_image = Image.open(dest_image_path)
        dest_image.save(dest_image_path, pnginfo=pnginfo)
        base_filename = os.path.basename(dest_image_path)
        dir_path = os.path.dirname(dest_image_path)
        if not base_filename.endswith('.png'):
            with open(os.path.join(dir_path, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(metadata_text)


    def copy_png_metadata(self, src_image_path, dest_image_path):
        pnginfo, metadata_text = self.read_png_metadata(src_image_path)
        self.write_png_metadata(pnginfo, metadata_text, dest_image_path)


    def copy_png_to_webp(self, src_image_path, dest_image_path):
        exiftool_path = "exiftool.exe"
        if os.path.exists(exiftool_path):
            src_image = Image.open(src_image_path)
            metadata = src_image.info
            metadata_str = ', '.join(f'{key}: {value}' for key, value in metadata.items())
            subprocess.run([exiftool_path, '-overwrite_original', f'-UserComment={metadata_str}', dest_image_path], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            self.stop = True
            messagebox.showerror("Error!",
                                    "Could not copy metadata from PNG-to-WEBP."
                                    "\n\nexiftool.exe does not exist in the root path. (Check spelling)"
                                    "\n\nDownload the Windows executable from exiftool.org and place in the same folder as batch_resize_images.exe, restart the program and try again."
                                    "\n\nThe resize operation will now stop.")


    # WEBP
    def read_webp_metadata(self, src_image_path):
        process = subprocess.run(["exiftool.exe", '-UserComment', '-b', src_image_path], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        user_comment = process.stdout.strip()
        print(user_comment)
        return user_comment


    def write_webp_metadata(self, user_comment, dest_image_path):
        base_filename = os.path.basename(dest_image_path)
        subprocess.run(["exiftool.exe", '-overwrite_original', f'-UserComment={user_comment}', dest_image_path], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if not base_filename.endswith('.webp'):
            with open(f"{base_filename}.txt", "w", encoding="utf-8") as f:
                f.write(user_comment)


    def copy_webp_metadata(self, src_image_path, dest_image_path):
        if os.path.exists("exiftool.exe"):
            user_comment = self.read_webp_metadata(src_image_path)
            self.write_webp_metadata(user_comment, dest_image_path)
        else:
            self.stop = True
            messagebox.showerror("Error!",
                                    "Could not copy metadata from WEBP-to-WEBP."
                                    "\n\nexiftool.exe does not exist in the root path. (Check spelling)"
                                    "\n\nDownload the Windows executable from exiftool.org and place in the same folder as batch_resize_images.exe, restart the program and try again."
                                    "\n\nThe resize operation will now stop.")



#endregion
################################################################################################################################################
#region -  Handle About Window


    def toggle_about_window(self):
        if self.about_window is not None:
            self.close_about_window()
        else:
            self.open_about_window()


    def open_about_window(self):
        self.about_window = AboutWindow(self.master)
        self.about_window.protocol("WM_DELETE_WINDOW", self.close_about_window)
        main_window_width = root.winfo_width()
        main_window_x = root.winfo_x() - 200 + main_window_width // 2
        main_window_y = root.winfo_y() + 30
        self.about_window.geometry("+{}+{}".format(main_window_x, main_window_y))


    def close_about_window(self):
        self.about_window.destroy()
        self.about_window = None


#endregion
################################################################################################################################################
#region -  Framework


def check_path():
    parser = argparse.ArgumentParser(description='Resize Images Resize_Image')
    parser.add_argument('--path', type=str, help='Path to the folder')
    args = parser.parse_args()
    if args.path and os.path.exists(args.path):
        path = args.path
    else:
        path = None
    return path


def setup_root():
    root = tk.Tk()
    root.title("v1.06 - Batch Resize Images --- github.com/Nenotriple")
    root.geometry("480x250")
    root.resizable(False, False)
    root.update_idletasks()
    set_icon(root)
    return root


def set_icon(root):
    if getattr(sys, 'frozen', False):
        application_path = sys._MEIPASS
    elif __file__:
        application_path = os.path.dirname(__file__)
    icon_path = os.path.join(application_path, "icon.ico")
    try:
        root.iconbitmap(icon_path)
    except TclError:
        pass


def center_window(root):
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    root = setup_root()
    path = check_path()
    center_window(root)
    ResizeImages(root, path)
    root.mainloop()


#endregion
################################################################################################################################################
#region - Changelog


'''

[v1.06 changes:](https://github.com/Nenotriple/batch_resize_images/releases/tag/v1.06)

  - New:
      - Metadata can now be copied between PNG and WEBP images.
        - Copying metadata from PNG-to-WEBP and WEBP-to-PNG requires `ExifTool.exe` to be in the same folder as `batch_resize_images.exe`.
        - ExifTool (2003-2024) is created by Phil Harvey and can be downloaded from https://exiftool.org/

<br>

  - Fixed:
    -

<br>

  - Other changes:
    - Clicking on the directory entry when it's displaying the default `...` will now clear the entry.
    - Minor UI tweaks.


'''

#endregion
################################################################################################################################################
#region - Todo


'''

- Todo
  -

- Tofix
  -

'''

#endregion
