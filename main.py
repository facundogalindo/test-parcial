#!/usr/bin/env python3
"""
Proyecto de Práctica de Exámenes – PyCharm

Script para:
  - Pantalla de bienvenida con botón sobre imagen
  - Cargar preguntas resaltadas de archivos Word (.docx) de las Unidades 1,2,3
  - Seleccionar cuántas preguntas usar de cada unidad
  - Mostrar cuestionario con GUI Tkinter:
      * Ventana dimensionada al contenido
      * Barra de progreso
      * Teclas rápidas (V/F para VF, 1-4 para MC, Enter verificar)
      * Feedback visual con imágenes precargadas de éxito/fracaso
      * Botón “Salir” para terminar la aplicación en cualquier momento

Para generar el .exe con ícono personalizado, usa:
    pyinstaller --onefile --windowed \
        --add-data "Img;Img" \
        --add-data "Practica;Practica" \
        --icon "Img/icono.ico" \
        main.py
"""
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
import random


def load_questions(path):
    doc = Document(path)
    qs = []
    paras = doc.paragraphs
    idx = 0
    while idx < len(paras):
        line = paras[idx].text.strip()
        m = re.match(r"^(\d+)\.\s*(.+)$", line)
        if m:
            q = {'question': m.group(2), 'type': None, 'options': [], 'answers': []}
            idx += 1
            while idx < len(paras):
                text = paras[idx].text.strip()
                if re.match(r"^(\d+)\.\s*", text):
                    break
                hl = any(run.font.highlight_color == WD_COLOR_INDEX.YELLOW for run in paras[idx].runs)
                mc = re.match(r"^([A-Z])[\.\)]\s*(.+)$", text)
                if mc:
                    q['type'] = 'MC'
                    letter, txt = mc.group(1), mc.group(2)
                    q['options'].append((letter, txt))
                    if hl:
                        q['answers'].append(letter)
                elif text.lower() in ('verdadero', 'falso'):
                    q['type'] = 'VF'
                    q['options'].append((text,))
                    if hl:
                        q['answers'].append(text)
                idx += 1
            qs.append(q)
        else:
            idx += 1
    return qs


def ask_question(root, q, idx, total, good, bad, img_ok, img_ko):
    win = tk.Toplevel(root)
    win.title(f"Pregunta {idx}/{total}  Bien: {good}  Mal: {bad}")
    ttk.Style(win).theme_use('clam')

    frame = ttk.Frame(win, padding=20)
    frame.pack(fill='both', expand=True)

    # Barra de progreso
    pb = ttk.Progressbar(frame, length=400, mode='determinate', maximum=total)
    pb['value'] = idx - 1
    pb.pack(pady=(0, 10))

    ttk.Label(frame, text=q['question'], wraplength=600,
              font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))

    widgets = []
    vars_mc = {}
    var_vf = tk.StringVar(value="")

    if q['type'] == 'MC':
        for letter, txt in q['options']:
            v = tk.BooleanVar()
            vars_mc[letter] = v
            cb = ttk.Checkbutton(frame, text=f"{letter}. {txt}", variable=v)
            cb.pack(anchor='w', pady=3)
            widgets.append(cb)
    else:
        for (opt,) in q['options']:
            rb = ttk.Radiobutton(frame, text=opt, variable=var_vf, value=opt)
            rb.pack(anchor='w', pady=3)
            widgets.append(rb)

    img_label = None
    if img_ok and img_ko:
        img_label = ttk.Label(frame)
        img_label.pack(pady=10)

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=10)
    btn_ver = ttk.Button(btn_frame, text="Verificar")
    btn_skip = ttk.Button(btn_frame, text="Siguiente")
    btn_exit = ttk.Button(btn_frame, text="Salir", command=lambda: os._exit(0))
    btn_skip.state(['disabled'])
    btn_ver.pack(side='left', padx=5)
    btn_exit.pack(side='left', padx=5)
    btn_skip.pack(side='right', padx=5)

    def disable_all():
        for w in widgets:
            w.state(['disabled'])
        btn_ver.state(['disabled'])
        btn_skip.state(['!disabled'])

    def show_feedback(correct):
        if img_label:
            img = img_ok if correct else img_ko
            img_label.config(image=img)
            img_label.image = img
        else:
            msg = "¡Correcto!" if correct else f"Incorrecto. Respuestas correctas: {', '.join(q['answers'])}"
            messagebox.showinfo("Resultado", msg, parent=win)

    result = False

    def verify():
        nonlocal result
        if q['type'] == 'MC':
            sel = [l for l, v in vars_mc.items() if v.get()]
            if not sel:
                messagebox.showwarning("Atención", "Seleccione al menos una opción.", parent=win)
                return
            result = set(sel) == set(q['answers'])
        else:
            sel = var_vf.get()
            if not sel:
                messagebox.showwarning("Atención", "Seleccione Verdadero o Falso.", parent=win)
                return
            result = (sel == q['answers'][0])
        disable_all()
        show_feedback(result)

    def on_key(e):
        c = e.char.lower()
        if q['type'] == 'VF':
            if c == 'v': var_vf.set('Verdadero')
            if c == 'f': var_vf.set('Falso')
        else:
            for i, (letter, _) in enumerate(q['options'], start=1):
                if str(i) == c:
                    vars_mc[letter].set(not vars_mc[letter].get())
        if e.keysym == 'Return':
            verify()

    btn_ver.config(command=verify)
    btn_skip.config(command=win.destroy)
    win.bind('<Key>', on_key)

    win.update_idletasks()
    win.minsize(win.winfo_width(), win.winfo_height())
    win.resizable(False, False)
    win.grab_set()
    win.wait_window()
    return result


