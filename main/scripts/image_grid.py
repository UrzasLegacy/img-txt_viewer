"""
########################################
#                                      #
#              Image Grid              #
#                                      #
#   Version : v1.02                    #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################

Description:
-------------
Display a grid of images, clicking an image returns the index as defined in 'natural_sort'.
Images without a text pair have a red flag placed over them.

"""


################################################################################################################################################
#region -  Imports


import os
import re
from tkinter import ttk, Toplevel, IntVar, StringVar, BooleanVar, Frame, Label, Button, Radiobutton, Checkbutton, Scale, Scrollbar, Canvas
from PIL import Image, ImageTk, ImageDraw, ImageFont

from main.scripts.TkToolTip import TkToolTip as ToolTip


#endregion
################################################################################################################################################
#region - CLASS: ImageGrid


class ImageGrid:
    image_cache = {1: {}, 2: {}, 3: {}}  # Cache for each thumbnail size
    text_file_cache = {}

    def __init__(self, master, filepath, window_x, window_y, jump_to_image):

        # Window configuration
        self.create_window(master, window_x, window_y)

        # Image navigation function
        self.ImgTxt_jump_to_image = jump_to_image

        # Image directory and supported file types
        self.folder = filepath
        self.supported_filetypes = (".png", ".webp", ".jpg", ".jpeg", ".jpg_large", ".jfif", ".tif", ".tiff", ".bmp", ".gif")

        # Image grid configuration
        self.max_width = 85  # Thumbnail width
        self.max_height = 85  # Thumbnail height
        self.rows = 500  # Max rows
        self.cols = 8  # Max columns
        self.images_per_load = 150  # Num of images to load per set

        # Image loading and filtering
        self.loaded_images = 0  # Num of images loaded to the UI
        self.filtered_images = 0  # Num of images displayed after filtering

        # Image flag
        self.image_flag = self.create_image_flag()

        # Image files in the folder
        self.all_file_list = self.get_all_files()
        self.image_file_list = self.get_image_files()
        self.num_total_images = len(self.image_file_list)  # Number of images in the folder

        # Default thumbnail size. Range=(1,2,3). Set to 3 if total_images is less than 25.
        self.image_size = IntVar(value=3) if self.num_total_images < 25 else IntVar(value=2)

        # Toggle window auto-close when selecting an image
        self.auto_close = BooleanVar(value=True)

        # Interface creation
        self.create_interface()
        self.load_images()


