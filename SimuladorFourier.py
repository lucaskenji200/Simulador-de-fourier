import tkinter as tk
from tkinter import messagebox, filedialog 
import sympy
from sympy import (
    symbols, integrate, sympify, lambdify,
    sin as sympy_sin, cos as sympy_cos, pi as sympy_pi,
    exp as sympy_exp, Abs as sympy_Abs, sqrt as sympy_sqrt,
    E as sympy_E, log as sympy_log,
    Piecewise, Add, S
)
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import traceback
import os
import io                 
from PIL import Image     

# ... (o resto do código inicial permanece o mesmo) ...

# Configuração inicial
x = symbols('x')
lista_de_funcoes_widgets = []
limitantes_widgets = []
max_funcoes = 5
MAX_N_TERMS = 100

# Dicionários para conversão de funções
SYMPY_LOCALS = {
    "x": x, "pi": sympy_pi, "e": sympy_E,
    "sin": sympy_sin, "sen": sympy_sin,
    "cos": sympy_cos, "exp": sympy_exp,
    "sqrt": sympy_sqrt, "raiz": sympy_sqrt,
    "Abs": sympy_Abs, "abs": sympy_Abs,
    "log": sympy_log, "ln": sympy_log,
}

NUMPY_MODULES = [
    'numpy',
    {
        'sin': np.sin, 'sen': np.sin, 'cos': np.cos,
        'Abs': np.abs, 'abs': np.abs, 'exp': np.exp,
        'sqrt': np.sqrt, 'raiz': np.sqrt,
        'log': np.log, 'ln': np.log, 'E': np.e, 'pi': np.pi
    }
]

# Cache para coeficientes
fourier_cache = {
    "signature": None,
    "a0": None,
    "an_coeffs": None,
    "bn_coeffs": None,
    "L": None,
    "A": None,
    "B": None,
    "lambdified_original_func": None,
    "x_plot_base": None
}

# Variáveis globais
last_plotted_y_fourier = None
is_animating_flag = False
animation_job_id = None
NUM_ANIMATION_FRAMES = 10
ANIMATION_DELAY_MS = 20
recalc_timer_id = None
app_running = True

def on_closing():
    global app_running
    app_running = False
    if animation_job_id:
        try: j.after_cancel(animation_job_id)
        except tk.TclError: pass
    if recalc_timer_id:
        try: j.after_cancel(recalc_timer_id)
        except tk.TclError: pass
    j.quit()
    j.destroy()

# Criação da janela principal
j = tk.Tk()
j.title("Simulador de Séries de Fourier")
j.configure(bg="#1e1e1e")
j.geometry("1250x650")
j.protocol("WM_DELETE_WINDOW", on_closing)

# Frame de entrada
input_frame = tk.Frame(j, bg="#1e1e1e")
input_frame.place(x=10, y=10, width=430, height=630)

# Rótulos
tk.Label(input_frame, text="f(x)", font=("Arial", 12), bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=5, pady=2, sticky="w")
tk.Label(input_frame, text="Início", font=("Arial", 12), bg="#1e1e1e", fg="white").grid(row=0, column=1, padx=5, pady=2, sticky="w")
tk.Label(input_frame, text="Fim", font=("Arial", 12), bg="#1e1e1e", fg="white").grid(row=0, column=3, padx=5, pady=2, sticky="w")

# Frame dinâmico para entradas
dynamic_input_frame = tk.Frame(input_frame, bg="#1e1e1e")
dynamic_input_frame.grid(row=1, column=0, columnspan=5, sticky="ew")

def criar_novo_input_widgets(master_frame, index):
    func_entry = tk.Entry(master_frame, font=("Arial", 12), width=20, bg="#3c3c3c", fg="white", insertbackground="white")
    func_entry.grid(row=index, column=0, padx=5, pady=3, sticky="ew")

    min_entry = tk.Entry(master_frame, font=("Arial", 12), width=6, bg="#3c3c3c", fg="white", insertbackground="white")
    min_entry.grid(row=index, column=1, padx=(5,0), pady=3, sticky="ew")

    tk.Label(master_frame, text="a", font=("Arial", 12), bg="#1e1e1e", fg="white").grid(row=index, column=2, padx=(0,5), pady=3)

    max_entry = tk.Entry(master_frame, font=("Arial", 12), width=6, bg="#3c3c3c", fg="white", insertbackground="white")
    max_entry.grid(row=index, column=3, padx=5, pady=3, sticky="ew")

    func_entry.bind("<KeyRelease>", lambda event: agendar_recalculo(triggered_by_slider=False))
    min_entry.bind("<KeyRelease>", lambda event: agendar_recalculo(triggered_by_slider=False))
    max_entry.bind("<KeyRelease>", lambda event: agendar_recalculo(triggered_by_slider=False))

    return func_entry, min_entry, max_entry