def main():
    # Ventana de bienvenida
    welcome = tk.Tk()
    welcome.title("Bienvenido")

    try:
        pil_img = Image.open(os.path.join("Img", "simulacro para joyitas.png"))
        sw, sh = welcome.winfo_screenwidth(), welcome.winfo_screenheight()
        pil_img.thumbnail((int(sw*0.8), int(sh*0.8)), Image.Resampling.LANCZOS)
        bg_img = ImageTk.PhotoImage(pil_img, master=welcome)
        canvas = tk.Canvas(welcome, width=bg_img.width(), height=bg_img.height(), highlightthickness=0)
        canvas.create_image(0, 0, anchor='nw', image=bg_img)
        btn_start = tk.Button(canvas, text="Comenzar", command=welcome.destroy)
        canvas.create_window(bg_img.width()//2, bg_img.height()-30, window=btn_start)
        canvas.pack()
    except Exception as e:
        print(f"Error cargando imagen de bienvenida: {e}")
        btn_start = tk.Button(welcome, text="Comenzar", command=welcome.destroy)
        btn_start.pack(padx=20, pady=20)

    welcome.resizable(False, False)
    welcome.mainloop()

    # Ventana de carga de unidades
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.title("Carga de Unidades")
    root.geometry('800x600')

    try:
        img_ok = ImageTk.PhotoImage(Image.open("Img/joya.jpg"), master=root)
        img_ko = ImageTk.PhotoImage(Image.open("Img/joyita.jpg"), master=root)
    except Exception:
        img_ok = img_ko = None

    selections = {}
    for u in (1, 2, 3):
        frm = ttk.Frame(root, padding=10)
        frm.pack(fill='x')
        ttk.Label(frm, text=f"Unidad {u}:").pack(side='left')
        btn_load = ttk.Button(
            frm, text="Cargar archivo",
            command=lambda u=u: selections.setdefault(u,
                filedialog.askopenfilename(
                    title=f"Cargar Unidad {u}", initialdir="Practica",
                    filetypes=[("Word", "*.docx")], master=root)))
        btn_load.pack(side='left', padx=5)

    main_btns = ttk.Frame(root)
    main_btns.pack(pady=20)
    ttk.Button(main_btns, text="Continuar", command=root.quit).pack(side='left', padx=5)
    ttk.Button(main_btns, text="Salir", command=lambda: os._exit(0)).pack(side='left', padx=5)

    root.mainloop()
    root.withdraw()

    counts = {}
    for u, path in selections.items():
        if path:
            cnt = simpledialog.askinteger(
                "Cantidad", f"¿Cuántas preguntas de Unidad {u}?", minvalue=1, maxvalue=100, parent=root)
            counts[u] = cnt

    all_qs = []
    for u, c in counts.items():
        qs = load_questions(selections[u])
        random.shuffle(qs)
        all_qs.extend(qs[:c])
    random.shuffle(all_qs)

    good = bad = 0
    total = len(all_qs)
    for i, q in enumerate(all_qs, start=1):
        if ask_question(root, q, i, total, good, bad, img_ok, img_ko):
            good += 1
        else:
            bad += 1

    messagebox.showinfo(
        "Resultados",
        f"Total: {total}\nBien: {good}\nMal: {bad}",
        parent=root
    )


if __name__ == '__main__':
    main()