#endregion
################################################################################################################################################
#region -  Create Interface


    def create_interface(self):
        self.create_top_handle()
        self.create_canvas()
        self.create_control_row()


    def create_top_handle(self):
        self.frame_top_Handle = Frame(self.top)
        self.frame_top_Handle.pack(fill="both")

        title = Label(self.frame_top_Handle, cursor="size", text="Image Grid", font=("", 16))
        title.pack(side="top", fill="x", padx=5, pady=5)
        title.bind("<ButtonPress-1>", self.start_drag)
        title.bind("<ButtonRelease-1>", self.stop_drag)
        title.bind("<B1-Motion>", self.dragging_window)

        self.button_close = Button(self.frame_top_Handle, text="X", overrelief="groove", relief="flat", command=self.close_window)
        self.button_close.place(anchor="nw", relx=0.945, height=40, width=40)
        self.bind_widget_highlight(self.button_close, color='#ffcac9')
        ToolTip.create(self.button_close, "Close", 500, 6, 12)

        separator = ttk.Separator(self.frame_top_Handle)
        separator.pack(side="top", fill="x")


    def create_canvas(self):
        self.frame_main = Frame(self.top)
        self.frame_main.pack(fill="both", expand=True)

        self.scrollbar = Scrollbar(self.frame_main)
        self.scrollbar.pack(side="right", fill="y")

        self.frame_thumbnails = Frame(self.frame_main)
        self.frame_thumbnails.pack(side="left", fill="both", expand=True)

        self.canvas_thumbnails = Canvas(self.frame_thumbnails, yscrollcommand=self.scrollbar.set)
        self.canvas_thumbnails.pack(side="top", fill="both", expand=True)
        self.canvas_thumbnails.bind("<MouseWheel>", self.on_mousewheel)

        self.scrollbar.config(command=self.canvas_thumbnails.yview)

        self.frame_image_grid = Frame(self.canvas_thumbnails)
        self.frame_image_grid.bind("<MouseWheel>", self.on_mousewheel)


    def create_control_row(self):
        self.frame_bottom = Frame(self.frame_thumbnails)
        self.frame_bottom.pack(side="bottom", fill="x", padx=5)

        self.label_image_info = Label(self.frame_bottom, text="Size:")
        self.label_image_info.pack(side="left", padx=5)
        ToolTip.create(self.label_image_info, "Adjust grid size", 500, 6, 12)

        self.slider_image_size = Scale(self.frame_bottom, variable=self.image_size, orient="horizontal", from_=1, to=3, showvalue=False)
        self.slider_image_size.bind("<ButtonRelease-1>", lambda event: self.reload_grid())
        self.slider_image_size.pack(side="left")
        ToolTip.create(self.slider_image_size, "Adjust grid size", 500, 6, 12)

        self.grip_window_size = ttk.Sizegrip(self.frame_bottom)
        self.grip_window_size.pack(side="right", padx=(5,0))
        ToolTip.create(self.grip_window_size, "Adjust window size", 500, 6, 12)

        self.button_refresh = Button(self.frame_bottom, text="Refresh", overrelief="groove", command=self.reload_grid)
        self.button_refresh.pack(side="right", padx=5)
        ToolTip.create(self.button_refresh, "Refresh the image grid. Useful when you've added or removed images, or altered the text pairs.", 500, 6, 12)

        self.button_load_all = Button(self.frame_bottom, text="Load All", overrelief="groove", command=lambda: self.load_images(all_images=True))
        self.button_load_all.pack(side="right", padx=5)
        ToolTip.create(self.button_load_all, "Load all images in the folder (Slow)", 500, 6, 12)

        self.label_image_info = Label(self.frame_bottom)
        self.label_image_info.pack(side="right", padx=5)
        ToolTip.create(self.label_image_info, "Filtered Images : Loaded Images, Total Images", 500, 6, 12)

        self.image_filter = StringVar(value="All")
        self.radiobutton_all = Radiobutton(self.frame_bottom, text="All", variable=self.image_filter, value="All", command=self.reload_grid)
        self.radiobutton_all.pack(side="left", padx=5)
        ToolTip.create(self.radiobutton_all, "Display all LOADED images", 500, 6, 12)

        self.radiobutton_paired = Radiobutton(self.frame_bottom, text="Paired", variable=self.image_filter, value="Paired", command=self.reload_grid)
        self.radiobutton_paired.pack(side="left", padx=5)
        ToolTip.create(self.radiobutton_paired, "Display images with text pairs", 500, 6, 12)

        self.radiobutton_unpaired = Radiobutton(self.frame_bottom, text="Unpaired", variable=self.image_filter, value="Unpaired", command=self.reload_grid)
        self.radiobutton_unpaired.pack(side="left", padx=5)
        ToolTip.create(self.radiobutton_unpaired, "Display images without text pairs", 500, 6, 12)

        self.checkbutton_auto_close = Checkbutton(self.frame_bottom, text="Auto-Close", variable=self.auto_close)
        self.checkbutton_auto_close.pack(side="left", padx=5)
        ToolTip.create(self.checkbutton_auto_close, "Uncheck this to keep the window open after selecting an image", 500, 6, 12)


