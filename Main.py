import tkinter as tk
from tkinter import ttk
import os
import random
from tkinter import filedialog
from PIL import Image, ImageTk
import json
import tkinter.font as tkfont
import re

# Defines the clickable images
class ImageButton(tk.Frame):
    def __init__(self, master, command, **kwargs):
        super().__init__(master, **kwargs)
        self.normal_color = "white"  # Match the background color of the main window
        self.hover_color = "#CCCCCC"
        self.click_color = "#999999"

        self.config(bg=self.normal_color, highlightthickness=20, highlightbackground=self.normal_color)
        
        self.photo = None
        self.label = tk.Label(self)
        self.label.pack(padx=0, pady=0)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", lambda e: self.on_click(e, command))
        self.label.bind("<Enter>", self.on_enter)
        self.label.bind("<Leave>", self.on_leave)
        self.label.bind("<Button-1>", lambda e: self.on_click(e, command))
        self.label.config(borderwidth=0, highlightthickness=0, border=0)

    def on_enter(self, _):
        self.config(highlightbackground=self.hover_color)

    def on_leave(self, _):
        self.config(highlightbackground=self.normal_color)

    def on_click(self, _, command):
        self.config(highlightbackground=self.click_color)
        self.after(100, lambda: self.config(highlightbackground=self.normal_color))
        command()

    def update_image(self, image_path):
        if image_path:
            with Image.open(image_path, "r") as image:
                image = self.resize_image(image, 700, 700)
                self.photo = ImageTk.PhotoImage(image)
                self.label.config(image=self.photo)
        else:
            self.photo = None
            self.label.config(image='')

    def resize_image(self, image, max_width, max_height):
        width_ratio = max_width / image.width
        height_ratio = max_height / image.height
        ratio = min(width_ratio, height_ratio)

        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)

        return image.resize((new_width, new_height), Image.ANTIALIAS)

