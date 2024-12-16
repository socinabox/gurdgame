import tkinter as tk
from tkinter import messagebox
import random
import json
import os
import sys
from PIL import Image, ImageTk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import webbrowser

# Determine if running as a frozen (compiled) executable
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

grocery_file_path = os.path.join(application_path, "grocery_items.txt")

local_vars = {}
with open(grocery_file_path, "r") as f:
    file_content = f.read()
    exec(file_content, {}, local_vars)

grocery_items = local_vars['grocery_items']

WIN_THRESHOLD = 50
LOSE_THRESHOLD = -20
GROCERY_WIN_THRESHOLD = 100
DIFFICULTY = "medium"

def load_progress():
    progress_path = os.path.join(application_path, "progress.json")
    if os.path.exists(progress_path):
        with open(progress_path, "r") as f:
            data = json.load(f)
    else:
        data = {"total_points": 0, "games_played": 0}
    return data

def save_progress(data):
    progress_path = os.path.join(application_path, "progress.json")
    with open(progress_path, "w") as f:
        json.dump(data, f)

def select_foods(options, count=2, difficulty="medium"):
    good_foods = [f for f in options if f[1] > 0]
    bad_foods = [f for f in options if f[1] < 0]
    chosen_good = random.choice(good_foods)
    chosen_bad = random.choice(bad_foods)
    selected = [chosen_good, chosen_bad]
    random.shuffle(selected)
    return selected

# Example meditation videos dictionary
meditation_videos = {
    "Calm": "https://www.youtube.com/@calm",
    "Breathing": "https://www.youtube.com/@EckhartTolle",
    "Headspace": "https://www.youtube.com/@headspace",
    "Cozy Cycles": "https://www.youtube.com/@CozyCycles"
}

