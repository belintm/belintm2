#!/usr/bin/env python3
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

INPUT_DIR = "input"
OUTPUT_DIR = "output"


def extract_uid_from_gbx(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        match = re.search(rb"[A-Za-z0-9_-]{20,35}", data)
        if match:
            return match.group(0).decode("utf-8", errors="ignore")
    except Exception:
        pass
    return None


def create_matchsettings_file(maps, output_path):
    playlist = ET.Element("playlist")
    gameinfos = ET.SubElement(playlist, "gameinfos")
    ET.SubElement(gameinfos, "game_mode").text = "0"
    ET.SubElement(gameinfos, "script_name").text = "TimeAttack.Script.txt"
    ET.SubElement(gameinfos, "title").text = "TMStadium@nadeo"
    ET.SubElement(gameinfos, "chat_time").text = "0"
    ET.SubElement(gameinfos, "finishtimeout").text = "1"
    ET.SubElement(gameinfos, "allwarmupduration").text = "0"
    ET.SubElement(gameinfos, "disablerespawn").text = "0"
    ET.SubElement(gameinfos, "forceshowallopponents").text = "0"

    filter_elem = ET.SubElement(playlist, "filter")
    ET.SubElement(filter_elem, "is_lan").text = "1"
    ET.SubElement(filter_elem, "is_internet").text = "1"
    ET.SubElement(filter_elem, "is_solo").text = "0"
    ET.SubElement(filter_elem, "is_hotseat").text = "0"
    ET.SubElement(filter_elem, "sort_index").text = "1000"
    ET.SubElement(filter_elem, "random_map_order").text = "0"

    mode_settings = ET.SubElement(playlist, "mode_script_settings")
    ET.SubElement(mode_settings, "setting", name="S_TimeLimit", type="integer", value="1200")
    ET.SubElement(mode_settings, "setting", name="S_ForceLapsNb", type="integer", value="-1")

    ET.SubElement(playlist, "startindex").text = "0"

    for file_path, uid in maps:
        map_elem = ET.SubElement(playlist, "map")
        ET.SubElement(map_elem, "file").text = file_path
        ET.SubElement(map_elem, "ident").text = uid or "UNKNOWN_UID"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    xml_str = minidom.parseString(ET.tostring(playlist, encoding="utf-8")).toprettyxml(indent="\t", encoding="utf-8")
    with open(output_path, "wb") as f:
        f.write(xml_str)
    print(f"✅ Matchsetting créé : {output_path} ({len(maps)} maps)")


class MatchWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trackmania² MatchSettings Wizard")
        self.geometry("700x500")

        self.folders = {}
        self.current_index = 0
        self.selections = {}
        self.all_maps = []
        self.load_maps()
        self.create_folder_ui()

    def load_maps(self):
        if not os.path.exists(INPUT_DIR):
            os.makedirs(INPUT_DIR)
        for folder in sorted(os.listdir(INPUT_DIR)):
            folder_path = os.path.join(INPUT_DIR, folder)
            if not os.path.isdir(folder_path):
                continue
            maps = []
            for file in sorted(os.listdir(folder_path)):
                if file.lower().endswith(".gbx"):
                    full_path = os.path.join(folder_path, file)
                    uid = extract_uid_from_gbx(full_path)
                    relative = f"{folder}/{file}"
                    maps.append((relative, uid))
                    self.all_maps.append((relative, uid))
            if maps:
                self.folders[folder] = maps

    # --- Vérification chemins ---
    def check_invalid_paths(self, paths):
        invalid = [p for p in paths if "'" in p or '"' in p]
        if invalid:
            messagebox.showerror(
                "Erreur de chemin",
                "Les chemins suivants contiennent des caractères interdits (\' ou \") :\n\n" +
                "\n".join(invalid)
            )
            return False
        return True

    # --- Parcours des dossiers ---
    def create_folder_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        if self.current_index >= len(self.folders):
            self.create_global_ui()
            return

        folder = list(self.folders.keys())[self.current_index]
        maps = self.folders[folder]

        tk.Label(self, text=f"Sélection des maps pour : {folder}", font=("Arial", 13, "bold")).pack(pady=10)

        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self, text="Tout sélectionner / Tout désélectionner", command=lambda: self.toggle_all(self.map_vars)).pack(pady=5)

        self.map_vars = {}
        for path, _ in maps:
            var = tk.BooleanVar(value=True)
            self.map_vars[path] = var
            ttk.Checkbutton(scroll_frame, text=path.split("/")[-1], variable=var).pack(anchor="w", padx=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(self, text="Suivant →", command=self.next_folder).pack(pady=10)

    def toggle_all(self, var_dict):
        all_selected = all(v.get() for v in var_dict.values())
        for v in var_dict.values():
            v.set(not all_selected)

    def next_folder(self):
        folder = list(self.folders.keys())[self.current_index]
        selected = [p for p, v in self.map_vars.items() if v.get()]
        if selected:
            if not self.check_invalid_paths(selected):
                return
            self.selections[folder] = selected
            maps = [(p, self._find_uid(p)) for p in selected]
            out_path = os.path.join(OUTPUT_DIR, f"{folder}_all.txt")
            create_matchsettings_file(maps, out_path)
        self.current_index += 1
        self.create_folder_ui()

    # --- Matchsetting global ---
    def create_global_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Sélection des maps pour le matchsetting GLOBAL :", font=("Arial", 13, "bold")).pack(pady=10)

        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self, text="Tout sélectionner / Tout désélectionner", command=lambda: self.toggle_all(self.global_vars)).pack(pady=5)

        self.global_vars = {}
        for path, _ in self.all_maps:
            var = tk.BooleanVar(value=True)
            self.global_vars[path] = var
            ttk.Checkbutton(scroll_frame, text=path.split("/")[-1], variable=var).pack(anchor="w", padx=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(self, text="Créer le matchsetting GLOBAL", command=self.create_global_and_custom).pack(pady=10)

    def create_global_and_custom(self):
        selected = [p for p, v in self.global_vars.items() if v.get()]
        if selected:
            if not self.check_invalid_paths(selected):
                return
            maps = [(p, self._find_uid(p)) for p in selected]
            out_path = os.path.join(OUTPUT_DIR, "btc_all.txt")
            create_matchsettings_file(maps, out_path)
        self.ask_custom_creation()

    # --- Matchsettings personnalisés ---
    def ask_custom_creation(self):
        for widget in self.winfo_children():
            widget.destroy()

        label = tk.Label(self, text="Souhaitez-vous créer un matchsetting personnalisé ?", font=("Arial", 13))
        label.pack(pady=20)

        ttk.Button(self, text="Oui", command=self.create_custom_ui).pack(pady=5)
        ttk.Button(self, text="Non", command=self.quit).pack(pady=5)

    def create_custom_ui(self):
        self.show_custom_selection_ui()

    def show_custom_selection_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Sélectionnez les maps pour le matchsetting personnalisé :", font=("Arial", 13, "bold")).pack(pady=10)

        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self, text="Tout sélectionner / Tout désélectionner", command=lambda: self.toggle_all(self.custom_vars)).pack(pady=5)

        self.custom_vars = {}
        for folder, maps in self.folders.items():
            ttk.Label(scroll_frame, text=f"[{folder}]", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 0))
            for path, _ in maps:
                var = tk.BooleanVar(value=False)
                self.custom_vars[path] = var
                ttk.Checkbutton(scroll_frame, text=path.split("/")[-1], variable=var).pack(anchor="w", padx=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(self, text="Créer le matchsetting personnalisé", command=self.create_custom_and_ask_again).pack(pady=10)

    def create_custom_and_ask_again(self):
        selected = [p for p, v in self.custom_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Aucune map", "Veuillez sélectionner au moins une map.")
            return
        if not self.check_invalid_paths(selected):
            return

        name = simpledialog.askstring("Nom du matchsetting", "Entrez un nom pour ce matchsetting :", initialvalue="custom")
        if not name:
            return

        maps = [(p, self._find_uid(p)) for p in selected]
        out_path = os.path.join(OUTPUT_DIR, f"{name}.txt")
        create_matchsettings_file(maps, out_path)
        messagebox.showinfo("Succès", f"Matchsetting '{name}.txt' créé !")

        again = messagebox.askyesno("Créer un autre ?", "Voulez-vous créer un autre matchsetting personnalisé ?")
        if again:
            self.show_custom_selection_ui()
        else:
            self.quit()

    def _find_uid(self, path):
        for folder_maps in self.folders.values():
            for p, uid in folder_maps:
                if p == path:
                    return uid
        return None


if __name__ == "__main__":
    app = MatchWizard()
    app.mainloop()
