import os
import json
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from pypdf import PdfReader, PdfWriter

HISTORIAL_FILE = "historial.json"
MAX_HISTORIAL = 15

DESTINOS_FILE = "destinos_historial.json"
MAX_DESTINOS = 10

class AppPassPDF(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("App Pass - Gestor de Seguridad PDF Masivo")
        self.geometry("950x740")
        self.minsize(820, 620)  # Tamaño mínimo seguro
        self.resizable(True, True)
        
        # --- ICONO DE LA VENTANA ---
        try:
            self.iconbitmap("sas.ico")
        except Exception:
            pass 
        
        self.archivos_datos = []  
        self.historial_rutas = self.cargar_historial(HISTORIAL_FILE, MAX_HISTORIAL)
        self.destinos_rutas = self.cargar_historial(DESTINOS_FILE, MAX_DESTINOS)
        self.archivos_copiados = []  
        
        self.carpeta_destino_global = tk.StringVar(value="")

        self.crear_interfaz()
        
        # Atajos de teclado globales
        self.bind("<Control-v>", lambda e: self.pegar_desde_portapapeles())
        self.bind("<Control-c>", lambda e: self.copiar_seleccionados_tabla())

    def cargar_historial(self, archivo, max_elementos):
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def guardar_historial(self, datos, archivo):
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def agregar_a_historial_archivos(self, rutas):
        for ruta in rutas:
            ruta = os.path.normpath(ruta)
            if ruta in self.historial_rutas:
                self.historial_rutas.remove(ruta)
            self.historial_rutas.insert(0, ruta)
        
        if len(self.historial_rutas) > MAX_HISTORIAL:
            self.historial_rutas = self.historial_rutas[:MAX_HISTORIAL]
            
        self.guardar_historial(self.historial_rutas, HISTORIAL_FILE)
        self.actualizar_combobox_historial()

    def agregar_a_historial_destinos(self, carpeta):
        carpeta = os.path.normpath(carpeta)
        if carpeta in self.destinos_rutas:
            self.destinos_rutas.remove(carpeta)
        self.destinos_rutas.insert(0, carpeta)
        
        if len(self.destinos_rutas) > MAX_DESTINOS:
            self.destinos_rutas = self.destinos_rutas[:MAX_DESTINOS]
            
        self.guardar_historial(self.destinos_rutas, DESTINOS_FILE)
        self.actualizar_combobox_destinos()

    def actualizar_combobox_historial(self):
        self.combo_historial['values'] = self.historial_rutas
        if self.historial_rutas:
            self.combo_historial.set("Añadir archivos desde el historial...")

    def actualizar_combobox_destinos(self):
        self.combo_destinos['values'] = self.destinos_rutas

    def crear_interfaz(self):
        # Configurar la ventana principal para que expanda su contenido con flexibilidad
        self.rowconfigure(2, weight=1)  # La fila de la tabla se expande
        self.columnconfigure(0, weight=1)

        # --- Título ---
        titulo = tk.Label(self, text="Gestor de Seguridad PDF Masivo", font=("Arial", 13, "bold"))
        titulo.grid(row=0, column=0, pady=8)

        # --- Panel Superior: Historial y Botones de Selección ---
        frame_superior = tk.Frame(self)
        frame_superior.grid(row=1, column=0, sticky="ew", padx=15, pady=4)
        frame_superior.columnconfigure(0, weight=1)

        lbl_hist = tk.Label(frame_superior, text="Historial reciente de archivos (últimos 15):", font=("Arial", 9, "bold"))
        lbl_hist.grid(row=0, column=0, sticky="w", pady=(0, 2))

        frame_combo_btn = tk.Frame(frame_superior)
        frame_combo_btn.grid(row=1, column=0, sticky="ew")
        frame_combo_btn.columnconfigure(0, weight=1)

        self.combo_historial = ttk.Combobox(frame_combo_btn, state="readonly", font=("Arial", 9))
        self.combo_historial.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.combo_historial.bind("<<ComboboxSelected>>", self.seleccionar_desde_historial)
        self.actualizar_combobox_historial()

        btn_examinar = tk.Button(frame_combo_btn, text="Examinar...", command=self.examinar_archivos_dialogo, bg="#e0e0e0", font=("Arial", 9))
        btn_examinar.grid(row=0, column=1, padx=(0, 5))

        btn_pegar = tk.Button(frame_combo_btn, text="📋 Pegar (Ctrl+V)", command=self.pegar_desde_portapapeles, bg="#e2e3e5", font=("Arial", 9))
        btn_pegar.grid(row=0, column=2)

        # --- Tabla de Ficheros (Treeview) con Drag & Drop y Menú Contextual ---
        frame_tabla = tk.LabelFrame(self, text=" Ficheros seleccionados (Arrastra PDFs aquí o usa Clic Derecho) ", font=("Arial", 9, "bold"), padx=8, pady=6)
        frame_tabla.grid(row=2, column=0, sticky="nsew", padx=15, pady=6)
        frame_tabla.rowconfigure(0, weight=1)
        frame_tabla.columnconfigure(0, weight=1)

        columnas = ("nombre", "estado", "resultado", "destino", "ruta")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings")
        self.tree.heading("nombre", text="Archivo PDF")
        self.tree.heading("estado", text="Seguridad")
        self.tree.heading("resultado", text="Resultado")
        self.tree.heading("destino", text="Carpeta Destino")
        self.tree.heading("ruta", text="Ruta Original")

        self.tree.column("nombre", width=160, minwidth=100, stretch=True)
        self.tree.column("estado", width=90, minwidth=80, stretch=False)
        self.tree.column("resultado", width=140, minwidth=100, stretch=True)
        self.tree.column("destino", width=220, minwidth=120, stretch=True)
        self.tree.column("ruta", width=200, minwidth=120, stretch=True)

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.abrir_pdf_con_doble_click)

        # Registrar Drag & Drop en la tabla
        self.tree.drop_target_register(DND_FILES)
        self.tree.dnd_bind('<<Drop>>', self.al_soltar_archivos)

        # --- Menú Contextual (Clic Derecho) ---
        self.menu_contextual = tk.Menu(self, tearoff=0)
        self.tree.bind("<Button-3>", self.mostrar_menu_contextual)

        # --- Panel de Carpeta de Destino Global (Bajo la tabla) ---
        frame_destino = tk.LabelFrame(self, text=" Configuración de Carpeta de Destino Global ", font=("Arial", 9, "bold"), padx=8, pady=6)
        frame_destino.grid(row=3, column=0, sticky="ew", padx=15, pady=4)
        frame_destino.columnconfigure(0, weight=1)

        lbl_dest_reciente = tk.Label(frame_destino, text="Últimas 10 carpetas utilizadas:", font=("Arial", 9, "bold"))
        lbl_dest_reciente.grid(row=0, column=0, sticky="w", pady=(0, 2))

        frame_combo_dest = tk.Frame(frame_destino)
        frame_combo_dest.grid(row=1, column=0, sticky="ew", pady=2)
        frame_combo_dest.columnconfigure(0, weight=1)

        self.combo_destinos = ttk.Combobox(frame_combo_dest, state="readonly", font=("Arial", 9))
        self.combo_destinos.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.combo_destinos.bind("<<ComboboxSelected>>", self.seleccionar_destino_desde_historial)
        self.actualizar_combobox_destinos()

        btn_examinar_dest = tk.Button(frame_combo_dest, text="Examinar...", command=self.seleccionar_carpeta_destino, bg="#e0e0e0", font=("Arial", 9))
        btn_examinar_dest.grid(row=0, column=1, padx=(0, 5))

        btn_reset_dir = tk.Button(frame_combo_dest, text="Por defecto", command=self.resetear_carpeta_destino, bg="#e0e0e0", font=("Arial", 9))
        btn_reset_dir.grid(row=0, column=2)

        frame_dest_actual = tk.Frame(frame_destino)
        frame_dest_actual.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        frame_dest_actual.columnconfigure(0, weight=1)

        self.entry_destino = tk.Entry(frame_dest_actual, textvariable=self.carpeta_destino_global, font=("Arial", 9), state="readonly")
        self.entry_destino.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        btn_abrir_explorador = tk.Button(frame_dest_actual, text="📂 Abrir en Explorador", command=self.abrir_explorador_activo, bg="#d1ecf1", fg="#0c5460", font=("Arial", 9, "bold"))
        btn_abrir_explorador.grid(row=0, column=1)

        btn_limpiar_lista = tk.Button(self, text="Vaciar lista de archivos", command=self.limpiar_seleccion, font=("Arial", 9), fg="#c0392b")
        btn_limpiar_lista.grid(row=4, column=0, sticky="e", padx=15, pady=2)

        # --- Sección de Gestión de Contraseñas ---
        frame_acciones = tk.LabelFrame(self, text=" Acciones de Seguridad ", font=("Arial", 9, "bold"), padx=10, pady=6)
        frame_acciones.grid(row=5, column=0, sticky="ew", padx=15, pady=4)
        frame_acciones.columnconfigure(1, weight=1)

        tk.Label(frame_acciones, text="Contraseña Actual (si aplica):", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=3)
        self.entry_pwd_actual = tk.Entry(frame_acciones, show="*", font=("Arial", 9))
        self.entry_pwd_actual.grid(row=0, column=1, sticky="ew", pady=3, padx=10)

        tk.Label(frame_acciones, text="Nueva Contraseña:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=3)
        self.entry_pwd_nueva = tk.Entry(frame_acciones, show="*", font=("Arial", 9))
        self.entry_pwd_nueva.grid(row=1, column=1, sticky="ew", pady=3, padx=10)

        frame_botones = tk.Frame(frame_acciones)
        frame_botones.grid(row=2, column=0, columnspan=2, pady=6)

        btn_agregar = tk.Button(frame_botones, text="Aplicar Password a Lote", command=self.accion_aplicar_password_lote, bg="#d4edda", fg="#155724", font=("Arial", 9, "bold"), width=22, padx=4, pady=3)
        btn_agregar.pack(side="left", padx=5)

        btn_quitar = tk.Button(frame_botones, text="Quitar Seguridad a Lote", command=self.accion_quitar_password_lote, bg="#f8d7da", fg="#721c24", font=("Arial", 9, "bold"), width=20, padx=4, pady=3)
        btn_quitar.pack(side="left", padx=5)

    def seleccionar_destino_desde_historial(self, event):
        seleccion = self.combo_destinos.get()
        if seleccion and os.path.exists(seleccion):
            norm_path = os.path.normpath(seleccion)
            self.carpeta_destino_global.set(norm_path)
            self.actualizar_destinos_en_tabla()

    def seleccionar_carpeta_destino(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if carpeta:
            norm_path = os.path.normpath(carpeta)
            self.carpeta_destino_global.set(norm_path)
            self.agregar_a_historial_destinos(norm_path)
            self.actualizar_destinos_en_tabla()

    def resetear_carpeta_destino(self):
        self.carpeta_destino_global.set("")
        self.actualizar_destinos_en_tabla()

    def mostrar_menu_contextual(self, event):
        item_id = self.tree.identify_row(event.y)
        self.menu_contextual.delete(0, tk.END)

        if item_id:
            if item_id not in self.tree.selection():
                self.tree.selection_set(item_id)
            
            self.menu_contextual.add_command(label="📂 Abrir archivo", command=self.menu_abrir_archivo)
            self.menu_contextual.add_command(label="📋 Copiar archivo(s)", command=self.copiar_seleccionados_tabla)
            self.menu_contextual.add_command(label="📄 Pegar (crear copia con _copia1)", command=self.pegar_archivo_con_sufijo)
        else:
            self.tree.selection_remove(self.tree.selection())
            if self.archivos_copiados:
                self.menu_contextual.add_command(label="📄 Pegar (crear copia con _copia1)", command=self.pegar_archivo_con_sufijo)
            else:
                self.menu_contextual.add_command(label="📋 Pegar (desde portapapeles)", command=self.pegar_desde_portapapeles)

        try:
            self.menu_contextual.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu_contextual.grab_release()

    def menu_abrir_archivo(self):
        seleccion = self.tree.selection()
        if seleccion:
            item = self.tree.item(seleccion[0])
            ruta_original = item['values'][4]
            ruta_a_abrir = self.obtener_ruta_salida_para_archivo(ruta_original)
            if not os.path.exists(ruta_a_abrir):
                ruta_a_abrir = ruta_original
            if os.path.exists(ruta_a_abrir):
                try:
                    os.startfile(ruta_a_abrir)
                except Exception as ex:
                    messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{ex}")

    def copiar_seleccionados_tabla(self, event=None):
        seleccion = self.tree.selection()
        if seleccion:
            self.archivos_copiados = []
            for item_id in seleccion:
                item = self.tree.item(item_id)
                ruta_original = item['values'][4]
                ruta_efectiva = self.obtener_ruta_salida_para_archivo(ruta_original)
                if not os.path.exists(ruta_efectiva):
                    ruta_efectiva = ruta_original
                if os.path.exists(ruta_efectiva):
                    self.archivos_copiados.append(ruta_efectiva)

    def pegar_archivo_con_sufijo(self):
        if not self.archivos_copiados:
            messagebox.showwarning("Aviso", "No hay ningún archivo copiado desde la tabla.")
            return

        nuevas_rutas_generadas = []
        for origen in self.archivos_copiados:
            if not os.path.exists(origen):
                continue
            
            dir_base = os.path.dirname(origen)
            nombre_archivo = os.path.basename(origen)
            nombre_sin_ext, ext = os.path.splitext(nombre_archivo)
            
            contador = 1
            nuevo_nombre = f"{nombre_sin_ext}_copia{contador}{ext}"
            ruta_destino = os.path.join(dir_base, nuevo_nombre)
            
            while os.path.exists(ruta_destino):
                contador += 1
                nuevo_nombre = f"{nombre_sin_ext}_copia{contador}{ext}"
                ruta_destino = os.path.join(dir_base, nuevo_nombre)
            
            try:
                shutil.copy2(origen, ruta_destino)
                nuevas_rutas_generadas.append(ruta_destino)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo duplicar el archivo {nombre_archivo}:\n{e}")

        if nuevas_rutas_generadas:
            self.añadir_archivos(nuevas_rutas_generadas)

    def al_soltar_archivos(self, event):
        rutas_crudas = self.tk.splitlist(event.data)
        rutas_pdf = [r for r in rutas_crudas if r.lower().endswith('.pdf')]
        if rutas_pdf:
            self.añadir_archivos(rutas_pdf)
        else:
            messagebox.showwarning("Aviso", "Solo se pueden arrastrar archivos con formato PDF (*.pdf).")

    def pegar_desde_portapapeles(self):
        try:
            clipboard_data = self.clipboard_get()
            if not clipboard_data:
                return

            lineas = clipboard_data.strip().replace('"', '').splitlines()
            rutas_a_procesar = []
            
            for linea in lineas:
                ruta_limpia = linea.strip()
                if os.path.exists(ruta_limpia) and ruta_limpia.lower().endswith('.pdf'):
                    rutas_a_procesar.append(ruta_limpia)

            if rutas_a_procesar:
                self.añadir_archivos(rutas_a_procesar)
            else:
                messagebox.showwarning("Aviso", "El portapapeles no contiene rutas de archivos PDF válidas.")
        except Exception:
            messagebox.showwarning("Aviso", "No se pudieron recuperar archivos válidos desde el portapapeles.")

    def abrir_explorador_activo(self):
        ruta_a_abrir = ""
        seleccion = self.tree.selection()
        
        if seleccion:
            item = self.tree.item(seleccion[0])
            ruta_original = item['values'][4]
            ruta_a_abrir = os.path.dirname(self.obtener_ruta_salida_para_archivo(ruta_original))
        else:
            global_dir = self.carpeta_destino_global.get()
            if global_dir and os.path.exists(global_dir):
                ruta_a_abrir = global_dir
            elif self.archivos_datos:
                ruta_a_abrir = os.path.dirname(self.obtener_ruta_salida_para_archivo(self.archivos_datos[0]['ruta']))
            else:
                ruta_a_abrir = os.getcwd()

        if os.path.exists(ruta_a_abrir):
            os.startfile(ruta_a_abrir)
        else:
            messagebox.showerror("Error", f"La ruta no existe en el disco:\n{ruta_a_abrir}")

    def actualizar_destinos_en_tabla(self):
        for item_id in self.tree.get_children():
            val = self.tree.item(item_id, 'values')
            ruta_orig = val[4]
            nuevo_destino = self.obtener_ruta_salida_para_archivo(ruta_orig)
            carpeta_destino_str = os.path.dirname(nuevo_destino)
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
            self.agregar_a_historial_archivos(nuevas_rutas)

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