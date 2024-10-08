"""
########################################
#                                      #
#             Upscale Image            #
#                                      #
#   Version : v1.04                    #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################

Description:
-------------
Upscale a single/batch image using realesrgan-ncnn-vulkan.exe

"""

################################################################################################################################################
#region -  Imports


import os
import time
import shutil
import subprocess
from tkinter import ttk, Toplevel, messagebox, Frame, Entry, Label, Button, IntVar, DoubleVar, StringVar, TclError
from tkinter.filedialog import askdirectory
from PIL import Image, ImageSequence


#endregion
################################################################################################################################################
#region - CLASS: Upscale


class Upscale:
    def __init__(self, master, ImgTxtViewer, ToolTip, filepath, window_x, window_y, batch, update_pair, jump_to_image):
        self.top = Toplevel(master, borderwidth=2, relief="groove")
        self.top.overrideredirect("true")
        self.top.geometry("+{}+{}".format(window_x, window_y))
        self.top.grab_set()
        self.top.focus_force()
        self.top.bind("<Escape>", self.close_window)
        self.top.bind("<Return>", self.determine_image_type)

        self.batch_mode = batch
        self.batch_filepath = os.path.dirname(filepath)

        self.supported_filetypes = (".png", ".webp", ".jpg", ".jpeg", ".jpg_large", ".jfif", ".tif", ".tiff", ".bmp", ".gif")

        self.ImgTxtViewer = ImgTxtViewer
        self.sort_key = self.ImgTxtViewer.get_file_sort_key()
        self.ImgTxt_update_pair = update_pair
        self.ImgTxt_jump_to_image = jump_to_image

        self.ToolTip = ToolTip

        self.process = None
        self.start_x = None
        self.start_y = None

        self.original_filepath = filepath
        self.converted_filepath = None

        self.total_gif_frames = None
        self.current_gif_frame = None

        self.is_window_closed = False


        self.get_image_info()
        self.create_interface()
        self.update_size_info_label()


#endregion
################################################################################################################################################
#region -  Setup Interface


    def create_interface(self):

        self.frame_container = Frame(self.top)
        self.frame_container.pack(expand=True, fill="both")

        title_text = "Upscale Image" if not self.batch_mode else "Batch Upscale"
        title = Label(self.frame_container, cursor="size", text=title_text, font=("", 16))
        title.pack(side="top", fill="x", padx=5, pady=5)
        title.bind("<ButtonPress-1>", self.start_drag)
        title.bind("<ButtonRelease-1>", self.stop_drag)
        title.bind("<B1-Motion>", self.dragging_window)


        self.button_close = Button(self.frame_container, text="X", overrelief="groove", relief="flat", command=self.close_window)
        button_close_padding = 0.945 if self.batch_mode else 0.92
        self.button_close.place(anchor="nw", relx=button_close_padding, height=40, width=40, x=-15, y=0)
        self.bind_widget_highlight(self.button_close, color='#ffcac9')


        separator = ttk.Separator(self.frame_container)
        separator.pack(side="top", fill="x")