def adicionar_campos_funcao():
    if len(lista_de_funcoes_widgets) >= max_funcoes:
        button_add_func.config(state=tk.DISABLED)
        return

    idx = len(lista_de_funcoes_widgets)
    func_entry, min_entry, max_entry = criar_novo_input_widgets(dynamic_input_frame, idx)

    lista_de_funcoes_widgets.append(func_entry)
    limitantes_widgets.append((min_entry, max_entry))

    if len(lista_de_funcoes_widgets) == max_funcoes:
        button_add_func.config(state=tk.DISABLED)

# Primeira linha de entrada
func_e, min_e, max_e = criar_novo_input_widgets(dynamic_input_frame, 0)
lista_de_funcoes_widgets.append(func_e)
limitantes_widgets.append((min_e, max_e))

# Botão para adicionar mais funções
button_add_func = tk.Button(dynamic_input_frame, text="+", font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", command=adicionar_campos_funcao, width=2, relief=tk.FLAT)
button_add_func.grid(row=0, column=4, padx=5, pady=3, sticky="w")

# Controle deslizante para número de termos
current_row_after_inputs = max_funcoes + 1
tk.Label(input_frame, text="Número de termos (n)", font=("Arial", 12), bg="#1e1e1e", fg="white").grid(row=current_row_after_inputs, column=0, columnspan=4, padx=5, pady=(15,2), sticky="w")
n_slider = tk.Scale(input_frame, from_=1, to=MAX_N_TERMS, orient="horizontal", length=380, resolution=1, bg="#1e1e1e", fg="white", troughcolor="#555555", highlightthickness=0)
n_slider.set(10)
n_slider.grid(row=current_row_after_inputs + 1, column=0, columnspan=5, padx=5, pady=2, sticky="ew")

# Labels informativos
L_label_var = tk.StringVar()
L_label = tk.Label(input_frame, textvariable=L_label_var, font=("Arial", 10), bg="#1e1e1e", fg="#cccccc", justify=tk.LEFT, wraplength=400)
L_label.grid(row=current_row_after_inputs + 2, column=0, columnspan=5, padx=5, pady=5, sticky="w")

error_message_var = tk.StringVar()
error_label = tk.Label(input_frame, textvariable=error_message_var, font=("Arial", 10, "italic"), bg="#1e1e1e", fg="red", justify=tk.LEFT, wraplength=400)
error_label.grid(row=current_row_after_inputs + 3, column=0, columnspan=5, padx=5, pady=5, sticky="w")

def salvar_animacao_gif():
    """Gera uma animação variando n de 1 a 100 e a salva como um arquivo GIF."""
    # 1. Validar se os coeficientes já foram calculados
    if fourier_cache["signature"] is None:
        messagebox.showerror("Erro", "Calcule uma série de Fourier primeiro antes de salvar a animação.")
        return

    # 2. Abrir janela para o usuário escolher onde salvar o arquivo
    filepath = filedialog.asksaveasfilename(
        defaultextension=".gif",
        filetypes=[("GIF files", "*.gif"), ("All files", "*.*")],
        title="Salvar Animação GIF"
    )
    if not filepath: # Se o usuário cancelar a janela
        return

    save_animation_button.config(state=tk.DISABLED)
    status_message_var.set("Iniciando a geração do GIF...")
    j.update_idletasks()
    
    frames = [] # Lista para armazenar cada quadro da animação na memória
    
    try:
        # 3. Obter dados do cache que não mudam no loop
        x_vals = fourier_cache["x_plot_base"]
        y_original_vals = fourier_cache["lambdified_original_func"](x_vals)
        L_val, A_val, B_val = fourier_cache["L"], fourier_cache["A"], fourier_cache["B"]

        # 4. Loop de 1 a 100 para gerar cada quadro
        for n_val in range(1, 101):
            status_message_var.set(f"Gerando quadro {n_val}/100...")
            j.update_idletasks() # Mantém a interface responsiva

            # Calcular a série para o n atual
            f_series_expr = construct_fourier_series_expr_from_cache(n_val, x)
            f_series_numeric = lambdify(x, f_series_expr, modules=NUMPY_MODULES, cse=True)
            y_fourier_vals = f_series_numeric(x_vals)

            # Plotar o quadro
            plot_on_canvas(x_vals, y_fourier_vals, y_original_vals, n_val, L_val, A_val, B_val)
            
            # 5. Salvar o quadro em um buffer de memória em vez de um arquivo
            with io.BytesIO() as buf:
                fig.savefig(buf, format='png', dpi=100)
                buf.seek(0)
                # Adicionar o quadro à lista como um objeto de imagem
                img = Image.open(buf)
                frames.append(img.copy()) # .copy() é importante para evitar problemas com o buffer

        # 6. Salvar a lista de quadros como um GIF animado
        status_message_var.set("Salvando o arquivo GIF...")
        j.update_idletasks()
        frames[0].save(
            filepath,
            save_all=True,
            append_images=frames[1:], # Anexa os quadros restantes
            duration=100,             # Duração de cada quadro em milissegundos (100ms = 10 FPS)
            loop=0                    # 0 significa loop infinito
        )
        messagebox.showinfo("Sucesso", f"Animação salva com sucesso em:\n{filepath}")

    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro durante o salvamento do GIF:\n{e}")
        traceback.print_exc()
    finally:
        # 7. Reativar o botão e limpar a mensagem de status
        status_message_var.set("")
        save_animation_button.config(state=tk.NORMAL)


# Posição dos novos widgets
button_row = current_row_after_inputs + 4

# Botão para salvar
save_animation_button = tk.Button(input_frame, text="Salvar Animação (GIF)", 
                                  font=("Arial", 12, "bold"), bg="#007ACC", fg="white", 
                                  command=salvar_animacao_gif, relief=tk.FLAT)
save_animation_button.grid(row=button_row, column=0, columnspan=5, padx=5, pady=(15, 5), sticky="ew")

# Label de Status
status_message_var = tk.StringVar()
status_label = tk.Label(input_frame, textvariable=status_message_var, font=("Arial", 9), bg="#1e1e1e", fg="#00FF00")
status_label.grid(row=button_row + 1, column=0, columnspan=5, padx=5, pady=2, sticky="ew")

# <--- FIM: MUDANÇAS PARA SALVAR GIF --- >


# Configuração do gráfico
fig, ax = plt.subplots(figsize=(7, 5), dpi=100)
plt.style.use('seaborn-v0_8-darkgrid')

fig.patch.set_facecolor('#2a2a2a')
ax.set_facecolor('#333333')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')
ax.xaxis.label.set_color('white')
ax.yaxis.label.set_color('white')
ax.title.set_color('white')
for spine in ax.spines.values():
    spine.set_edgecolor('gray')

canvas = FigureCanvasTkAgg(fig, master=j)
canvas_widget = canvas.get_tk_widget()
canvas_widget.place(x=450, y=20, width=780, height=610)

# Funções auxiliares
def display_error(title, message):
    error_message_var.set(f"{title}: {message}")
    print(f"Error - {title}: {message}")

def clear_error():
    error_message_var.set("")

def verificar_parenteses_balanceados(s: str) -> bool:
    pilha = []
    for char in s:
        if char == '(': pilha.append(char)
        elif char == ')':
            if not pilha: return False
            pilha.pop()
    return not pilha

def build_current_function_signature_str(active_pieces_list, A_calc, B_calc):
    sorted_pieces = sorted([(str(p['expr']), p['a'], p['b']) for p in active_pieces_list], key=lambda item: item[1])
    return f"{str(sorted_pieces)}|A:{A_calc:.4f}|B:{B_calc:.4f}"

def construct_fourier_series_expr_from_cache(num_terms_to_sum, x_sym):
    if fourier_cache["L"] is None or abs(fourier_cache["L"]) < 1e-9:
        return S(fourier_cache["a0"] / 2) if fourier_cache["a0"] is not None else S.Zero

    series = S(fourier_cache["a0"] / 2) if fourier_cache["a0"] is not None else S.Zero

    if fourier_cache["an_coeffs"] is None or fourier_cache["bn_coeffs"] is None:
        return series

    for n_idx in range(1, min(num_terms_to_sum + 1, len(fourier_cache["an_coeffs"]))):
        term = S.Zero
        if n_idx < len(fourier_cache["an_coeffs"]) and fourier_cache["an_coeffs"][n_idx] is not None and abs(fourier_cache["an_coeffs"][n_idx]) > 1e-9:
            term += fourier_cache["an_coeffs"][n_idx] * sympy_cos(n_idx * sympy_pi * x_sym / fourier_cache["L"])
        if n_idx < len(fourier_cache["bn_coeffs"]) and fourier_cache["bn_coeffs"][n_idx] is not None and abs(fourier_cache["bn_coeffs"][n_idx]) > 1e-9:
            term += fourier_cache["bn_coeffs"][n_idx] * sympy_sin(n_idx * sympy_pi * x_sym / fourier_cache["L"])
        series += term
    return series

def plot_on_canvas(x_plot_vals, y_fourier_plot_vals, y_original_plot_vals, n_val, L_val, A_val, B_val, is_anim_frame=False):
    if not app_running: return
    ax.clear()
    ax.axhline(0, color='gray', linewidth=0.7, linestyle='--')
    ax.axvline(0, color='gray', linewidth=0.7, linestyle='--')

    if y_original_plot_vals is not None:
        if not isinstance(y_original_plot_vals, np.ndarray):
            y_original_plot_vals = np.full_like(x_plot_vals, fill_value=y_original_plot_vals)
        ax.plot(x_plot_vals, y_original_plot_vals, label="Original f(x)", color="#FFA500", linestyle="--", linewidth=2.5)

    if y_fourier_plot_vals is not None:
        if not isinstance(y_fourier_plot_vals, np.ndarray):
            y_fourier_plot_vals = np.full_like(x_plot_vals, fill_value=y_fourier_plot_vals)
        series_label = f"Fourier (n={n_val})"
        ax.plot(x_plot_vals, y_fourier_plot_vals, label=series_label, color="#00FFFF", linewidth=1.8)

    title_str = f"Fourier Approximation (L={L_val:.2f})"
    if A_val is not None and B_val is not None:
        title_str += f" on [{A_val:.2f}, {B_val:.2f}]"
    ax.set_title(title_str, fontsize=12, color='white')
    ax.set_xlabel("x", fontsize=10, color='white'); ax.set_ylabel("f(x)", fontsize=10, color='white')

    legend = ax.legend(fontsize=9, facecolor='#444444', edgecolor='gray')
    for text in legend.get_texts():
        text.set_color("white")

    ax.grid(True, linestyle=':', linewidth=0.4, color='gray')

    combined_y_finite = []

    if y_fourier_plot_vals is not None and isinstance(y_fourier_plot_vals, np.ndarray):
        combined_y_finite.extend(y_fourier_plot_vals[np.isfinite(y_fourier_plot_vals)])
    if y_original_plot_vals is not None and isinstance(y_original_plot_vals, np.ndarray):
        combined_y_finite.extend(y_original_plot_vals[np.isfinite(y_original_plot_vals)])

    if len(combined_y_finite) > 0:
        min_y, max_y = np.min(combined_y_finite), np.max(combined_y_finite)
        padding = (max_y - min_y) * 0.1 if abs(max_y - min_y) > 1e-6 else 0.5
        padding = max(padding, 0.1)
        ax.set_ylim(min_y - padding, max_y + padding)
    else:
        ax.set_ylim(-1.5, 1.5)

    try:
        canvas.draw_idle()
    except tk.TclError:
        if app_running: print("TclError during canvas.draw_idle(), likely window closed.")

def _perform_animation_step(current_frame_num, x_anim_vals, y_start_anim, y_target_anim, y_orig_anim, n_slider_target, L_anim, A_anim, B_anim):
    global is_animating_flag, animation_job_id, last_plotted_y_fourier, app_running

    if not is_animating_flag or not app_running:
        is_animating_flag = False
        return

    if current_frame_num > NUM_ANIMATION_FRAMES:
        is_animating_flag = False
        if isinstance(y_target_anim, np.ndarray):
            last_plotted_y_fourier = y_target_anim.copy()
        plot_on_canvas(x_anim_vals, y_target_anim, y_orig_anim, n_slider_target, L_anim, A_anim, B_anim, is_anim_frame=False)
        return

    alpha = current_frame_num / NUM_ANIMATION_FRAMES
    y_interp = (1 - alpha) * y_start_anim + alpha * y_target_anim
    plot_on_canvas(x_anim_vals, y_interp, y_orig_anim, n_slider_target, L_anim, A_anim, B_anim, is_anim_frame=True)

    if app_running:
        try:
            animation_job_id = j.after(ANIMATION_DELAY_MS,
                                     lambda: _perform_animation_step(current_frame_num + 1, x_anim_vals, y_start_anim, y_target_anim, y_orig_anim, n_slider_target, L_anim, A_anim, B_anim))
        except tk.TclError:
            if app_running: print("TclError scheduling next animation frame.")
            is_animating_flag = False

def start_fourier_animation(x_vals_for_anim, y_fourier_start_anim, y_fourier_target_anim, y_original_for_anim, n_target_val, L_for_anim, A_for_anim, B_for_anim):
    global is_animating_flag, animation_job_id
    if not app_running: return

    if animation_job_id:
        try: j.after_cancel(animation_job_id)
        except tk.TclError: pass
    is_animating_flag = True
    _perform_animation_step(1, x_vals_for_anim, y_fourier_start_anim, y_fourier_target_anim, y_original_for_anim, n_target_val, L_for_anim, A_for_anim, B_for_anim)

def calcular_e_plotar(triggered_by_slider_change=False):
    global fourier_cache, last_plotted_y_fourier, is_animating_flag, animation_job_id, app_running

    if not app_running: return
    clear_error()

    if is_animating_flag and not triggered_by_slider_change:
        if animation_job_id:
            try: j.after_cancel(animation_job_id)
            except tk.TclError: pass
        is_animating_flag = False

    try:
        n_terms_from_slider = n_slider.get()
        active_pieces_data = []
        all_limits_for_interval = []

        for idx, func_entry_widget in enumerate(lista_de_funcoes_widgets):
            func_str = func_entry_widget.get().strip()
            min_lim_str = limitantes_widgets[idx][0].get().strip()
            max_lim_str = limitantes_widgets[idx][1].get().strip()

            if not func_str and not min_lim_str and not max_lim_str:
                    continue

            if not func_str:
                display_error("Entrada Incompleta", f"Função faltando para o intervalo [{min_lim_str or '?'}, {max_lim_str or '?'}] na linha {idx+1}.")
                return

            if not verificar_parenteses_balanceados(func_str):
                display_error("Erro de Função", f"Parênteses desbalanceados em '{func_str}' na linha {idx+1}.")
                return

            try:
                if not min_lim_str or not max_lim_str:
                    display_error("Entrada Incompleta", f"Intervalo faltando para '{func_str}' na linha {idx+1}.")
                    return
                a_local, b_local = float(min_lim_str), float(max_lim_str)

                if a_local >= b_local:
                    display_error("Erro de Intervalo", f"Inválido [{a_local}, {b_local}] para '{func_str}'. a < b esperado (linha {idx+1}).")
                    return

                f_expr = sympify(func_str, locals=SYMPY_LOCALS)
                active_pieces_data.append({'expr': f_expr, 'a': a_local, 'b': b_local})
                all_limits_for_interval.extend([a_local, b_local])
            except ValueError:
                display_error("Erro de Entrada", f"Limites de intervalo inválidos para '{func_str}' na linha {idx+1}.")
                return
            except Exception as e_sympify:
                display_error("Erro de Função", f"Erro em '{func_str}': {e_sympify} (linha {idx+1}).")
                return

        if not active_pieces_data:
            ax.clear(); ax.set_title("Nenhuma função válida definida", fontsize=10, color='white')
            ax.text(0.5, 0.5, "Defina f(x) e seu(s) intervalo(s).", ha='center', va='center', transform=ax.transAxes, fontsize=9, color='white')
            L_label_var.set("Defina a(s) função(ões) e o(s) intervalo(s).")
            fourier_cache["signature"] = None; last_plotted_y_fourier = None; canvas.draw_idle(); return

        A_calc, B_calc = min(all_limits_for_interval), max(all_limits_for_interval)

        if abs(A_calc - B_calc) < 1e-9 :
                 display_error("Erro de Intervalo", "O intervalo total de integração é muito pequeno.")
                 return
        T_calc = B_calc - A_calc
        L_calc = T_calc / 2.0
        L_label_var.set(f"Intervalo Total: [{A_calc:.2f}, {B_calc:.2f}],  T = {T_calc:.3f},  L = {L_calc:.3f}")

        new_sig_str = build_current_function_signature_str(active_pieces_data, A_calc, B_calc)

        recalculate_coeffs_and_base = (new_sig_str != fourier_cache["signature"])

        if recalculate_coeffs_and_base:
            if animation_job_id:
                try: j.after_cancel(animation_job_id)
                except tk.TclError: pass
            is_animating_flag = False
            print(f"Recalculando coeficientes e base. Nova assinatura: {new_sig_str}")
            fourier_cache["signature"] = new_sig_str
            fourier_cache["A"], fourier_cache["B"], fourier_cache["L"] = A_calc, B_calc, L_calc
            last_plotted_y_fourier = None

            piecewise_conditions_expressions = []
            for p_data in active_pieces_data:
                eff_a = max(p_data['a'], fourier_cache["A"])
                eff_b = min(p_data['b'], fourier_cache["B"])
                if eff_a < eff_b:
                    condition = (x >= eff_a) & (x <= eff_b)
                    piecewise_conditions_expressions.append((p_data['expr'], condition))

            if not piecewise_conditions_expressions:
                display_error("Erro de Intervalo", "Nenhuma parte da(s) função(ões) está no intervalo total.")
                return

            sympy_total_func = Piecewise(*piecewise_conditions_expressions, (S.Zero, True))
            fourier_cache["lambdified_original_func"] = lambdify(x, sympy_total_func, modules=NUMPY_MODULES, cse=True)

            try:
                if abs(fourier_cache["L"]) < 1e-9:
                    fourier_cache["a0"] = 0.0
                    fourier_cache["an_coeffs"] = [0.0] * (MAX_N_TERMS + 1)
                    fourier_cache["bn_coeffs"] = [0.0] * (MAX_N_TERMS + 1)
                else:
                    integral_a0_sym = integrate(sympy_total_func, (x, fourier_cache["A"], fourier_cache["B"]))
                    val_a0_sym = integral_a0_sym.evalf() if hasattr(integral_a0_sym, 'evalf') else integral_a0_sym
                    fourier_cache["a0"] = float(val_a0_sym / fourier_cache["L"])

                    current_an_coeffs = [0.0] * (MAX_N_TERMS + 1)
                    current_bn_coeffs = [0.0] * (MAX_N_TERMS + 1)

                    for n_idx in range(1, MAX_N_TERMS + 1):
                        integrand_an = sympy_total_func * sympy_cos(n_idx * sympy_pi * x / fourier_cache["L"])
                        integral_an_sym = integrate(integrand_an, (x, fourier_cache["A"], fourier_cache["B"]))
                        val_an_sym = integral_an_sym.evalf() if hasattr(integral_an_sym, 'evalf') else integral_an_sym
                        current_an_coeffs[n_idx] = float(val_an_sym / fourier_cache["L"])

                        integrand_bn = sympy_total_func * sympy_sin(n_idx * sympy_pi * x / fourier_cache["L"])
                        integral_bn_sym = integrate(integrand_bn, (x, fourier_cache["A"], fourier_cache["B"]))
                        val_bn_sym = integral_bn_sym.evalf() if hasattr(integral_bn_sym, 'evalf') else integral_bn_sym
                        current_bn_coeffs[n_idx] = float(val_bn_sym / fourier_cache["L"])
                    
                    fourier_cache["an_coeffs"] = current_an_coeffs
                    fourier_cache["bn_coeffs"] = current_bn_coeffs

            except Exception as e_coeff_calc:
                display_error("Erro nos Coeficientes", f"Erro ao calcular: {e_coeff_calc}")
                fourier_cache["signature"] = None; return

            plot_range_extension = (fourier_cache["B"] - fourier_cache["A"]) * 0.5
            x_min_plot = fourier_cache["A"] - plot_range_extension
            x_max_plot = fourier_cache["B"] + plot_range_extension
            fourier_cache["x_plot_base"] = np.linspace(x_min_plot, x_max_plot, 700)

        if any(fourier_cache[key] is None for key in ["a0", "an_coeffs", "bn_coeffs", "lambdified_original_func", "x_plot_base", "L", "A", "B"]):
            ax.clear(); ax.set_title("Erro: Dados para plotagem incompletos.", fontsize=10, color='white'); canvas.draw_idle()
            return

        f_series_expr_target = construct_fourier_series_expr_from_cache(n_terms_from_slider, x)
        f_series_numeric_target = lambdify(x, f_series_expr_target, modules=NUMPY_MODULES, cse=True)

        y_fourier_target_vals = f_series_numeric_target(fourier_cache["x_plot_base"])
        y_original_plot_vals = fourier_cache["lambdified_original_func"](fourier_cache["x_plot_base"])

        can_animate = (triggered_by_slider_change and
                           last_plotted_y_fourier is not None and
                           isinstance(last_plotted_y_fourier, np.ndarray) and
                           len(last_plotted_y_fourier) == len(y_fourier_target_vals))

        if can_animate:
            start_fourier_animation(fourier_cache["x_plot_base"], last_plotted_y_fourier.copy(),
                                     y_fourier_target_vals, y_original_plot_vals, n_terms_from_slider,
                                     fourier_cache["L"], fourier_cache["A"], fourier_cache["B"])
        else:
            if animation_job_id:
                try: j.after_cancel(animation_job_id)
                except tk.TclError: pass
            is_animating_flag = False
            plot_on_canvas(fourier_cache["x_plot_base"], y_fourier_target_vals, y_original_plot_vals,
                           n_terms_from_slider, fourier_cache["L"], fourier_cache["A"], fourier_cache["B"])
            if isinstance(y_fourier_target_vals, np.ndarray):
                last_plotted_y_fourier = y_fourier_target_vals.copy()

    except Exception as e_main:
        traceback.print_exc()
        display_error("Erro Inesperado", f"Ocorreu um erro: {e_main}")
        ax.clear(); ax.set_title("Erro durante cálculo/plotagem", fontsize=10, color='white')
        canvas.draw_idle()
        fourier_cache["signature"] = None; last_plotted_y_fourier = None
        if animation_job_id:
            try: j.after_cancel(animation_job_id)
            except tk.TclError: pass
        is_animating_flag = False

def agendar_recalculo(event=None, triggered_by_slider=False):
    global recalc_timer_id
    if not app_running: return

    if recalc_timer_id:
        try: j.after_cancel(recalc_timer_id)
        except tk.TclError: pass

    delay = ANIMATION_DELAY_MS * (NUM_ANIMATION_FRAMES + 2) if triggered_by_slider and is_animating_flag else 150 if triggered_by_slider else 500
    
    try:
        recalc_timer_id = j.after(delay, lambda: calcular_e_plotar(triggered_by_slider_change=triggered_by_slider))
    except tk.TclError:
        if app_running: print("TclError scheduling recalculation.")

# Configurar evento do slider
n_slider.config(command=lambda val: agendar_recalculo(triggered_by_slider=True))

# Iniciar a aplicação
if app_running:
    try:
        j.after(100, lambda: calcular_e_plotar(triggered_by_slider_change=False))
        j.mainloop()
    except tk.TclError as e:
        if "application has been destroyed" not in str(e) and app_running:
            print(f"TclError in main loop: {e}")
    except Exception as e:
        if app_running:
            print(f"General Error in main loop: {e}")
            traceback.print_exc()
