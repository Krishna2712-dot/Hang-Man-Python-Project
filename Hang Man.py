import tkinter as tk
from tkinter import ttk, messagebox, font
import mysql.connector


class HangmanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Hangman Game")
        self.root.geometry("800x600")

        # Database config (UPDATE THESE)
        self.db_config = {
            'host': '127.0.0.1',
            'user': 'root',
            'password': '123456',
            'database': 'word_guess_game'
        }

        # Game state variables
        self.score = 0
        self.high_score = 0
        self.streak = 0
        self.word = ""
        self.hint = ""
        self.guessed = []
        self.wrong_attempts = 0
        self.max_attempts = 4
        self.timer_id = None
        self.time_left = 0

        # GUI Setup
        self.setup_fonts()
        self.setup_top_panel()
        self.setup_selection_panel()
        self.setup_canvas()
        self.setup_word_display()
        self.setup_keyboard()

    def setup_fonts(self):
        self.header_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.button_font = font.Font(family="Helvetica", size=10)
        self.hint_font = font.Font(family="Helvetica", size=10, slant="italic")

    def setup_top_panel(self):
        self.top_frame = tk.Frame(self.root, bg="white")
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        # Left-aligned scores
        left_frame = tk.Frame(self.top_frame, bg="white")
        left_frame.pack(side=tk.LEFT)
        self.score_label = tk.Label(left_frame, text="Score: 0", bg="white", font=self.header_font)
        self.score_label.pack(side=tk.LEFT, padx=20)
        self.high_score_label = tk.Label(left_frame, text="High Score: 0", bg="white", font=self.header_font)
        self.high_score_label.pack(side=tk.LEFT, padx=20)
        self.streak_label = tk.Label(left_frame, text="Streak: 0", bg="white", font=self.header_font)
        self.streak_label.pack(side=tk.LEFT, padx=20)

        # Right-aligned timer
        self.timer_label = tk.Label(self.top_frame, text="Time: 0", bg="white", font=self.header_font)
        self.timer_label.pack(side=tk.RIGHT, padx=20)

    def setup_selection_panel(self):
        self.selection_frame = tk.Frame(self.root)
        self.selection_frame.pack(pady=10)

        # Difficulty
        self.diff_var = tk.StringVar(value="Easy")
        tk.Label(self.selection_frame, text="Difficulty:", font=self.button_font).grid(row=0, column=0)
        for i, diff in enumerate(["Easy", "Medium", "Hard"]):
            rb = tk.Radiobutton(self.selection_frame, text=diff, variable=self.diff_var, value=diff,
                                font=self.button_font)
            rb.grid(row=0, column=i + 1, padx=5)

        # Category
        self.cat_var = tk.StringVar(value="Movies")
        tk.Label(self.selection_frame, text="Category:", font=self.button_font).grid(row=1, column=0, pady=10)
        for i, cat in enumerate(["Movies", "Countries", "Animals"]):
            rb = tk.Radiobutton(self.selection_frame, text=cat, variable=self.cat_var, value=cat, font=self.button_font)
            rb.grid(row=1, column=i + 1, padx=5)

        # Start button
        self.start_btn = tk.Button(self.selection_frame, text="Start Game", command=self.start_game,
                                   font=self.button_font, bg="#4CAF50", fg="white")
        self.start_btn.grid(row=2, columnspan=4, pady=10)

        # Hint label (hidden initially)
        self.hint_label = tk.Label(self.selection_frame, font=self.hint_font, fg="#666")
        self.hint_label.grid(row=3, columnspan=4)

    def setup_canvas(self):
        self.canvas = tk.Canvas(self.root, width=300, height=300, bg="white")
        self.canvas.pack(pady=20)
        self.draw_gallows()

    def draw_gallows(self):
        self.canvas.create_line(50, 280, 250, 280, width=5)  # Base
        self.canvas.create_line(150, 280, 150, 50, width=5)  # Pole
        self.canvas.create_line(150, 50, 250, 50, width=5)  # Beam
        self.canvas.create_line(250, 50, 250, 80, width=3)  # Rope

    def draw_hangman(self):
        if self.wrong_attempts >= 1:
            self.canvas.create_oval(225, 80, 275, 130, width=3)  # Head
        if self.wrong_attempts >= 2:
            self.canvas.create_line(250, 130, 250, 200, width=3)  # Body
        if self.wrong_attempts >= 3:
            self.canvas.create_line(250, 150, 200, 100, width=3)  # Left arm
            self.canvas.create_line(250, 150, 300, 100, width=3)  # Right arm
        if self.wrong_attempts >= 4:
            self.canvas.create_line(250, 200, 200, 250, width=3)  # Left leg
            self.canvas.create_line(250, 200, 300, 250, width=3)  # Right leg

    def setup_word_display(self):
        self.word_frame = tk.Frame(self.root)
        self.word_frame.pack(pady=20)
        self.word_labels = []

    def update_word_display(self):
        for label in self.word_labels:
            label.destroy()
        self.word_labels = []

        for char in self.word:
            if char == ' ':
                # Add space separator with extra padding
                lbl = tk.Label(self.word_frame, text="   ", font=("Helvetica", 24))
                lbl.pack(side=tk.LEFT)
                self.word_labels.append(lbl)
            else:
                # Add character/underscore
                text = char if char in self.guessed else "_"
                lbl = tk.Label(self.word_frame, text=text, font=("Helvetica", 24))
                lbl.pack(side=tk.LEFT, padx=2)
                self.word_labels.append(lbl)

    def setup_keyboard(self):
        self.keyboard_frame = tk.Frame(self.root)
        self.keyboard_frame.pack(pady=10)
        rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        self.buttons = {}
        for i, row in enumerate(rows):
            frame = tk.Frame(self.keyboard_frame)
            frame.pack()
            for j, char in enumerate(row):
                btn = tk.Button(frame, text=char, width=3, font=self.button_font,
                                command=lambda c=char: self.process_guess(c))
                btn.pack(side=tk.LEFT, padx=2, pady=2)
                self.buttons[char] = btn

    def process_guess(self, char):
        self.buttons[char].config(state=tk.DISABLED)
        if char in self.word:
            self.buttons[char].config(bg="#4CAF50", fg="white")
            self.guessed.append(char)
            self.update_word_display()
            self.check_game_status()
        else:
            self.buttons[char].config(bg="#f44336", fg="white")
            self.wrong_attempts += 1
            self.draw_hangman()
            self.check_game_status()

    def start_game(self):
        # Hide selections and show hint
        self.selection_frame.pack_forget()
        self.start_btn.config(state=tk.DISABLED)

        # Fetch word from DB
        self.word, self.hint = self.get_random_word()
        if not self.word:
            messagebox.showerror("Error", "No words found in database!")
            return

        # Auto-add spaces to guessed letters
        self.guessed = [c for c in self.word if c == ' ']

        # Update UI
        self.hint_label.config(text=f"Hint: {self.hint}")
        self.selection_frame.pack(pady=10)

        # Reset game state
        self.wrong_attempts = 0
        self.canvas.delete("all")
        self.draw_gallows()
        self.update_word_display()
        self.reset_keyboard()

        # Start timer
        self.timer_label.config(text="Time: 0")
        if self.diff_var.get() in ["Medium", "Hard"]:
            self.time_left = 45 if self.diff_var.get() == "Medium" else 30
            self.timer_label.config(text=f"Time: {self.time_left}")
            self.update_timer()

    def get_random_word(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            query = """SELECT word, hint FROM words 
                       WHERE difficulty=%s AND category=%s 
                       ORDER BY RAND() LIMIT 1"""
            cursor.execute(query, (self.diff_var.get(), self.cat_var.get()))
            result = cursor.fetchone()
            return (result[0].upper(), result[1]) if result else (None, None)
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
            return (None, None)
        finally:
            if 'conn' in locals() and conn.is_connected():
                conn.close()

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=f"Time: {self.time_left}")
            self.timer_id = self.root.after(1000, self.update_timer)
        else:
            self.game_over(loss=True)

    def check_game_status(self):
        if all(letter in self.guessed or letter == ' ' for letter in self.word):
            self.game_over(win=True)
        elif self.wrong_attempts >= self.max_attempts:
            self.game_over(loss=True)

    def game_over(self, win=False, loss=False):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        msg = ""
        if win:
            self.score += 10
            self.streak += 1
            msg = "You won!"
        if loss:
            self.streak = 0
            msg = f"Game Over! Word was: {self.word}"

        self.high_score = max(self.score, self.high_score)
        self.update_scores()

        if messagebox.askyesno("Game Over", f"{msg} Play again?"):
            self.reset_game()
        else:
            self.root.destroy()

    def reset_game(self):
        self.reset_keyboard()
        self.canvas.delete("all")
        self.draw_gallows()
        self.selection_frame.pack(pady=10)
        self.start_btn.config(state=tk.NORMAL)
        self.hint_label.config(text="")
        self.timer_label.config(text="Time: 0")
        self.update_word_display()

    def reset_keyboard(self):
        for btn in self.buttons.values():
            btn.config(state=tk.NORMAL, bg="SystemButtonFace", fg="black")

    def update_scores(self):
        self.score_label.config(text=f"Score: {self.score}")
        self.high_score_label.config(text=f"High Score: {self.high_score}")
        self.streak_label.config(text=f"Streak: {self.streak}")


if __name__ == "__main__":
    root = tk.Tk()
    game = HangmanGame(root)
    root.mainloop()