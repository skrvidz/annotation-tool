import io
import tkinter as tk
from tkinter import filedialog, ttk
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import json
import os
from tkinter import simpledialog, messagebox
import tkinter.font as tkFont

class AnnotationTool():
    def __init__(self, master):
        self.master = master
        self.master.title("Annotation Tool")

        # Replace the canvas creation in __init__ method with:
        self.canvas_frame = ttk.Frame(master, cursor='crosshair')
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.font = tkFont.Font(family='Lato Black', size=15, weight='bold')

        # Display
        self.canvas = tk.Canvas(self.canvas_frame)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add a frame for navigation buttons below the canvas
        self.nav_frame = ttk.Frame(self.canvas_frame, style='Card.TFrame')
        self.nav_frame.pack(side=tk.TOP, pady=5)

        # Filename Label
        self.filename_label = ttk.Label(self.nav_frame, text="", font=self.font)
        self.filename_label.pack(side=tk.TOP, fill=tk.BOTH, pady=5)  # Adjust padding as needed

        self.btn_prev = ttk.Button(self.nav_frame, text="Previous", command=self.previous_image)
        self.btn_prev.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.btn_next = ttk.Button(self.nav_frame, text="Next", command=self.next_image)
        self.btn_next.pack(side=tk.RIGHT, fill=tk.X, padx=5, pady=5)

        # Add a frame for zoom controls
        self.zoom_factor = 1.0  # Initialize zoom factor
        self.zoom_frame = ttk.Frame(self.canvas_frame,style='Card.TFrame')
        self.zoom_frame.pack(side=tk.TOP, pady=10)

        self.zoom_in_button = ttk.Button(self.zoom_frame, text="Zoom In", command=self.zoom_in)
        self.zoom_in_button.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.zoom_out_button = ttk.Button(self.zoom_frame, text="Zoom Out",  command=self.zoom_out)
        self.zoom_out_button.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5)

        self.scroll_x = ttk.Scrollbar(self.canvas, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scroll_y = ttk.Scrollbar(self.canvas, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        s = ttk.Style()
        s.configure('TScrollbar',width=35)

        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.annotations = {}  # Store references to bbox and text

         # Side Menu
        self.side_menu = ttk.Frame(master, width=200)
        self.side_menu.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Editing Options
        self.edit_frame = ttk.Frame(self.side_menu,style='Card.TFrame')
        self.edit_frame.pack(pady=10)
        
        self.add = ttk.Button(self.edit_frame, text="Add Annotation", command=self.toggle_add_mode)
        #self.add = ttk.Button(self.edit_frame, text="Add Annotation",command=self.enter_add_mode)
        self.add.pack(side=tk.LEFT, fill=tk.BOTH, padx=5,pady=5)
        self.delete_btn = ttk.Button(self.edit_frame, text="Erase Selected", command=self.delete_bbox)
        self.delete_btn.pack(side=tk.LEFT, fill=tk.BOTH, padx=5,pady=5)

         # Side Menu
        self.save_menu = ttk.Frame(self.side_menu)
        self.save_menu.pack(side=tk.BOTTOM, fill=tk.Y, padx=10, pady=20)

        # Setting up the menu
        self.menu = tk.Menu(master)
        master.config(menu=self.menu)
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Folder", command=self.select_folder)

        # Initialize variables
        
        self.adding_bbox = False
        self.image = None
        self.photo = None
        self.json_data = None
        self.files = []
        self.current_index = -1
   
    def on_canvas_configure(self, event):
        # Reset the scroll region to encompass the image
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def populate_textblocks(self):
        # Clear the listboxes before populating
        self.text_list.delete(0, tk.END)

        # Check if there is any annotation data to populate
        if self.json_data:
            for item in self.json_data:
                self.text_list.insert(tk.END, item['text'])
            

    def redraw_selected(self):
        if not self.image:
            return
    
        self.bbox_list.delete(0, tk.END)
        self.canvas.delete("annotation")  # Use a tag for all annotation objects
        self.annotations.clear()
        selected_indices = self.text_list.curselection()
        selected_items = [self.json_data[i] for i in selected_indices] if selected_indices else self.json_data
        img_width, img_height = self.image.size
        for item in selected_items:
            bbox = item['bbox']
            confidence = item['confidence']
            x1 = bbox['Left'] * img_width * self.zoom_factor
            y1 = bbox['Top'] * img_height * self.zoom_factor
            x2 = x1 + bbox['Width'] * img_width * self.zoom_factor
            y2 = y1 + bbox['Height'] * img_height * self.zoom_factor
            # Draw the rectangle and the text
            outline_color = self.get_color(confidence)
            rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color, tags="annotation", width=3)
            text2 = self.canvas.create_text(x1+2, y1+2, text=f"{item['text']}", anchor='nw', fill='black', tags="annotation", font = self.font)
            text = self.canvas.create_text(x1, y1, text=f"{item['text']}", anchor='nw', fill='deep sky blue', tags="annotation", font=self.font)
            self.annotations[rect] = text,text2  # Populate the annotations dictionary
            bbox_coords = (x1, y1, x2, y2)
            self.bbox_list.insert(tk.END, bbox_coords)

    def toggle_add_mode(self):
        self.adding_bbox = not self.adding_bbox
        # Update the button text based on the current mode
        self.add.config(text="Finish Adding" if self.adding_bbox else "Add Annotation")

    def enter_add_mode(self):
        self.adding_bbox = True

    def add_annotation(self, bbox_coords):
        if not self.image:
            return
        text = simpledialog.askstring("Input", "Enter the text for the annotation:",
                                      parent=self.master)
        if text:
            x1, y1, x2, y2 = bbox_coords
            rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#000fff000", width=3, tags="annotation")
            text_bg = self.canvas.create_text(x1+2, y1+2, text=text, anchor='nw', fill='black', tags="annotation", font=self.font)
            text_id = self.canvas.create_text(x1, y1, text=text, anchor='nw', fill='deep sky blue', tags="annotation", font=self.font)
            self.annotations[rect] = (text_id, text_bg)
    
            # Convert the absolute coordinates to relative
            img_width, img_height = self.image.size  # Assuming self.image holds the current image

            json_bbox = {
                'Width': (x2 - x1) / img_width / self.zoom_factor,
                'Height': (y2 - y1) / img_height / self.zoom_factor,
                'Left': x1 / img_width / self.zoom_factor,
                'Top': y1 / img_height / self.zoom_factor
            }
    
            # As we don't have a 'confidence' value for user-added annotations, set a default or ask the user
            confidence = 100  # or any default value
    
            # Append the new annotation to json_data
            new_annotation = {
                'text': text,
                'confidence': confidence,
                'bbox': json_bbox
            }
            if not self.json_data:
                self.json_data = []

            self.json_data.append(new_annotation)
    
            # Sort the json_data list of dictionaries based on the 'Top' then 'Left' values of the 'bbox'
            self.json_data.sort(key=lambda item: (item['bbox']['Top'], item['bbox']['Left']))
    
            # Determine the index where to insert the text in the list and insert it
            insert_index = self.find_insert_index(bbox_coords)
            self.text_list.insert(insert_index, text)
            self.refresh_bbox_list()

    def find_insert_index(self, new_bbox_coords):
        new_x1, new_y1, _, _ = new_bbox_coords
        for index in range(self.bbox_list.size()):
            bbox_coords = self.bbox_list.get(index)
            x1, y1, _, _ = map(float, bbox_coords[0:4])
            # Check if new bbox is below or to the right of the current bbox
            if new_y1 > y1 or (new_y1 == y1 and new_x1 > x1):
                continue
            else:
                return index
        return self.bbox_list.size()
    
    def select_folder(self):
        response = messagebox.askyesno("Select Folders", "Do you want to select multiple folders?")
        folder_paths = []
        if response:
            # Multiple folder selection
            while True:
                folder_path = filedialog.askdirectory(mustexist=True, title="Select Folder")
                if not folder_path:
                    break
                folder_paths.append(folder_path)
        else:
            # Separate folder selection for images and JSONs
            img_folder_path = filedialog.askdirectory(mustexist=True, title="Select Image Folder")
            if img_folder_path:
                folder_paths.append(img_folder_path)
            json_folder_path = filedialog.askdirectory(mustexist=True, title="Select JSON Folder")
            if json_folder_path:
                folder_paths.append(json_folder_path)

        if folder_paths:
            try:
                self.files = self.find_pairs(folder_paths)
                print("self.files")
                if self.files:
                    self.current_index = 0
                    self.load_image_and_json(*self.files[self.current_index])
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

    def find_pairs(self, folder_paths):
        # Extend to include PDF files in the search
        images, jsons = [], []
        json_folder = None

        # Distinguish between image/JSON folders and assign JSON folder path
        for folder in folder_paths:
            files = os.listdir(folder)
            if any(f.lower().endswith('.json') for f in files):
                if json_folder is None:  # Assume the first folder containing any JSON files is the JSON folder
                    json_folder = folder
            images.extend([os.path.join(folder, f) for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))])
        
        if json_folder is None:
            raise ValueError("No JSON folder found among the provided paths.")
    
        jsons = [os.path.join(json_folder, f) for f in os.listdir(json_folder) if f.lower().endswith('.json')]
        
        pairs = []
        for img_path in images:
            img_name = os.path.splitext(os.path.basename(img_path))[0]
            json_name = img_name + '.json'
            json_path = os.path.join(json_folder, json_name)  # This ensures json_path is always a valid path

            if not os.path.exists(json_path):
                # Create an empty JSON file if it doesn't exist
                with open(json_path, 'w') as file:
                    json.dump({}, file)  # Writing an empty JSON object
            pairs.append((img_path, json_path))
        return pairs
    
    def load_image_and_json(self, image_path, json_path):
        try:
            if image_path.lower().endswith('.pdf'):
                print("pdwhattt")
                # Open the PDF and convert the first page to a PIL Image
                with fitz.open(image_path) as doc:
                    page = doc.load_page(0)  # Load the first page
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("ppm")
                    self.image = Image.open(io.BytesIO(img_data))
            else:
                # If not a PDF, open the image as before
                self.image = Image.open(image_path)

            self.photo = ImageTk.PhotoImage(self.image)

            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.photo, anchor='nw')

            with open(json_path, 'r') as file:
                self.json_data = json.load(file)

            self.annotations.clear()
            self.draw_annotations()
            self.draw_filename()
            self.populate_textblocks()
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading files: {e}")

    def draw_filename(self):
        # Extract the original image or PDF file name without extension
        file_path = self.files[self.current_index][0]
        img_filename = os.path.basename(file_path)
        noext_filename = os.path.splitext(img_filename)[0]

        self.filename_label.config(text=noext_filename)

    def draw_annotations(self):

        self.bbox_list.delete(0, tk.END)
        # Clear the canvas except for the image
        self.canvas.delete("annotation")  # Use a tag for all annotation objects

        # Get image dimensions for scaling
        img_width, img_height = self.image.size

        # Loop through items in JSON and draw bounding boxes and text
        for item in self.json_data:
            bbox = item['bbox']
            confidence = item['confidence']
            # Apply zoom factor to bounding box coordinates
            x1 = bbox['Left'] * img_width * self.zoom_factor
            y1 = bbox['Top'] * img_height * self.zoom_factor
            x2 = x1 + bbox['Width'] * img_width * self.zoom_factor
            y2 = y1 + bbox['Height'] * img_height * self.zoom_factor

            # Draw the rectangle and the text
            outline_color = self.get_color(confidence)
            rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline=outline_color , tags="annotation",width=3)
            text2 = self.canvas.create_text(x1+2, y1+2, text=f"{item['text']}", anchor='nw', fill='black', tags="annotation", font = self.font)
            text = self.canvas.create_text(x1, y1, text=f"{item['text']}", anchor='nw', fill='deep sky blue', tags="annotation", font = self.font)
            self.annotations[rect] = text, text2  # Populate the annotations dictionary
            bbox_coords = (x1, y1, x2, y2)
            self.bbox_list.insert(tk.END, bbox_coords)

    def get_color(self, confidence):
        # Assume confidence is between 0 and 100

        if confidence > 90:
            return "#000fff000"  # green
        elif confidence > 75:
            return "#a3ff00"  # lighter green
        #elif confidence > 70:
        #    return "#fff400"  # yellow
        #elif confidence > 60:
        #    return "#ffa700"  # orange
        else:
            return "#ff0000"  # red
        
    def next_image(self):
        if self.current_index < len(self.files) - 1:
            self.current_index += 1
            self.zoom_factor=1
            self.load_image_and_json(*self.files[self.current_index])
    
    def previous_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.zoom_factor=1
            self.load_image_and_json(*self.files[self.current_index])

    def zoom_in(self, event=None):
        self.zoom(1.1)  # Zoom in by 10%

    def zoom_out(self, event=None):
        self.zoom(0.9)  # Zoom out by 10%

    def zoom(self, zoom_factor):
        # Adjust zoom factor
        if not self.image:
            return
        
        self.zoom_factor *= zoom_factor
    
        # Rescale all canvas objects
        self.canvas.scale("all", 0, 0, zoom_factor, zoom_factor)
    
        # Resize the image while maintaining the aspect ratio
        width, height = self.image.size
        new_size = int(width * self.zoom_factor), int(height * self.zoom_factor)
        resized_image = self.image.resize(new_size, Image.LANCZOS)
        
        # Update the PhotoImage object
        self.photo = ImageTk.PhotoImage(resized_image)
    
        # Delete the previous canvas image
        self.canvas.delete("image")
        
        # Redraw the image with the new scale and keep a reference to the image object
        self.canvas.image = self.canvas.create_image(0, 0, image=self.photo, anchor='nw', tags="image")
    
        # Update the scroll region to encompass the new image size
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
        # Redraw annotations for the current zoom level
        self.redraw_selected()

        self.populate_textblocks()

    def create_ui_elements(self):
        # Text Annotations Listbox
        self.text_list = tk.Listbox(self.side_menu, width=35, selectmode='multiple', 
                                    bg='white', fg='black', highlightthickness=0, bd=0)
        self.text_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.buttons = ttk.Frame(self.side_menu, style='Card.TFrame')
        self.buttons.pack(side=tk.TOP, fill=tk.BOTH, pady=10, padx=10)
        # Textblock Selection
        #self.redraw_button = ttk.Button(self.buttons, text="Redraw", command=self.redraw_selected)
        self.redraw_button = ttk.Button(self.buttons, text="Redraw", command=self.redraw_selected)
        self.redraw_button.pack(side=tk.LEFT, fill=tk.Y, padx=5,pady=5)

        self.clear_all_btn = ttk.Button(self.buttons, text="Reset", command=self.reset_annotations)
        self.clear_all_btn.pack(side=tk.LEFT, fill=tk.Y, padx=5,pady=5)
        
        self.clear_all_btn = ttk.Button(self.buttons, text="Clear All", command=self.clear_all_bboxes)
        self.clear_all_btn.pack(side=tk.LEFT, fill=tk.Y, padx=5,pady=5)

        # Bounding Boxes Listbox
        self.bbox_list = tk.Listbox(self.side_menu, selectmode='multiple',
                                    bg='white', fg='black', highlightthickness=0, bd=0)
        self.bbox_list.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=10,pady=10)
        
        self.save_bttn = ttk.Button(self.save_menu, text='Save JSON',style='Accent.TButton', command=self.save_annotations)
        self.save_bttn.pack(side=tk.TOP,fill=tk.Y, padx=5, pady=5)

        # Bind the canvas with mouse click, drag, and release events
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

    def on_canvas_click(self, event):

        if self.adding_bbox:
            self.start_x = self.canvas.canvasx(event.x)
            self.start_y = self.canvas.canvasy(event.y)
            self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x + 1, self.start_y + 1, outline="#000fff000",width=3)
        else:
            return

    def on_canvas_drag(self, event):

        if self.adding_bbox:
            # Update the size of the rectangle as the mouse is dragged
            curX = self.canvas.canvasx(event.x)
            curY = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)
        else:
            return

    #def on_canvas_release(self, event):
    #    if self.adding_bbox:
    #        curX = self.canvas.canvasx(event.x)
    #        curY = self.canvas.canvasy(event.y)
    #        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)
    #        self.add_annotation((self.start_x, self.start_y, curX, curY))
    #        self.canvas.delete(self.rect)
    #        self.adding_bbox = False  # Reset the flag here
    #    else:
    #        return
        
    def on_canvas_release(self, event):
        if self.adding_bbox:
            curX = self.canvas.canvasx(event.x)
            curY = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)
            self.add_annotation((self.start_x, self.start_y, curX, curY))
            self.canvas.delete(self.rect)
            # Do not reset the flag here, user will toggle the mode manually using the button
        else:
            return

    def delete_bbox(self):
        selected_bbox_index = self.bbox_list.curselection()
        selected_text_index = self.text_list.curselection()

        if not selected_bbox_index and not selected_text_index:
            messagebox.showinfo("Info", "No bounding box or text selected")
            return
        
        response = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this annotation?")
        if response:  # Step 4: Delete Annotation
            # Prefer bounding box selection if available, otherwise use text selection
            if selected_bbox_index:
                selected_index = selected_bbox_index[0]
            else:
                selected_index = selected_text_index[0]

            bbox_id = list(self.annotations.keys())[selected_index]
            text_id, text_bg = self.annotations[bbox_id]

            # Retrieve the text content from the canvas item
            text_content = self.canvas.itemcget(text_id, 'text')

            # Delete both the bounding box and its associated text items from the canvas
            self.canvas.delete(bbox_id)
            self.canvas.delete(text_id)
            self.canvas.delete(text_bg)

            # Update the annotations dictionary
            del self.annotations[bbox_id]

            # Remove the item from the listboxes
            self.bbox_list.delete(selected_index)
            self.text_list.delete(selected_index)

            # Remove the corresponding annotation from json_data by matching text content
            self.json_data = [item for item in self.json_data if item['text'] != text_content]
            self.populate_textblocks()

    def clear_all_bboxes(self):
        response = messagebox.askyesno("Confirm Clear All", "Are you sure you want to delete all annotations?")
        if response:  # Step 4: Delete Annotation
            # Clear the json_data list
            self.json_data = []

            # You may also want to clear other related structures if needed
            self.annotations.clear()
            self.bbox_list.delete(0, tk.END)
            self.text_list.delete(0, tk.END)
            self.canvas.delete("annotation")

    def reset_annotations(self):
        if not self.image:
            return
        self.zoom_factor=1
        self.load_image_and_json(*self.files[self.current_index])

    def refresh_bbox_list(self):
        # Step 1: Collect all bounding box coordinates and associated text
        bbox_data = []
        for rect, (text_id, _) in self.annotations.items():
            text = self.canvas.itemcget(text_id, 'text')  # Retrieve the associated text
            coords = self.canvas.coords(rect)  # Retrieve the coordinates
            if coords:
                bbox_data.append((coords, text))

        # Step 2: Sort the bounding boxes by their coordinates (top to bottom, then left to right)
        bbox_data.sort(key=lambda x: (x[0][1], x[0][0]))  # Sort by y1 (top) and then x1 (left)

        # Step 3: Clear the current list and insert the sorted data
        self.bbox_list.delete(0, tk.END)
        for coords, text in bbox_data:
            self.bbox_list.insert(tk.END, coords)

    def save_annotations(self):
        if not self.image:
            messagebox.showinfo("Info", "No image loaded.")
            return

        # Ask the user to select a folder
        folder_path = filedialog.askdirectory(
            title="Select Folder to Save Annotations"
        )

        # If the user cancels the folder selection, folder_path will be empty
        if not folder_path:
            messagebox.showinfo("Info", "Save operation cancelled.")
            return

        # Extract the original image file name without extension
        img_filename = os.path.basename(self.files[self.current_index][0])
        noext_filename = os.path.splitext(img_filename)[0]

        # Create a JSON file name based on the original image file name
        json_file_name = f"{noext_filename}.json"
        json_file_path = os.path.join(folder_path, json_file_name)

        # Save annotations to the JSON file
        try:
            with open(json_file_path, 'w') as file:
                json.dump(self.json_data, file, indent=4)
            messagebox.showinfo("Success", f"Annotations saved successfully to {json_file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving annotations: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    current_directory = os.getcwd()
    root.tk.call('source','./azure/azure.tcl')
    root.tk.call("set_theme", "light")
    theme = tk.BooleanVar(value = False)

    def on_toggle():
        if theme.get():
            root.tk.call("set_theme", "dark")
        else:
            root.tk.call("set_theme", "light")

    toggle_button = ttk.Checkbutton(app.canvas_frame, text='Change Theme', style='Switch.TCheckbutton', variable=theme, command=on_toggle)
    toggle_button.pack()

    app.create_ui_elements()
    root.mainloop()    
            