# Main class
class ImageComparator:
    def __init__(self, root):

        self.image_data = {}
        self.deleted_images = []
        self.startScore = 1000
        self.left_image = ""
        self.right_image = ""
        self.image_name_regex = self.load_image_name_regex()

        self.root = root
        self.root.title("Image Comparator")

        # Configure dark theme colors
        self.bg_color = '#222222'
        self.fg_color = '#EEEEEE'
        self.highlight_color = '#444444'
        self.table_color = '#333333'
        self.button_bg = '#CC0000'
        self.button_hover = '#FF0000'

        # Create menu bar
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)

        # Create File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Image Folder", command=self.load_images)
        self.file_menu.add_command(label="Open ELO File", command=self.load_json_file)
        self.file_menu.add_command(label="Save ELO", command=self.save_json_file)

        # Create frames for images and table
        self.image_frame = tk.Frame(self.root, bg=self.bg_color)
        self.image_frame.pack(side="top", padx=50, pady=10)

        # Create container frames for each image + button
        self.left_container = tk.Frame(self.image_frame, bg=self.bg_color)
        self.right_container = tk.Frame(self.image_frame, bg=self.bg_color)

        self.left_image_button = ImageButton(self.left_container, self.left_image_click, bg=self.bg_color)
        self.left_image_button.pack()
        
        self.left_eliminate_button = tk.Button(
            self.left_container,
            text="✕",
            command=self.eliminate_left_image,
            bg=self.button_bg,
            fg='white',
            font=('Arial', 16, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=5
        )
        self.left_eliminate_button.pack(pady=(5, 0))
        self.left_eliminate_button.bind('<Enter>', lambda e: self.left_eliminate_button.config(bg=self.button_hover))
        self.left_eliminate_button.bind('<Leave>', lambda e: self.left_eliminate_button.config(bg=self.button_bg))

        self.right_image_button = ImageButton(self.right_container, self.right_image_click, bg=self.bg_color)
        self.right_image_button.pack()
        
        self.right_eliminate_button = tk.Button(
            self.right_container,
            text="✕",
            command=self.eliminate_right_image,
            bg=self.button_bg,
            fg='white',
            font=('Arial', 16, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=5
        )
        self.right_eliminate_button.pack(pady=(5, 0))
        self.right_eliminate_button.bind('<Enter>', lambda e: self.right_eliminate_button.config(bg=self.button_hover))
        self.right_eliminate_button.bind('<Leave>', lambda e: self.right_eliminate_button.config(bg=self.button_bg))

        self.table_frame = tk.Frame(self.root, bg=self.bg_color)
        self.table_frame.pack(side="top", padx=50, pady=10, fill="both", expand=True)

        # Initially hide the image buttons
        self.show_hide_image_buttons(False)

        # Create and style the table
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure("Treeview",
                             background=self.table_color,
                             foreground=self.fg_color,
                             fieldbackground=self.table_color,
                             borderwidth=0,
                             font=("Franklin Gothic Medium", 14))
        self.style.map('Treeview', background=[('selected', self.highlight_color)])
        self.style.configure("Treeview.Heading",
                             background=self.table_color,
                             foreground=self.fg_color,
                             relief="flat",
                             font=("Franklin Gothic Medium", 16))
        self.style.map("Treeview.Heading",
                       background=[('active', self.highlight_color)])

        self.tree = ttk.Treeview(self.table_frame, columns=('Image', 'Score'), show='headings')
        self.tree.heading('Image', text='Image')
        self.tree.heading('Score', text=f'Score (Min: {int(self.calculate_threshold())})')
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind('<Double-1>', self.open_image)

        # Create and style the scrollbar
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side='right', fill='y')

        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.style.configure("Vertical.TScrollbar",
                             background=self.table_color,
                             bordercolor=self.table_color,
                             arrowcolor=self.fg_color)

    def open_image(self, event):
        item = self.tree.selection()[0]
        image_name = self.tree.item(item, "values")[0]
        full_path = next((path for path in self.image_data.keys() if os.path.basename(path) == image_name), None)
        if full_path:
            if os.name == 'nt':  # For Windows
                os.startfile(full_path)

    # Control whether or not to show the image backgrounds, i.e. if the image isn't loaded yet, don't.
    def show_hide_image_buttons(self, show):
        if show:
            self.left_container.pack(side="left", padx=10, pady=10)
            self.right_container.pack(side="right", padx=10, pady=10)
        else:
            self.left_container.pack_forget()
            self.right_container.pack_forget()

    def calculate_k_factor(self):
        return (0.1 * len(self.image_data)) + 16
    
    def calculate_threshold(self):
        return (-1 * 0.25 * len(self.image_data)) + self.startScore # = 1000
    
    def elo(self, rating_winner, rating_loser, k_factor):
        expected_winner = 1 / (1 + 10 ** ((rating_loser - rating_winner) / 400))
        expected_loser = 1 - expected_winner
    
        # Calculate the new ratings
        new_winner_rating = rating_winner + k_factor * (1 - expected_winner)
        new_loser_rating = rating_loser + k_factor * (0 - expected_loser)

        return new_winner_rating, new_loser_rating

    # When the left image is chosen
    def left_image_click(self):
        scores = self.elo(self.image_data[self.left_image], self.image_data[self.right_image], self.calculate_k_factor())

        self.image_data[self.left_image] = scores[0]
        self.image_data[self.right_image] = scores[1]
        # if the failed image has a score < threshold, consider it a loser and delete it.
        if (self.image_data[self.right_image] < self.calculate_threshold()):
            self.deleted_images.append(self.right_image)
            del self.image_data[self.right_image]

        self.display_random_images()
        self.update_table()

    # When the right image is chosen
    def right_image_click(self):
        scores = self.elo(self.image_data[self.right_image], self.image_data[self.left_image], self.calculate_k_factor())
        
        self.image_data[self.right_image] = scores[0]
        self.image_data[self.left_image] = scores[1]
        # if the failed image has a score < threshold, consider it a loser and delete it.
        if (self.image_data[self.left_image] < self.calculate_threshold()):
            self.deleted_images.append(self.left_image)
            del self.image_data[self.left_image]

        self.display_random_images()
        self.update_table()

    # Eliminate left image directly
    def eliminate_left_image(self):
        if self.left_image in self.image_data:
            self.deleted_images.append(self.left_image)
            del self.image_data[self.left_image]
            self.display_random_images()
            self.update_table()

    # Eliminate right image directly
    def eliminate_right_image(self):
        if self.right_image in self.image_data:
            self.deleted_images.append(self.right_image)
            del self.image_data[self.right_image]
            self.display_random_images()
            self.update_table()
    
    # Find a random pair of images in the dictionary, and update the image buttons with them
    def display_random_images(self):
        if self.image_data:
            random_images = random.sample(list(self.image_data.keys()), 2)
            left_image_path, right_image_path = random_images
            self.left_image = left_image_path
            self.right_image = right_image_path

            self.left_image_button.update_image(left_image_path)
            self.right_image_button.update_image(right_image_path)
            self.show_hide_image_buttons(True)
        else:
            self.left_image_button.update_image(None)
            self.right_image_button.update_image(None)
            self.show_hide_image_buttons(False)

    # Get the image paths and store them into the dictionary
    def load_images(self):
        self.image_data = {}
        folder_path = filedialog.askdirectory()
        if folder_path:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if (re.search(self.image_name_regex, file)):
                        self.image_data[os.path.join(root,file)] = self.startScore

        self.display_random_images()
        self.update_table()

    # Load an existing dictionary (as json) and save it into ours
    def load_json_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as json_file:
                loaded_data = json.load(json_file)
            
            self.image_data = loaded_data.get("image_data", {})
            self.deleted_images = loaded_data.get("deleted_images", [])

        self.display_random_images()
        self.update_table()

    # Save the dictionary with all its progress to a json file
    def save_json_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            data_to_save = {
                "image_data": dict(sorted(self.image_data.items(), key=lambda x: x[1], reverse=True)),
                "deleted_images": self.deleted_images
            }
            with open(file_path, 'w') as json_file:
                json.dump(data_to_save, json_file, indent=4)

    # Load image name regex from an external file (or fallback)
    def load_image_name_regex(self):
        default_regex = "."
        config_path = os.path.join(os.path.dirname(__file__), 'image_name_regex.txt')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                regex = f.read().strip()
                return regex or default_regex
        except Exception:
            return default_regex

    # Update the values in the table when image scores change
    def update_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        sorted_data = sorted(self.image_data.items(), key=lambda x: x[1], reverse=True)
        for image, score in sorted_data:
            # Round the score to the nearest integer
            rounded_score = round(score)
            self.tree.insert('', 'end', values=(os.path.basename(image), rounded_score))
            self.tree.heading("Image", text="Images ("+ str(len(self.image_data)) +"), Eliminated: " + str(len(self.deleted_images)))
            self.tree.heading('Score', text=f'Score (Min: {int(self.calculate_threshold())})')

# Start point
if __name__ == "__main__":
    Image.MAX_IMAGE_PIXELS = None
    root = tk.Tk()
    root.configure(background='#222222')
    root.state('zoomed')
    app = ImageComparator(root)
    root.mainloop()