####### Options ##################################################
        frame_comboboxes = Frame(self.frame_container)
        frame_comboboxes.pack(side="top", fill="x", padx=10, pady=10)

        if self.batch_mode:
            frame_input_batch_directory = Frame(frame_comboboxes)
            frame_input_batch_directory.pack(side="top", fill="x", padx=10, pady=10)

            # Input
            self.label_batch_upscale_path = Label(frame_input_batch_directory, text="Upscale Path")
            self.label_batch_upscale_path.pack(anchor="w", side="top", padx=5, pady=5)
            self.batch_upscale_path = StringVar(value=self.batch_filepath)
            self.entry_batch_upscale_path = Entry(frame_input_batch_directory, width=50, textvariable=self.batch_upscale_path)
            self.entry_batch_upscale_path.pack(side="left", fill="x", padx=5, pady=5)
            self.ToolTip.create(self.entry_batch_upscale_path, f"The input path\n\n{self.batch_filepath}", 250, 6, 12)

            self.button_browse_batch_input = Button(frame_input_batch_directory, overrelief="groove", text="Browse...", command=lambda: self.choose_directory(self.batch_upscale_path))
            self.button_browse_batch_input.pack(side="left", fill="x", padx=2, pady=2)

            self.button_open_batch_input = Button(frame_input_batch_directory, overrelief="groove", text="Open", command=lambda: self.open_directory(self.batch_upscale_path.get()))
            self.button_open_batch_input.pack(side="left", fill="x", padx=2, pady=2)

            frame_output_batch_directory = Frame(frame_comboboxes)
            frame_output_batch_directory.pack(side="top", fill="x", padx=10, pady=10)

            # Output
            self.label_batch_output_path = Label(frame_output_batch_directory, text="Output Path")
            self.label_batch_output_path.pack(anchor="w", side="top", padx=5, pady=5)

            self.batch_output_path = StringVar(value=os.path.join(self.batch_upscale_path.get(), "Output"))

            self.entry_batch_output_path = Entry(frame_output_batch_directory, width=50, textvariable=self.batch_output_path)
            self.entry_batch_output_path.pack(side="left", fill="x", padx=5, pady=5)
            self.ToolTip.create(self.entry_batch_output_path, "The output path", 250, 6, 12)

            self.browse_batch_output_button = Button(frame_output_batch_directory, overrelief="groove", text="Browse...", command=lambda: self.choose_directory(self.batch_output_path))
            self.browse_batch_output_button.pack(side="left", fill="x", padx=2, pady=2)

            self.open_batch_output_button = Button(frame_output_batch_directory, overrelief="groove", text="Open", command=lambda: self.open_directory(self.batch_output_path.get()))
            self.open_batch_output_button.pack(side="left", fill="x", padx=2, pady=2)


        frame_model = Frame(frame_comboboxes)
        frame_model.pack(side="top", fill="x", padx=10, pady=10)

        self.label_upscale_model = Label(frame_model, text="Upscale Model")
        self.label_upscale_model.pack(anchor="w", side="top", padx=5, pady=5)
        self.combobox_upscale_model = ttk.Combobox(frame_model, width=25, state="readonly", values=["realesr-animevideov3-x4", "RealESRGAN_General_x4_v3", "realesrgan-x4plus", "realesrgan-x4plus-anime"])
        self.combobox_upscale_model.pack(side="top", fill="x", padx=5, pady=5)
        self.ToolTip.create(self.combobox_upscale_model, "Select the RESRGAN upscale model", 250, 6, 12)
        self.combobox_upscale_model.set("realesr-animevideov3-x4")


        frame_size = Frame(frame_comboboxes)
        frame_size.pack(side="top", fill="x", padx=10, pady=10)

        self.label_size = Label(frame_size, text="Upscale Factor")
        self.label_size.pack(anchor="w", side="top", padx=5, pady=5)
        self.upscale_factor_value = DoubleVar(value=2.00)
        self.slider_upscale_factor = ttk.Scale(frame_size, from_=0.25, to=8.00, orient="horizontal", variable=self.upscale_factor_value, command=self.update_upscale_factor_label)
        self.slider_upscale_factor.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.ToolTip.create(self.slider_upscale_factor, "Determines the final size of the image.\n\nImages are first upscaled by 4x and then resized according to the selected upscale factor.\n\nThe final resolution is calculated as: (4 * original size) / upscale factor.", 250, 6, 12)
        self.label_upscale_factor_value = Label(frame_size, textvariable=self.upscale_factor_value, width=5)
        self.label_upscale_factor_value.pack(side="left", anchor="w", padx=5, pady=5)


        frame_slider = Frame(frame_comboboxes)
        frame_slider.pack(side="top", fill="x", padx=10, pady=10)

        self.label_upscale_strength = Label(frame_slider, text="Upscale Strength")
        self.label_upscale_strength.pack(anchor="w", side="top", padx=5, pady=5)
        self.upscale_strength_value = IntVar(value=100)
        self.slider_upscale_strength = ttk.Scale(frame_slider, from_=0, to=100, orient="horizontal", command=self.update_strength_label)
        self.slider_upscale_strength.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.ToolTip.create(self.slider_upscale_strength, "Adjust the upscale strength to determine the final blending value of the output image.\n\n0% = Only original image, 100% = Only upscaled image.", 250, 6, 12)
        self.label_upscale_strength_percent = Label(frame_slider, width=5)
        self.label_upscale_strength_percent.pack(anchor="w", side="left", padx=5, pady=5)
        self.slider_upscale_strength.set(100)