class GERDGameApp:
    def __init__(self, master):
        self.master = master
        self.master.title("GERD-Friendly Eating Game")

        self.images_dir = os.path.join(application_path, "images")

        self.points = 0
        self.data = load_progress()

        self.grocery_picks = 0
        self.grocery_mode = False

        self.fig = Figure(figsize=(4,1), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.info_frame = tk.Frame(self.master)
        self.info_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.points_label = tk.Label(self.info_frame, text="Points: 0")
        self.points_label.pack(side=tk.LEFT, padx=10)
        
        self.message_label = tk.Label(self.info_frame, text="Choose a game mode")
        self.message_label.pack(side=tk.LEFT, padx=10)
        
        self.image_label = tk.Label(self.master)
        self.image_label.pack(side=tk.TOP, pady=10)

        self.choices_frame = tk.Frame(self.master)
        self.choices_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.game_mode_frame = tk.Frame(self.master)
        self.game_mode_frame.pack(side=tk.TOP, pady=20)

        self.main_game_button = tk.Button(self.game_mode_frame, text="Play Meal-Sequence Game", command=self.start_main_game)
        self.main_game_button.pack(side=tk.LEFT, padx=10)

        self.grocery_game_button = tk.Button(self.game_mode_frame, text="Play Grocery Selection Game", command=self.start_grocery_game)
        self.grocery_game_button.pack(side=tk.LEFT, padx=10)

        # Add Meditation Videos button
        self.meditation_button = tk.Button(self.game_mode_frame, text="Meditation Videos", command=self.show_meditation_videos)
        self.meditation_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(self.master, text="Start Selected Game", command=self.no_op)
        self.next_button.pack(side=tk.BOTTOM, pady=10)

        self.update_acid_graph()

    def no_op(self):
        pass

    def update_acid_graph(self):
        self.ax.clear()
        max_points = WIN_THRESHOLD if not self.grocery_mode else GROCERY_WIN_THRESHOLD
        acid_level = max_points - self.points
        num_hash = min(max(acid_level, 0), 50)
        num_dot = 50 - num_hash
        
        display_str = "#" * num_hash + "." * num_dot
        self.ax.text(0.5, 0.5, f"Acid Level:\n{display_str}", ha='center', va='center', 
                     fontname='DejaVu Sans Mono', fontsize=10)
        self.ax.axis('off')

        self.canvas.draw()

    def start_main_game(self):
        self.reset_for_main_menu()
        self.message_label.config(text="Make GERD-friendly choices!")
        self.next_button.config(text="Next Choice", command=self.next_round_main_game)
        self.points = 0
        self.grocery_mode = False
        self.update_points_display()
        self.clear_choices()
        self.next_round_main_game()

    def next_round_main_game(self):
        self.clear_choices()
        selected_options = select_foods(grocery_items, count=2, difficulty=DIFFICULTY)
        self.message_label.config(text="Choose the GERD-friendly option!")
        
        for opt in selected_options:
            food_name, score, explanation, img_path, category = opt
            btn = tk.Button(self.choices_frame, text=food_name, command=lambda o=opt: self.choose_food_main_game(o))
            btn.pack(side=tk.LEFT, padx=10, pady=5)

    def choose_food_main_game(self, option):
        food_name, score, explanation, img_path, category = option
        self.points += score
        self.update_points_display()
        self.message_label.config(text=f"You chose {food_name}: {explanation}")

        if score > 0:
            self.update_food_image("happy.jpg")
        else:
            self.update_food_image("sad.jpg")

        self.update_acid_graph()

        if self.points >= WIN_THRESHOLD:
            messagebox.showinfo("Congratulations", "You reached 50 points! You win!")
            self.end_main_game()
        elif self.points <= LOSE_THRESHOLD:
            messagebox.showinfo("Game Over", "You reached -20 points or less. You lose!")
            self.end_main_game()
        else:
            self.master.after(2000, self.next_round_main_game)

    def update_points_display(self):
        self.points_label.config(text=f"Points: {self.points}")

    def clear_choices(self):
        for widget in self.choices_frame.winfo_children():
            widget.destroy()

    def end_main_game(self):
        self.data["total_points"] += self.points
        self.data["games_played"] += 1
        save_progress(self.data)
        avg_points = self.data["total_points"] / self.data["games_played"] if self.data["games_played"] > 0 else 0
        messagebox.showinfo("Game Over", f"Your total points this session: {self.points}\nAverage: {avg_points:.2f}")
        self.show_end_options()

    def start_grocery_game(self):
        self.reset_for_main_menu()
        self.grocery_mode = True
        self.points = 0
        self.grocery_picks = 0
        self.update_points_display()
        self.message_label.config(text="Select 20 GERD-friendly items out of 50.")
        self.next_button.pack_forget()

        full_list = random.sample(grocery_items, 50)
        self.grocery_list = full_list

        self.clear_choices()

        categories = {}
        for item in self.grocery_list:
            cat = item[4]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

        for cat, items in categories.items():
            cat_frame = tk.LabelFrame(self.choices_frame, text=cat)
            cat_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            row_frame = tk.Frame(cat_frame)
            row_frame.pack(side=tk.TOP, fill=tk.X)

            for idx, it in enumerate(items):
                food_name, score, explanation, img_path, category = it
                btn = tk.Button(row_frame, text=food_name[:15], width=20, command=lambda o=it: self.choose_grocery(o))
                btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.update_acid_graph()

    def choose_grocery(self, option):
        if not self.grocery_mode:
            return
        food_name, score, explanation, img_path, category = option
        self.points += score
        self.grocery_picks += 1
        self.update_points_display()

        if score > 0:
            self.update_food_image("happy.jpg")
        else:
            self.update_food_image("sad.jpg")

        self.message_label.config(text=f"You chose {food_name}. {explanation}")
        self.update_acid_graph()

        if self.points >= GROCERY_WIN_THRESHOLD:
            messagebox.showinfo("Congratulations", "You reached 100 points!")
            self.end_grocery_game()
            return
        elif self.points <= LOSE_THRESHOLD:
            messagebox.showinfo("Too Bad", "You dropped below -20 points. You lose!")
            self.end_grocery_game()
            return

        if self.grocery_picks >= 20:
            if self.points >= GROCERY_WIN_THRESHOLD:
                messagebox.showinfo("Congratulations", "You reached 100 points!")
            elif self.points <= LOSE_THRESHOLD:
                messagebox.showinfo("Too Bad", "You dropped below -20 points. You lose!")
            else:
                messagebox.showinfo("Game Over", f"You finished with {self.points} points.")
            self.end_grocery_game()

    def end_grocery_game(self):
        self.data["total_points"] += self.points
        self.data["games_played"] += 1
        save_progress(self.data)
        avg_points = self.data["total_points"] / self.data["games_played"] if self.data["games_played"] > 0 else 0
        messagebox.showinfo("Session Summary", f"Your total points: {self.points}\nAverage points: {avg_points:.2f}")
        self.show_end_options()

    def update_food_image(self, img_filename):
        test_img_path = os.path.join(self.images_dir, img_filename)
        if os.path.exists(test_img_path):
            img = Image.open(test_img_path).resize((150,150))
            self.photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo, text='')
        else:
            self.image_label.config(image='', text='(No image available)')

    def show_end_options(self):
        end_window = tk.Toplevel(self.master)
        end_window.title("What Next?")
        prompt_label = tk.Label(end_window, text="What would you like to do next?")
        prompt_label.pack(pady=10)

        def quit_game():
            self.master.destroy()

        def return_main_menu():
            end_window.destroy()
            self.show_main_menu()

        btn_frame = tk.Frame(end_window)
        btn_frame.pack(pady=10)

        quit_btn = tk.Button(btn_frame, text="Quit", command=quit_game)
        quit_btn.pack(side=tk.LEFT, padx=5)

        return_btn = tk.Button(btn_frame, text="Return", command=return_main_menu)
        return_btn.pack(side=tk.LEFT, padx=5)

    def show_main_menu(self):
        self.clear_choices()
        self.message_label.config(text="Choose a game mode")
        self.points = 0
        self.update_points_display()

        self.game_mode_frame.pack(side=tk.TOP, pady=20)
        self.next_button.config(text="Start Selected Game", command=self.no_op)
        self.image_label.config(image='', text='')
        self.grocery_mode = False
        self.update_acid_graph()

    def reset_for_main_menu(self):
        for widget in self.choices_frame.winfo_children():
            widget.destroy()
        self.game_mode_frame.pack_forget()
        self.image_label.config(image='', text='')

    def show_meditation_videos(self):
        meditation_window = tk.Toplevel(self.master)
        meditation_window.title("Recommended Meditation Videos")

        info_label = tk.Label(meditation_window, text="Click on a video to open it in your browser:")
        info_label.pack(pady=10)

        for title, url in meditation_videos.items():
            btn = tk.Button(meditation_window, text=title, fg="blue", cursor="hand2",
                            command=lambda link=url: webbrowser.open(link))
            btn.pack(pady=5, padx=10)

        close_btn = tk.Button(meditation_window, text="Close", command=meditation_window.destroy)
        close_btn.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = GERDGameApp(root)
    root.mainloop()