#endregion
################################################################################################################################################
#region -  Primary Logic


    def reload_grid(self, event=None):
        self.clear_frame(self.frame_image_grid)
        self.set_size_settings()
        self.update_image_info_label()
        self.update_cache_and_grid()


    def update_cache_and_grid(self):
        self.update_filtered_images()
        self.update_image_cache()
        self.create_image_grid()


    def update_image_cache(self):
        image_size_key = self.image_size.get()
        filtered_sorted_files = list(filter(self.filter_images, sorted(self.image_file_list, key=self.natural_sort)))
        current_text_file_sizes = {
            os.path.splitext(os.path.join(self.folder, filename))[0] + '.txt': os.path.getsize(os.path.splitext(os.path.join(self.folder, filename))[0] + '.txt') if os.path.exists(os.path.splitext(os.path.join(self.folder, filename))[0] + '.txt') else 0
            for filename in filtered_sorted_files}
        for filename in filtered_sorted_files:
            img_path, txt_path = self.get_image_and_text_paths(filename)
            current_text_file_size = current_text_file_sizes[txt_path]
            cached_text_file_size = self.text_file_cache.get(txt_path, -1)
            if img_path not in self.image_cache[image_size_key] or current_text_file_size != cached_text_file_size:
                self.create_new_image(img_path, txt_path)
                self.text_file_cache[txt_path] = current_text_file_size


    def update_image_info_label(self):
        self.update_filtered_images()
        self.update_shown_images()
        self.update_button_state()


    def update_shown_images(self):
        shown_images = min(self.filtered_images, self.loaded_images)
        self.label_image_info.config(text=f"{shown_images} : {self.loaded_images}, of {self.num_total_images}")


    def update_button_state(self):
        self.button_load_all.config(state="disabled" if self.loaded_images == self.num_total_images else "normal")


    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()


    def set_size_settings(self):
        size_settings = {1: (50, 50, 13),
                         2: (85, 85, 8),
                         3: (175, 175, 4)}
        self.max_width, self.max_height, self.cols = size_settings.get(self.image_size.get(), (85, 85, 8))


    def create_image_grid(self):
        self.canvas_thumbnails.create_window((0, 0), window=self.frame_image_grid, anchor='nw')
        self.images = self.load_image_set()
        self.populate_image_grid()
        self.configure_scroll_region()
        self.add_load_more_button()


    def populate_image_grid(self):
        for index, (image, filepath, image_index) in enumerate(self.images):
            row, col = divmod(index, self.cols)
            thumbnail = Button(self.frame_image_grid, relief="flat", overrelief="groove", image=image, command=lambda path=filepath: self.on_mouse_click(path))
            thumbnail.image = image
            thumbnail.grid(row=row, column=col)
            thumbnail.bind("<MouseWheel>", self.on_mousewheel)
            ToolTip.create(thumbnail, f"#{image_index + 1}, {os.path.basename(filepath)}", 200, 6, 12)


    def load_images(self, all_images=False):
        self.loaded_images = self.num_total_images if all_images else min(self.loaded_images + self.images_per_load, self.num_total_images)
        self.update_image_info_label()
        self.reload_grid()


    def load_image_set(self):
        images = []
        image_size_key = self.image_size.get()
        filtered_sorted_files = list(filter(self.filter_images, sorted(self.image_file_list, key=self.natural_sort)))
        current_text_file_sizes = {
            os.path.splitext(os.path.join(self.folder, filename))[0] + '.txt': os.path.getsize(os.path.splitext(os.path.join(self.folder, filename))[0] + '.txt') if os.path.exists(os.path.splitext(os.path.join(self.folder, filename))[0] + '.txt') else 0
            for filename in filtered_sorted_files}
        for image_index, filename in enumerate(filtered_sorted_files):
            if len(images) >= self.loaded_images:
                break
            img_path, txt_path = self.get_image_and_text_paths(filename)
            current_text_file_size = current_text_file_sizes[txt_path]
            cached_text_file_size = self.text_file_cache.get(txt_path, -1)
            if img_path not in self.image_cache[image_size_key] or current_text_file_size != cached_text_file_size:
                new_img = self.create_new_image(img_path, txt_path)
            else:
                new_img = self.image_cache[image_size_key][img_path]
            images.append((ImageTk.PhotoImage(new_img), img_path, image_index))
        return images


    def create_new_image(self, img_path, txt_path):
        new_img = Image.new("RGBA", (self.max_width, self.max_height))
        img = Image.open(img_path)
        img.thumbnail((self.max_width, self.max_height))
        position = ((self.max_width - img.width) // 2, (self.max_height - img.height) // 2)
        new_img.paste(img, position)
        if not os.path.exists(txt_path) or os.path.getsize(txt_path) == 0:
            flag_position = (self.max_width - self.image_flag.width, self.max_height - self.image_flag.height)
            new_img.paste(self.image_flag, flag_position, mask=self.image_flag)
        self.image_cache[self.image_size.get()][img_path] = new_img
        return new_img


    def filter_images(self, filename):
        if not filename.lower().endswith(self.supported_filetypes):
            return False
        txt_path = os.path.splitext(os.path.join(self.folder, filename))[0] + '.txt'
        file_size = os.path.getsize(txt_path) if os.path.exists(txt_path) else 0
        filter_dict = {"All": True, "Paired": file_size != 0, "Unpaired": file_size == 0}
        return filter_dict.get(self.image_filter.get(), False)


    def update_filtered_images(self):
        self.filtered_images = sum(1 for _ in filter(self.filter_images, sorted(self.image_file_list, key=self.natural_sort)))


    def get_image_and_text_paths(self, filename):
        img_path = os.path.join(self.folder, filename)
        txt_path = os.path.splitext(img_path)[0] + '.txt'
        return img_path, txt_path


    def paste_image_flag(self, new_img, img_path, txt_path, current_text_file_size=None):
        img = Image.open(img_path)
        img.thumbnail((self.max_width, self.max_height))
        position = ((self.max_width - img.width) // 2, (self.max_height - img.height) // 2)
        new_img.paste(img, position)
        if current_text_file_size is None:
            current_text_file_size = os.path.getsize(txt_path) if os.path.exists(txt_path) else 0
        if current_text_file_size == 0:
            flag_position = (self.max_width - self.image_flag.width, self.max_height - self.image_flag.height)
            new_img.paste(self.image_flag, flag_position, mask=self.image_flag)
        self.image_cache[self.image_size.get()][img_path] = new_img
        return new_img


    def create_image_flag(self):
        flag_size = 15
        outline_width = 1
        left, top = [dim - flag_size - outline_width for dim in (self.max_width, self.max_height)]
        right, bottom = self.max_width, self.max_height
        image_flag = Image.new('RGBA', (self.max_width, self.max_height))
        draw = ImageDraw.Draw(image_flag)
        draw.rectangle(((left, top), (right, bottom)), fill="black")
        draw.rectangle(((left + outline_width, top + outline_width), (right - outline_width, bottom - outline_width)), fill="red")
        corner_size = flag_size // 2
        triangle_points = [
            (left - outline_width, top - outline_width),
            (left + corner_size, top - outline_width),
            (left - outline_width, top + corner_size)]
        draw.polygon(triangle_points, fill=(0, 0, 0, 0))
        center = ((left + right) // 2, (top + bottom) // 2)
        font = ImageFont.truetype("arial", 15)
        draw.text(center, " -", fill="white", font=font, anchor="mm")
        return image_flag


    def get_image_index(self, directory, filename):
        filename = os.path.basename(filename)
        image_files = sorted((file for file in os.listdir(directory) if file.lower().endswith(self.supported_filetypes)), key=self.natural_sort)
        return image_files.index(filename) if filename in image_files else -1


#endregion
################################################################################################################################################
#region -  Interface Logic


    def configure_scroll_region(self):
        scroll_index = self.loaded_images / self.cols * 1.2
        scrollregion_height = scroll_index * self.max_height
        self.canvas_thumbnails.config(scrollregion=(0, 0, 750, scrollregion_height))


    def add_load_more_button(self):
        if self.image_filter.get() == "All" and self.loaded_images < self.num_total_images:
            load_more_button = Button(self.frame_image_grid, text="Load More...", height=2, command=self.load_images)
            load_more_button.grid(row=self.rows, column=0, columnspan=self.cols, sticky="ew", pady=5)
            ToolTip.create(load_more_button, "Load the next 150 images", 500, 6, 12)


    def on_mouse_click(self, path):
        index = self.get_image_index(self.folder, path)
        self.ImgTxt_jump_to_image(index)
        if self.auto_close.get():
            self.close_window()


    def on_mousewheel(self, event):
        if self.canvas_thumbnails.winfo_exists():
            self.canvas_thumbnails.yview_scroll(int(-1*(event.delta/120)), "units")


#endregion
################################################################################################################################################
#region -  Misc


    def get_all_files(self):
        try:
            return os.listdir(self.folder)
        except (FileNotFoundError, NotADirectoryError):
            return


    def get_image_files(self):
        return [name for name in self.all_file_list if os.path.isfile(os.path.join(self.folder, name)) and name.lower().endswith(self.supported_filetypes)]


    def natural_sort(self, string):
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', string)]


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
#region - Framework


    def create_window(self, master, window_x, window_y):
        # Create a new top-level widget and configure its properties
        self.top = Toplevel(master, borderwidth=2, relief="groove")
        self.top.overrideredirect(True)

        # Set the geometry (size and position) of the window
        window_size = "750x600"
        window_position = f"+{window_x}+{window_y}"
        self.top.geometry(f"{window_size}{window_position}")

        # Set the minimum and maximum size of the window
        self.top.minsize(750, 300)
        self.top.maxsize(750, 6000)

        # Make the window modal, set focus to it, set always on top
        #self.top.grab_set()
        self.top.focus_force()
        #self.top.attributes('-topmost', 1)

        # Bind the Escape and F2 keys to the close_window method
        self.top.bind("<Escape>", lambda event: self.close_window(event))
        self.top.bind('<F2>', lambda event: self.close_window(event))


    def close_window(self, event=None):
        self.top.destroy()


#endregion
################################################################################################################################################
#region - Changelog


'''

v1.02 changes:

  - New:
    -

<br>

  - Fixed:
    - Fixed issue where supported file types were case sensitive.

<br>

  - Other changes:
    - Reuse image_cache across instances, speeding up image loading while slightly increasing memory usage.
    - Internal refactoring, cleanup, and other small improvements here and there.


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