####### Info ##################################################

        if not self.batch_mode:
            self.frame_info = Frame(self.top)
            self.frame_info.pack(side="top", expand=True, fill="x", padx=10, pady=10)


            separator = ttk.Separator(self.frame_info)
            separator.pack(side="top", fill="x")


            self.frame_labels = Frame(self.frame_info)
            self.frame_labels.pack(side="left", expand=True, fill="x", padx=10, pady=10)

            label_current = Label(self.frame_labels, text="Current Size:")
            label_current.pack(anchor="w", side="top", padx=5, pady=5)
            label_new = Label(self.frame_labels, text="New Size:")
            label_new.pack(anchor="w", side="top", padx=5, pady=5)
            if self.original_filepath.lower().endswith(".gif"):
                label_frames = Label(self.frame_labels, text="Frames:")
                label_frames.pack(anchor="w", side="top", padx=5, pady=5)


            self.frame_dimensions = Frame(self.frame_info)
            self.frame_dimensions.pack(side="left", expand=True, fill="x", padx=10, pady=10)

            self.label_current_dimensions = Label(self.frame_dimensions, text=f"{self.original_image_width} x {self.original_image_height}", width=20)
            self.label_current_dimensions.pack(anchor="w", side="top", padx=5, pady=5)
            self.label_new_dimensions = Label(self.frame_dimensions, text="0 x 0", width=20)
            self.label_new_dimensions.pack(anchor="w", side="top", padx=5, pady=5)
            self.ToolTip.create(self.label_new_dimensions, " The final size of the image after upscaling ", 250, 6, 12)
            if self.original_filepath.lower().endswith(".gif"):
                self.label_framecount = Label(self.frame_dimensions, text=f"{self.current_gif_frame} of {self.total_gif_frames}", width=20)
                self.label_framecount.pack(anchor="w", side="top", padx=5, pady=5)


####### Primary Buttons ##################################################
        self.frame_primary_buttons = Frame(self.top)
        self.frame_primary_buttons.pack(side="top", fill="x")


        self.progress_bar = ttk.Progressbar(self.frame_primary_buttons, maximum=100)
        self.progress_bar.pack(side="top", expand=True, fill="x", padx=10, pady=10)


        #button_command = self.determine_image_type if not self.batch_mode else self.batch_upscale
        button_command = self.determine_image_type
        self.button_upscale = Button(self.frame_primary_buttons, overrelief="groove", text="Upscale", command=button_command)
        self.button_upscale.pack(side="left", expand=True, fill="x", padx=5, pady=5)


        self.button_cancel = Button(self.frame_primary_buttons, overrelief="groove", text="Cancel", command=self.close_window)
        self.button_cancel.pack(side="left", expand=True, fill="x", padx=5, pady=5)

