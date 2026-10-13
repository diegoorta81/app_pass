import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from pypdf import PdfReader, PdfWriter

HISTORIAL_FILE = "historial.json"
MAX_HISTORIAL = 15

class AppPassPDF(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("App Pass - Gestor de Seguridad PDF Masivo")
        self.geometry("900x720")
        self.resizable(False, False)
        
        self.archivos_datos = []  
        self.historial_rutas = self.cargar_historial()
        
        # Carpeta de destino global (vacío significa la carpeta de cada archivo original)
        self.carpeta_destino_global = tk.StringVar(value="")

        self.crear_interfaz()

    def cargar_historial(self):
        if os.path.exists(HISTORIAL_FILE):
            try:
                with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def guardar_historial(self):
        try:
            with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
                json.dump(self.historial_rutas, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def agregar_a_historial(self, rutas):
        for ruta in rutas:
            ruta = os.path.normpath(ruta)
            if ruta in self.historial_rutas:
                self.historial_rutas.remove(ruta)
            self.historial_rutas.insert(0, ruta)
        
        if len(self.historial_rutas) > MAX_HISTORIAL:
            self.historial_rutas = self.historial_rutas[:MAX_HISTORIAL]
            
        self.guardar_historial()
        self.actualizar_combobox_historial()

    def actualizar_combobox_historial(self):
        self.combo_historial['values'] = self.historial_rutas
        if self.historial_rutas:
            self.combo_historial.set("Añadir archivos desde el historial...")

    def crear_interfaz(self):
        # --- Título ---
        titulo = tk.Label(self, text="Gestor de Seguridad PDF", font=("Arial", 14, "bold"))
        titulo.pack(pady=8)

        # --- Panel Superior: Historial y Botones de Selección ---
        frame_superior = tk.Frame(self)
        frame_superior.pack(fill="x", padx=20, pady=5)

        lbl_hist = tk.Label(frame_superior, text="Historial reciente (últimos 15 archivos):", font=("Arial", 9, "bold"))
        lbl_hist.pack(anchor="w", pady=(0, 2))

        frame_combo_btn = tk.Frame(frame_superior)
        frame_combo_btn.pack(fill="x", pady=2)

        self.combo_historial = ttk.Combobox(frame_combo_btn, state="readonly", width=68, font=("Arial", 9))
        self.combo_historial.pack(side="left", padx=(0, 10))
        self.combo_historial.bind("<<ComboboxSelected>>", self.seleccionar_desde_historial)
        self.actualizar_combobox_historial()

        btn_examinar = tk.Button(frame_combo_btn, text="Examinar...", command=self.examinar_archivos_dialogo, bg="#e0e0e0", font=("Arial", 9))
        btn_examinar.pack(side="left")

        # --- Tabla de Ficheros (Treeview) ---
        frame_tabla = tk.LabelFrame(self, text=" Ficheros seleccionados, estado y destino ", font=("Arial", 10, "bold"), padx=10, pady=10)
        frame_tabla.pack(fill="both", expand=True, padx=20, pady=8)

        # Añadida la columna "destino"
        columnas = ("nombre", "estado", "resultado", "destino", "ruta")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=8)
        self.tree.heading("nombre", text="Archivo PDF")
        self.tree.heading("estado", text="Seguridad")
        self.tree.heading("resultado", text="Resultado")
        self.tree.heading("destino", text="Carpeta Destino")
        self.tree.heading("ruta", text="Ruta Original")

        self.tree.column("nombre", width=140)
        self.tree.column("estado", width=90)
        self.tree.column("resultado", width=150)
        self.tree.column("destino", width=200)
        self.tree.column("ruta", width=180)

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.abrir_pdf_con_doble_click)

        # --- Panel de Carpeta de Destino (Ubicado justo bajo la tabla) ---
        frame_destino = tk.Frame(self)
        frame_destino.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_destino, text="Carpeta de destino global:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 2))
        
        frame_dest_cont = tk.Frame(frame_destino)
        frame_dest_cont.pack(fill="x")

        self.entry_destino = tk.Entry(frame_dest_cont, textvariable=self.carpeta_destino_global, width=65, font=("Arial", 9), state="readonly")
        self.entry_destino.pack(side="left", padx=(0, 10))

        btn_cambiar_dir = tk.Button(frame_dest_cont, text="Cambiar...", command=self.seleccionar_carpeta_destino, bg="#e0e0e0", font=("Arial", 9))
        btn_cambiar_dir.pack(side="left", padx=(0, 5))

        btn_reset_dir = tk.Button(frame_dest_cont, text="Por defecto (Original)", command=self.resetear_carpeta_destino, bg="#e0e0e0", font=("Arial", 9))
        btn_reset_dir.pack(side="left")

        # Botón para limpiar lista
        btn_limpiar_lista = tk.Button(self, text="Vaciar lista de archivos", command=self.limpiar_seleccion, font=("Arial", 9), fg="#c0392b")
        btn_limpiar_lista.pack(anchor="e", padx=20, pady=2)

        # --- Sección de Gestión de Contraseñas ---
        frame_acciones = tk.LabelFrame(self, text=" Acciones de Seguridad ", font=("Arial", 10, "bold"), padx=15, pady=8)
        frame_acciones.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_acciones, text="Contraseña Actual (si aplica):", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_pwd_actual = tk.Entry(frame_acciones, show="*", width=35, font=("Arial", 10))
        self.entry_pwd_actual.grid(row=0, column=1, sticky="w", pady=4, padx=10)

        tk.Label(frame_acciones, text="Nueva Contraseña:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_pwd_nueva = tk.Entry(frame_acciones, show="*", width=35, font=("Arial", 10))
        self.entry_pwd_nueva.grid(row=1, column=1, sticky="w", pady=4, padx=10)

        frame_botones = tk.Frame(frame_acciones)
        frame_botones.grid(row=2, column=0, columnspan=2, pady=8)

        btn_agregar = tk.Button(frame_botones, text="Aplicar Password a Lote", command=self.accion_aplicar_password_lote, bg="#d4edda", fg="#155724", font=("Arial", 9, "bold"), width=22, padx=5, pady=4)
        btn_agregar.pack(side="left", padx=5)

        btn_quitar = tk.Button(frame_botones, text="Quitar Seguridad a Lote", command=self.accion_quitar_password_lote, bg="#f8d7da", fg="#721c24", font=("Arial", 9, "bold"), width=20, padx=5, pady=4)
        btn_quitar.pack(side="left", padx=5)

    def seleccionar_carpeta_destino(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if carpeta:
            norm_path = os.path.normpath(carpeta)
            self.carpeta_destino_global.set(norm_path)
            self.actualizar_destinos_en_tabla()

    def resetear_carpeta_destino(self):
        self.carpeta_destino_global.set("")
        self.actualizar_destinos_en_tabla()

    def actualizar_destinos_en_tabla(self):
        for item_id in self.tree.get_children():
            val = self.tree.item(item_id, 'values')
            ruta_orig = val[4]
            nuevo_destino = self.obtener_ruta_salida_para_archivo(ruta_orig)
            carpeta_destino_str = os.path.dirname(nuevo_destino)
            
            # Actualizar la columna de destino (índice 3) manteniendo los demás valores
            self.tree.item(item_id, values=(val[0], val[1], val[2], carpeta_destino_str, val[4]))

    def obtener_ruta_salida_para_archivo(self, ruta_original):
        dir_personalizada = self.carpeta_destino_global.get()
        if dir_personalizada:
            return os.path.join(dir_personalizada, os.path.basename(ruta_original))
        else:
            return ruta_original

    def examinar_archivos_dialogo(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccionar archivos PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if rutas:
            self.añadir_archivos(rutas)

    def seleccionar_desde_historial(self, event):
        seleccion = self.combo_historial.get()
        if seleccion and os.path.exists(seleccion):
            self.añadir_archivos([seleccion])

    def añadir_archivos(self, rutas):
        nuevas_rutas = []
        for r in rutas:
            r_norm = os.path.normpath(r)
            if not any(item['ruta'] == r_norm for item in self.archivos_datos) and os.path.exists(r_norm):
                estado_inicial = self.comprobar_estado_inicial(r_norm)
                nombre = os.path.basename(r_norm)
                ruta_destino_final = self.obtener_ruta_salida_para_archivo(r_norm)
                dir_destino_str = os.path.dirname(ruta_destino_final)
                
                self.archivos_datos.append({
                    'ruta': r_norm,
                    'nombre': nombre,
                    'estado': estado_inicial,
                    'resultado': 'Pendiente'
                })
                
                self.tree.insert("", tk.END, values=(nombre, estado_inicial, "Pendiente", dir_destino_str, r_norm))
                nuevas_rutas.append(r_norm)
        
        if nuevas_rutas:
            self.agregar_a_historial(nuevas_rutas)

    def comprobar_estado_inicial(self, ruta):
        try:
            reader = PdfReader(ruta)
            if reader.is_encrypted:
                return "Protegido"
            else:
                return "Libre"
        except Exception:
            return "Error al leer"

    def limpiar_seleccion(self):
        self.archivos_datos.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

    def actualizar_fila_treeview(self, ruta_buscada, nuevo_resultado, nuevo_estado=None):
        for item_id in self.tree.get_children():
            val = self.tree.item(item_id, 'values')
            if val[4] == ruta_buscada:
                nombre = val[0]
                estado = nuevo_estado if nuevo_estado else val[1]
                destino = val[3]
                self.tree.item(item_id, values=(nombre, estado, nuevo_resultado, destino, ruta_buscada))
                self.update_idletasks()
                break

    def accion_aplicar_password_lote(self):
        if not self.archivos_datos:
            messagebox.showwarning("Aviso", "No hay ningún archivo PDF seleccionado en la tabla.")
            return

        pwd_actual = self.entry_pwd_actual.get()
        pwd_nueva = self.entry_pwd_nueva.get()

        if not pwd_nueva:
            messagebox.showwarning("Aviso", "Debe introducir una nueva contraseña.")
            return

        for item in self.archivos_datos:
            ruta_orig = item['ruta']
            nombre = item['nombre']
            ruta_destino = self.obtener_ruta_salida_para_archivo(ruta_orig)

            if os.path.exists(ruta_destino):
                if not messagebox.askyesno("Confirmar sobrescritura", f"El fichero destino ya existe:\n{ruta_destino}\n\n¿Desea sobrescribirlo?"):
                    self.actualizar_fila_treeview(ruta_orig, "Omitido por usuario")
                    continue

            try:
                reader = PdfReader(ruta_orig)
                if reader.is_encrypted:
                    if not reader.decrypt(pwd_actual):
                        self.actualizar_fila_treeview(ruta_orig, "Error: Pwd actual incorrecta")
                        continue

                writer = PdfWriter()
                writer.append(reader)
                writer.encrypt(pwd_nueva)

                with open(ruta_destino, "wb") as f:
                    writer.write(f)

                self.actualizar_fila_treeview(ruta_orig, "Éxito: Password aplicada", "Protegido")
            except Exception as e:
                self.actualizar_fila_treeview(ruta_orig, f"Error: {str(e)}")

        messagebox.showinfo("Proceso Finalizado", "Se ha completado el procesamiento del lote de ficheros.")

    def accion_quitar_password_lote(self):
        if not self.archivos_datos:
            messagebox.showwarning("Aviso", "No hay ningún archivo PDF seleccionado en la tabla.")
            return

        pwd_actual = self.entry_pwd_actual.get()

        for item in self.archivos_datos:
            ruta_orig = item['ruta']
            nombre = item['nombre']
            ruta_destino = self.obtener_ruta_salida_para_archivo(ruta_orig)

            if os.path.exists(ruta_destino):
                if not messagebox.askyesno("Confirmar sobrescritura", f"El fichero destino ya existe:\n{ruta_destino}\n\n¿Desea sobrescribirlo?"):
                    self.actualizar_fila_treeview(ruta_orig, "Omitido por usuario")
                    continue

            try:
                reader = PdfReader(ruta_orig)
                if reader.is_encrypted:
                    if not pwd_actual:
                        self.actualizar_fila_treeview(ruta_orig, "Error: Requiere pwd actual")
                        continue
                    if not reader.decrypt(pwd_actual):
                        self.actualizar_fila_treeview(ruta_orig, "Error: Pwd actual incorrecta")
                        continue

                writer = PdfWriter()
                writer.append(reader)

                with open(ruta_destino, "wb") as f:
                    writer.write(f)

                self.actualizar_fila_treeview(ruta_orig, "Éxito: Seguridad retirada", "Libre")
            except Exception as e:
                self.actualizar_fila_treeview(ruta_orig, f"Error: {str(e)}")

        messagebox.showinfo("Proceso Finalizado", "Se ha completado la retirada de seguridad del lote.")

    def abrir_pdf_con_doble_click(self, event):
        item_id = self.tree.selection()
        if item_id:
            item = self.tree.item(item_id)
            ruta_original = item['values'][4]
            ruta_a_abrir = self.obtener_ruta_salida_para_archivo(ruta_original)
            if not os.path.exists(ruta_a_abrir):
                ruta_a_abrir = ruta_original

            if os.path.exists(ruta_a_abrir):
                try:
                    os.startfile(ruta_a_abrir)
                except Exception as ex:
                    messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{ex}")
            else:
                messagebox.showerror("Error", "El archivo ya no se encuentra en el disco.")

if __name__ == "__main__":
    app = AppPassPDF()
    app.mainloop()