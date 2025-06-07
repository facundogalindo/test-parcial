#!/usr/bin/env python3
"""
read_highlighted_questions.py

Script para cargar preguntas de un archivo Word (.docx) donde la(s) respuesta(s) correcta(s) está(n) resaltada(s) en amarillo,
y simular una evaluación GUI mejorada con progreso y desactivación de opciones tras verificar.

Uso:
  python read_highlighted_questions.py -i preguntas.docx

Dependencias:
  pip install python-docx
"""
import re
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from docx import Document
from docx.enum.text import WD_COLOR_INDEX


def select_file():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Seleccionar archivo de preguntas",
        filetypes=[("Archivos Word", "*.docx")]
    )
    root.destroy()
    return path


def load_questions(path):
    doc = Document(path)
    questions = []
    paras = doc.paragraphs
    idx = 0
    while idx < len(paras):
        text = paras[idx].text.strip()
        m_q = re.match(r"^(\d+)\.\s*(.+)$", text)
        if m_q:
            num = int(m_q.group(1))
            q_text = m_q.group(2)
            q = {'number': num, 'question': q_text, 'type': None, 'options': [], 'answers': []}
            idx += 1
            while idx < len(paras):
                line = paras[idx].text.strip()
                if re.match(r"^(\d+)\.\s*", line): break
                highlighted = any(run.font.highlight_color == WD_COLOR_INDEX.YELLOW for run in paras[idx].runs)
                m_opt = re.match(r"^([A-Z])\.\s*(.+)$", line)
                if m_opt:
                    q['type'] = 'MC'
                    letter, text_opt = m_opt.group(1), m_opt.group(2)
                    q['options'].append({'letter': letter, 'text': text_opt})
                    if highlighted: q['answers'].append(letter)
                elif line.lower() in ('verdadero', 'falso'):
                    q['type'] = 'VF'
                    q['options'].append({'text': line})
                    if highlighted: q['answers'].append(line)
                idx += 1
            questions.append(q)
        else:
            idx += 1
    return sorted(questions, key=lambda x: x['number'])


def ask_question(q, correct_count, incorrect_count):
    result = {'correct': False}
    root = tk.Tk()
    root.title(f"Pregunta {q['number']}  (Bien: {correct_count}  Mal: {incorrect_count})")
    root.geometry('500x350')
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except:
        pass

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)

    # Pregunta
    q_label = ttk.Label(frame, text=q['question'], wraplength=460, justify='left', font=('Segoe UI', 11, 'bold'))
    q_label.pack(pady=(0,10))

    # Progreso
    prog_label = ttk.Label(frame, text=f"Progreso - Bien: {correct_count} | Mal: {incorrect_count}", font=('Segoe UI', 10))
    prog_label.pack(pady=(0,15))

    option_widgets = []
    if q['type'] == 'MC':
        vars = {}
        for opt in q['options']:
            v = tk.BooleanVar(value=False)
            vars[opt['letter']] = v
            cb = ttk.Checkbutton(frame, text=f"{opt['letter']}. {opt['text']}", variable=v)
            cb.pack(anchor='w', pady=3)
            option_widgets.append(cb)
    else:
        var = tk.StringVar(value="")
        for opt in q['options']:
            rb = ttk.Radiobutton(frame, text=opt['text'], variable=var, value=opt['text'])
            rb.pack(anchor='w', pady=3)
            option_widgets.append(rb)

    def disable_options():
        for w in option_widgets:
            w.state(['disabled'])
        verify_btn.state(['disabled'])

    def check_answer():
        disable_options()
        if q['type'] == 'MC':
            selected = [lt for lt, v in vars.items() if v.get()]
            if not selected:
                messagebox.showwarning("Atención", "Seleccione al menos una opción.")
                return
            correct_set = set(q['answers'])
            if set(selected) == correct_set:
                messagebox.showinfo("Resultado", "¡Correcto!")
                result['correct'] = True
            else:
                corr = ", ".join(sorted(correct_set))
                messagebox.showinfo("Resultado", f"Incorrecto. Respuestas: {corr}.")
                result['correct'] = False
        else:
            sel = var.get()
            if not sel:
                messagebox.showwarning("Atención", "Seleccione Verdadero o Falso.")
                return
            correct = q['answers'][0]
            if sel == correct:
                messagebox.showinfo("Resultado", "¡Correcto!")
                result['correct'] = True
            else:
                messagebox.showinfo("Resultado", f"Incorrecto. La respuesta correcta: {correct}.")
                result['correct'] = False
        root.after(200, root.destroy)

    verify_btn = ttk.Button(frame, text="Verificar", command=check_answer)
    verify_btn.pack(pady=15)
    root.mainloop()
    return result['correct']


def main():
    parser = argparse.ArgumentParser(description='Simular evaluación desde Word con GUI mejorada')
    parser.add_argument('-i', '--input', help='Archivo .docx con preguntas resaltadas')
    args = parser.parse_args()

    path = args.input or select_file()
    if not path:
        return
    qs = load_questions(path)
    good = bad = 0
    for q in qs:
        if ask_question(fq, good, bad): good += 1
        else: bad += 1
    messagebox.showinfo("Fin", f"Total: {len(qs)}\nCorrectas: {good}\nIncorrectas: {bad}")

if __name__ == '__main__':
    main()
