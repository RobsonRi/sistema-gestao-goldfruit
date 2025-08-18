import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import sqlite3
import csv
from database_manager import DatabaseManager


class ParametrosCO2Window:
    def __init__(self, parent, db_manager, on_save_callback=None):
        self.parent = parent
        self.db_manager = db_manager
        self.on_save_callback = on_save_callback
        self.id_parametro_em_edicao = None

        self.window = tk.Toplevel(parent)
        self.window.title("Configurações de Emissão de CO2")
        self.window.state('zoomed')

        self._build_ui()
        self._load_parametros_to_ui()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        # Frame do Formulário
        frame_cadastro = tk.LabelFrame(self.window, text="Adicionar/Atualizar Parâmetro", padx=10, pady=10)
        frame_cadastro.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_cadastro, text="Tipo de Combustível:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_tipo_combustivel = tk.Entry(frame_cadastro, width=30)
        self.entry_tipo_combustivel.grid(row=0, column=1, sticky="ew", pady=2)

        tk.Label(frame_cadastro, text="Fator de Emissão (kg CO2/litro):").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_fator_emissao = tk.Entry(frame_cadastro, width=30)
        self.entry_fator_emissao.grid(row=1, column=1, sticky="ew", pady=2)

        frame_botoes_form = tk.Frame(frame_cadastro)
        frame_botoes_form.grid(row=2, column=0, columnspan=2, pady=10)

        self.btn_salvar = tk.Button(frame_botoes_form, text="Salvar Parâmetro", command=self._salvar_parametro)
        self.btn_salvar.pack(side=tk.LEFT, padx=5)

        btn_limpar = tk.Button(frame_botoes_form, text="Limpar", command=self._limpar_campos)
        btn_limpar.pack(side=tk.LEFT, padx=5)

        # Frame da Tabela
        frame_tabela = tk.LabelFrame(self.window, text="Parâmetros Cadastrados", padx=10, pady=10)
        frame_tabela.pack(pady=10, padx=10, fill="both", expand=True)

        cols = ("id", "tipo_combustivel", "fator_emissao")
        self.tree_parametros = ttk.Treeview(frame_tabela, columns=cols, show="headings")

        self.tree_parametros.heading("id", text="ID", command=lambda: self._ordenar_coluna("id", False))
        self.tree_parametros.heading("tipo_combustivel", text="Combustível",
                                     command=lambda: self._ordenar_coluna("tipo_combustivel", False))
        self.tree_parametros.heading("fator_emissao", text="Fator de Emissão",
                                     command=lambda: self._ordenar_coluna("fator_emissao", False))

        self.tree_parametros.column("id", width=0,stretch=tk.NO)
        self.tree_parametros.column("fator_emissao", width=120, anchor="e")

        scrollbar = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL, command=self.tree_parametros.yview)
        self.tree_parametros.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_parametros.pack(fill="both", expand=True, side=tk.LEFT)
        self.tree_parametros.bind('<<TreeviewSelect>>', self._on_item_select)

        frame_botoes_tabela = tk.Frame(frame_tabela)
        frame_botoes_tabela.pack(pady=5)
        btn_excluir = tk.Button(frame_botoes_tabela, text="Excluir Selecionado", command=self._excluir_parametro)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        btn_importar = tk.Button(frame_botoes_tabela, text="Importar de CSV", command=self._importar_csv)
        btn_importar.pack(side=tk.LEFT, padx=15)

    def _load_parametros_to_ui(self):
        self.tree_parametros.delete(*self.tree_parametros.get_children())
        for row in self.db_manager.fetch_all('parametros_co2'):
            self.tree_parametros.insert("", "end", values=(row['id'], row['tipo_combustivel'], row['fator_emissao']))

    def _limpar_campos(self):
        self.entry_tipo_combustivel.delete(0, tk.END)
        self.entry_fator_emissao.delete(0, tk.END)
        self.id_parametro_em_edicao = None
        self.btn_salvar.config(text="Salvar Parâmetro")
        if self.tree_parametros.selection():
            self.tree_parametros.selection_remove(self.tree_parametros.selection())

    def _on_item_select(self, event):
        selected_item = self.tree_parametros.selection()
        if not selected_item: return
        values = self.tree_parametros.item(selected_item, 'values')
        item_id, combustivel, fator = values
        self.entry_tipo_combustivel.delete(0, tk.END);
        self.entry_tipo_combustivel.insert(0, combustivel)
        self.entry_fator_emissao.delete(0, tk.END);
        self.entry_fator_emissao.insert(0, str(fator).replace('.', ','))
        self.id_parametro_em_edicao = item_id
        self.btn_salvar.config(text="Atualizar Parâmetro")

    def _excluir_parametro(self):
        if not self.id_parametro_em_edicao:
            messagebox.showwarning("Aviso", "Selecione um parâmetro para excluir.", parent=self.window)
            return
        nome_combustivel = self.entry_tipo_combustivel.get()
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir o parâmetro '{nome_combustivel}'?",
                               parent=self.window):
            try:
                self.db_manager.delete('parametros_co2', self.id_parametro_em_edicao)
                messagebox.showinfo("Sucesso", "Parâmetro excluído com sucesso!", parent=self.window)
                self._limpar_campos()
                self._load_parametros_to_ui()
                if self.on_save_callback: self.on_save_callback()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir: {e}", parent=self.window)

    def _salvar_parametro(self):
        tipo_combustivel = self.entry_tipo_combustivel.get().strip().upper()
        fator_emissao_str = self.entry_fator_emissao.get().strip().replace(',', '.')
        if not tipo_combustivel or not fator_emissao_str:
            messagebox.showwarning("Validação", "Ambos os campos são obrigatórios.", parent=self.window)
            return
        try:
            fator_emissao = float(fator_emissao_str)
        except ValueError:
            messagebox.showerror("Erro", "Fator de Emissão deve ser um número.", parent=self.window)
            return

        parametro_data = {'tipo_combustivel': tipo_combustivel, 'fator_emissao': fator_emissao}
        try:
            if self.id_parametro_em_edicao:
                self.db_manager.update('parametros_co2', self.id_parametro_em_edicao, parametro_data)
            else:
                self.db_manager.insert('parametros_co2', parametro_data)

            messagebox.showinfo("Sucesso", "Parâmetro salvo com sucesso!", parent=self.window)
            self._limpar_campos()
            self._load_parametros_to_ui()
            if self.on_save_callback: self.on_save_callback()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe um parâmetro para '{tipo_combustivel}'.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}", parent=self.window)

    def _ordenar_coluna(self, coluna, reversa):
        lista = [(self.tree_parametros.set(k, coluna), k) for k in self.tree_parametros.get_children('')]
        if coluna == 'id' or coluna == 'fator_emissao':
            lista.sort(key=lambda t: float(t[0].replace(',', '.')), reverse=reversa)
        else:
            lista.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)
        for i, (val, k) in enumerate(lista):
            self.tree_parametros.move(k, '', i)
        self.tree_parametros.heading(coluna, command=lambda: self._ordenar_coluna(coluna, not reversa))

    def _importar_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if not filepath: return
        sucesso, erros, duplicados = 0, 0, 0
        try:
            with open(filepath, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        tipo = row.get('tipo_combustivel', '').strip().upper()
                        fator = float(str(row.get('fator_emissao', 0)).replace(',', '.'))
                        if not tipo:
                            erros += 1;
                            continue
                        self.db_manager.insert('parametros_co2', {'tipo_combustivel': tipo, 'fator_emissao': fator})
                        sucesso += 1
                    except sqlite3.IntegrityError:
                        duplicados += 1
                    except (ValueError, TypeError):
                        erros += 1
            messagebox.showinfo("Importação Concluída", f"Sucesso: {sucesso}\nDuplicados: {duplicados}\nErros: {erros}")
            self._load_parametros_to_ui()
            if self.on_save_callback: self.on_save_callback()
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo.\nErro: {e}")