#endregion
################################################################################################################################################
#region -  Primary Functions


    def determine_image_type(self, event=None):
        if self.batch_mode:
            self.batch_upscale()
        else:
            directory, filename = os.path.split(self.original_filepath)
            filename, extension = os.path.splitext(filename)
            gif_path = self.original_filepath
            self.set_widget_state(state="disabled")
            if extension.lower() == '.gif':
                self._upscale_gif(gif_path)
            else:
                self.upscale_image()


    def batch_upscale(self):
        input_path = self.batch_upscale_path.get()
        output_path = self.batch_output_path.get()
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        count = 0
        for filename in os.listdir(input_path):
            file_path = os.path.join(input_path, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(self.supported_filetypes):
                self.original_filepath = file_path
                if filename.lower().endswith('.gif'):
                    print(f"Upscaling GIF: {file_path}")
                    self._upscale_gif(file_path, batch_mode=True, output_path=output_path)
                else:
                    print(f"Upscaling Image: {file_path}")
                    self.upscale_image(batch_mode=True, output_path=output_path)
                count += 1
        self.update_progress(100)
        messagebox.showinfo("Success", f"Successfully upscaled {count} images!")
        self.close_window()


    def _upscale_gif(self, gif_path, batch_mode=None, output_path=None):
        try:
            self.button_upscale.config(state="disabled")
            with Image.open(gif_path) as gif:
                frames = [(frame.copy().convert("RGBA"), frame.info['duration']) for frame in ImageSequence.Iterator(gif)]
            temp_dir = os.path.join(os.path.dirname(gif_path), "temp_upscale_img")
            os.makedirs(temp_dir, exist_ok=True)
            upscaled_frames = []
            total_frames = len(frames)
            model = str(self.combobox_upscale_model.get())
            for i, (frame, duration) in enumerate(frames):
                if self.is_window_closed:
                    return
                temp_frame_path = os.path.join(temp_dir, f"frame_{i}.png")
                frame.save(temp_frame_path)
                upscaled_frame_path = os.path.join(temp_dir, f"frame_{i}_upscaled.png")
                print(f"Upscaling frame {i+1}/{total_frames}")
                subprocess.run(["main/bin/resrgan/realesrgan-ncnn-vulkan.exe",
                                "-i", temp_frame_path,
                                "-o", upscaled_frame_path,
                                "-n", model,
                                "-s", "4",
                                "-f", "jpg"],
                                creationflags=subprocess.CREATE_NO_WINDOW)
                self.resize_image(upscaled_frame_path)
                if os.path.exists(upscaled_frame_path):
                    if self.upscale_strength_value.get() != 100:
                        self.blend_images(temp_frame_path, upscaled_frame_path, '.png')
                    with Image.open(upscaled_frame_path) as upscaled_frame:
                        upscaled_frame = upscaled_frame.convert("RGBA")
                        upscaled_frames.append((upscaled_frame, duration))
                self.update_progress((i+1)/total_frames*90)
                if not batch_mode:
                    padded_frame_number = str(i+1).zfill(len(str(total_frames)))
                    self.label_framecount.config(text=f"{padded_frame_number} of {total_frames}")
            directory, filename = os.path.split(gif_path)
            filename, extension = os.path.splitext(filename)
            upscaled_gif_path = os.path.join(output_path if batch_mode else directory, f"{filename}_upscaled{extension}")
            upscaled_frames[0][0].save(upscaled_gif_path, save_all=True, append_images=[frame for frame, _ in upscaled_frames[1:]], loop=0, duration=[duration for _, duration in upscaled_frames])
            shutil.rmtree(temp_dir)
            self.update_progress(99)
            if not batch_mode:
                time.sleep(0.1)
                self.close_window(self.get_image_index(directory, f"{filename}_upscaled{extension}"))
                result = messagebox.askyesno("Upscale Successful", f"Output path:\n{upscaled_gif_path}\n\nOpen image?")
                if result:
                    os.startfile(upscaled_gif_path)
        except (PermissionError, FileNotFoundError, TclError) as e:
            print(f"Error: {e}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred.\n\n{e}")
            self.close_window()

    def upscale_image(self, batch_mode=False, output_path=None):
        try:
            self.button_upscale.config(state="disabled")
            self.update_progress(25)
            directory, filename = os.path.split(self.original_filepath)
            filename, extension = os.path.splitext(filename)
            if extension.lower() == '.webp':
                extension = self.convert_webp_to_jpg(directory, filename)
            output_image_path = os.path.join(output_path if batch_mode else directory, f"{filename}{extension}" if batch_mode else f"{filename}_up{extension}")
            model = str(self.combobox_upscale_model.get())
            upscale_process = subprocess.Popen(["main/bin/resrgan/realesrgan-ncnn-vulkan.exe",
                              "-i", self.original_filepath,
                              "-o", output_image_path,
                              "-n", model,
                              "-s", "4",
                              "-f", "jpg"],
                              creationflags=subprocess.CREATE_NO_WINDOW)
            self.update_progress(40)
            upscale_process.wait()
            self.update_progress(60)
            self.resize_image(output_image_path)
            self.update_progress(80)
            self.delete_converted_image()
            if self.upscale_strength_value.get() != 100:
                self.blend_images(self.original_filepath, output_image_path, extension)
            self.update_progress(99)
            if not batch_mode:
                time.sleep(0.1)
                index = self.get_image_index(directory, output_image_path)
                self.close_window(index)
                result = messagebox.askyesno("Upscale Successful", f"Output path:\n{output_image_path}\n\nOpen image?")
                if result:
                   os.startfile(output_image_path)
        except (Exception) as e:
            messagebox.showerror("Error", f"An error occurred.\n\n{e}")
            self.close_window()


    def blend_images(self, original_image_path, upscaled_image_path, extension):
        with Image.open(original_image_path).convert("RGBA") as original_image:
            with Image.open(upscaled_image_path).convert("RGBA") as upscaled_image:
                original_image = original_image.resize(upscaled_image.size, Image.LANCZOS)
                alpha = self.upscale_strength_value.get() / 100.0
                blended_image = Image.blend(original_image, upscaled_image, alpha)
                if extension.lower() in ['.jpg', '.jpeg']:
                    blended_image = blended_image.convert("RGB")
                blended_image.save(upscaled_image_path)


    def get_image_index(self, directory, filename):
        filename = os.path.basename(filename)
        image_files = sorted((file for file in os.listdir(directory) if file.lower().endswith(self.supported_filetypes)), key=self.sort_key)
        return image_files.index(filename) if filename in image_files else -1


    def delete_converted_image(self):
        if self.converted_filepath and os.path.exists(self.converted_filepath):
            os.remove(self.converted_filepath)
            self.converted_filepath = None


    def resize_image(self, output_image_path):
        if not self.top.winfo_exists():
            return
        selected_scaling_factor = float(self.upscale_factor_value.get())
        with Image.open(output_image_path) as img:
            current_width, current_height = img.size
            upscale_tool_factor = 4.0
            original_width = int(current_width / upscale_tool_factor)
            original_height = int(current_height / upscale_tool_factor)
            new_width = int(original_width * selected_scaling_factor)
            new_height = int(original_height * selected_scaling_factor)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            img.save(output_image_path, quality=100)


#endregion
################################################################################################################################################
#region -  Window drag


    def start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y


    def stop_drag(self, event):
        self.start_x = None
        self.start_y = None


    def dragging_window(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        x = self.top.winfo_x() + dx
        y = self.top.winfo_y() + dy
        self.top.geometry(f"+{x}+{y}")


#endregion
################################################################################################################################################
#region -  Widget highlighting


    def bind_widget_highlight(self, widget, add=False, color=None):
        add = '+' if add else ''
        if color:
            widget.bind("<Enter>", lambda event: self.mouse_enter(event, color), add=add)
        else:
            widget.bind("<Enter>", self.mouse_enter, add=add)
        widget.bind("<Leave>", self.mouse_leave, add=add)


    def mouse_enter(self, event, color='#e5f3ff'):
        if event.widget['state'] == 'normal':
            event.widget['background'] = color


    def mouse_leave(self, event):
        event.widget['background'] = 'SystemButtonFace'


#endregion
################################################################################################################################################
#region -  Image Info / label


    def get_image_info(self):
        try:
            with Image.open(self.original_filepath) as image:
                self.original_image_width, self.original_image_height = image.size
                if self.original_filepath.lower().endswith(".gif"):
                    frames = [frame for frame in ImageSequence.Iterator(image)]
                    self.total_gif_frames = len(frames)
                    self.current_gif_frame = format(1, f'0{len(str(self.total_gif_frames))}d')
                else:
                    self.total_gif_frames = None
                    self.current_gif_frame = None
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error while opening image.\n\n{e}")
            self.close_window()


    def update_size_info_label(self, event=None):
        if not self.batch_mode:
            selected_scaling_factor = float(self.upscale_factor_value.get())
            new_width = self.original_image_width * selected_scaling_factor
            new_height = self.original_image_height * selected_scaling_factor
            self.label_new_dimensions.config(text=f"{int(new_width)} x {int(new_height)}")
            return new_width, new_height


    def update_strength_label(self, value):
        value = int(float(value))
        self.upscale_strength_value.set(value)
        self.label_upscale_strength_percent.config(text=f"{value}%")


    def update_upscale_factor_label(self, event):
        value = round(float(self.upscale_factor_value.get()) * 4) / 4
        self.upscale_factor_value.set(value)
        self.label_upscale_factor_value.config(text=f"{value:.2f}x")
        self.update_size_info_label()


#endregion
################################################################################################################################################
#region -  Misc


    def set_widget_state(self, state):
        widget_names = [
            "label_upscale_model",
            "combobox_upscale_model",
            "label_size",
            "entry_size",
            "label_upscale_strength",
            "slider_upscale_strength",
            "label_upscale_factor_value",
            "label_upscale_strength_percent"
        ]
        for widget_name in widget_names:
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.config(state=state)


    def convert_webp_to_jpg(self, directory, filename):
        with Image.open(self.original_filepath) as img:
            if img.mode == "RGBA":
                img = img.convert("RGB")
            jpg_filepath = os.path.join(directory, f"{filename}.jpg")
            img.save(jpg_filepath, 'JPEG', quality=100)
            self.converted_filepath = jpg_filepath
            extension = '.jpg'
            return extension


    def update_progress(self, progress):
        if not self.top.winfo_exists():
            return
        self.progress_bar.config(value=progress)
        self.frame_primary_buttons.update_idletasks()


    def delete_temp_dir(self):
        try:
            temp_dir = os.path.join(os.path.dirname(self.original_filepath), "temp_upscale_img")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except (PermissionError, FileNotFoundError):
            return


    def choose_directory(self, path_variable):
        directory = askdirectory()
        path_variable.set(directory)


    def open_directory(self, directory):
        try:
            if os.path.isdir(directory):
                os.startfile(directory)
        except Exception: return


    def close_window(self, index=None, event=None):
        self.is_window_closed = True
        self.delete_temp_dir()
        if index:
            self.ImgTxt_update_pair()
            self.ImgTxt_jump_to_image(index)
        self.top.destroy()


#endregion
################################################################################################################################################
#region -  Changelog

'''


v1.04 changes:


  - New:
    - Now supports batch upscaling a folder of  images.
    - The `Upscale Factor` widget is now a slider allowing you to select `from 0.25`, `to 8.0`, in `0.25 increments`.
    - New settings: `Strength` Set this from 0%, to 100% to define how much of the original image is visible after upscaling.


<br>


  - Fixed:
    - Settings are now disabled while upscaling to prevent them from being adjusted while upscaling.
    - Fixed issues with opening and holding-up images in the process.


<br>


  - Other changes:
    -


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
