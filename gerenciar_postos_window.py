# gerenciar_postos_window.py

import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import sqlite3
import csv
from importadores import ImportadorDePostos

from posto import Posto
from database_manager import DatabaseManager


class GerenciarPostosWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.postos = []
        self.id_posto_em_edicao = None

        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Postos de Combustível")
        self.window.state('zoomed')

        self._build_ui()
        self._load_postos_from_db()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        # Frame do Formulário
        frame_cadastro = tk.LabelFrame(self.window, text="Cadastrar/Atualizar Posto", padx=10, pady=10)
        frame_cadastro.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_cadastro, text="Nome:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_nome = tk.Entry(frame_cadastro, width=40)
        self.entry_nome.grid(row=0, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Cidade:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_cidade = tk.Entry(frame_cadastro, width=40)
        self.entry_cidade.grid(row=1, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Estado (UF):").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_estado = tk.Entry(frame_cadastro, width=40)
        self.entry_estado.grid(row=2, column=1, sticky="ew", pady=2)

        frame_botoes_form = tk.Frame(frame_cadastro)
        frame_botoes_form.grid(row=3, column=0, columnspan=2, pady=10)
        self.btn_salvar = tk.Button(frame_botoes_form, text="Salvar", command=self._salvar_posto)
        self.btn_salvar.pack(side=tk.LEFT, padx=5)
        btn_limpar = tk.Button(frame_botoes_form, text="Limpar Campos", command=self._limpar_campos)
        btn_limpar.pack(side=tk.LEFT, padx=5)

        # Frame da Tabela e Busca
        frame_lista = tk.LabelFrame(self.window, text="Postos Cadastrados", padx=10, pady=10)
        frame_lista.pack(pady=10, padx=10, fill="both", expand=True)

        frame_busca = tk.Frame(frame_lista)
        frame_busca.pack(pady=5, fill="x")
        tk.Label(frame_busca, text="Buscar por Nome ou Cidade:").pack(side=tk.LEFT)
        self.entry_busca = tk.Entry(frame_busca)
        self.entry_busca.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca.bind("<KeyRelease>", self._filtrar_na_tabela)

        frame_tree = tk.Frame(frame_lista)
        frame_tree.pack(fill="both", expand=True)

        cols = ("id", "nome", "cidade", "estado")
        self.tree_postos = ttk.Treeview(frame_tree, columns=cols, show="headings")
        cabecalhos = {"id": "ID", "nome": "Nome", "cidade": "Cidade", "estado": "UF"}
        for col, texto in cabecalhos.items():
            self.tree_postos.heading(col, text=texto,
                                     command=lambda c=col: self._ordenar_coluna(self.tree_postos, c, False))

        self.tree_postos.column("id", width=0, stretch=tk.NO)
        self.tree_postos.column("nome", width=400)
        self.tree_postos.column("cidade", width=200)
        self.tree_postos.column("estado", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_postos.yview)
        self.tree_postos.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_postos.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_postos.bind("<<TreeviewSelect>>", self._on_select)

        frame_botoes_tabela = tk.Frame(frame_lista)
        frame_botoes_tabela.pack(pady=5)
        btn_excluir = tk.Button(frame_botoes_tabela, text="Excluir Selecionado", command=self._excluir_posto)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        btn_importar = tk.Button(frame_botoes_tabela, text="Importar de CSV", command=self._importar_csv)
        btn_importar.pack(side=tk.LEFT, padx=15)

    def _load_postos_from_db(self):
        self.postos = [Posto.from_dict(row) for row in self.db_manager.fetch_all('postos_combustivel')]
        self._carregar_na_tabela(self.postos)

    def _carregar_na_tabela(self, lista):
        self.tree_postos.delete(*self.tree_postos.get_children())
        for posto in lista:
            self.tree_postos.insert("", "end", values=(posto.id, posto.nome, posto.cidade or "", posto.estado or ""))

    def _filtrar_na_tabela(self, event=None):
        texto = self.entry_busca.get().lower()
        filtrados = self.postos if not texto else [p for p in self.postos if
                                                   texto in p.nome.lower() or texto in (p.cidade or "").lower()]
        self._carregar_na_tabela(filtrados)

    def _ordenar_coluna(self, treeview, coluna, reversa):
        lista = [(treeview.set(item_id, coluna), item_id) for item_id in treeview.get_children('')]
        if coluna == 'id':
            lista.sort(key=lambda t: int(t[0]), reverse=reversa)
        else:
            lista.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)
        for i, (val, k) in enumerate(lista):
            treeview.move(k, '', i)
        treeview.heading(coluna, command=lambda: self._ordenar_coluna(treeview, coluna, not reversa))

    def _limpar_campos(self):
        self.entry_nome.delete(0, tk.END)
        self.entry_cidade.delete(0, tk.END)
        self.entry_estado.delete(0, tk.END)
        self.id_posto_em_edicao = None
        self.btn_salvar.config(text="Salvar")
        if self.tree_postos.selection():
            self.tree_postos.selection_remove(self.tree_postos.selection())

    def _on_select(self, event):
        selected = self.tree_postos.selection()
        if not selected: return
        item_id = self.tree_postos.item(selected[0], "values")[0]
        posto_obj = next((p for p in self.postos if p.id == item_id), None)
        if not posto_obj: return
        self.entry_nome.delete(0, tk.END);
        self.entry_nome.insert(0, posto_obj.nome)
        self.entry_cidade.delete(0, tk.END);
        self.entry_cidade.insert(0, posto_obj.cidade or "")
        self.entry_estado.delete(0, tk.END);
        self.entry_estado.insert(0, posto_obj.estado or "")
        self.id_posto_em_edicao = item_id
        self.btn_salvar.config(text="Atualizar")

    def _salvar_posto(self):
        nome = self.entry_nome.get().strip().upper()
        cidade = self.entry_cidade.get().strip().upper()
        estado = self.entry_estado.get().strip().upper()
        if not nome:
            messagebox.showwarning("Validação", "O nome do posto é obrigatório.", parent=self.window)
            return
        posto = Posto(nome, cidade, estado)
        try:
            if self.id_posto_em_edicao:
                    self.db_manager.update('postos_combustivel', self.id_posto_em_edicao, posto.to_dict())
            else:
                    self.db_manager.insert('postos_combustivel', posto.to_dict())
            messagebox.showinfo("Sucesso", "Posto salvo com sucesso.", parent=self.window)
            self._limpar_campos()
            self._load_postos_from_db()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe um posto com o nome '{nome}'.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.window)

    def _excluir_posto(self):
        if not self.id_posto_em_edicao:
            messagebox.showwarning("Aviso", "Selecione um posto para excluir.", parent=self.window)
            return
        nome = self.entry_nome.get()
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir o posto '{nome}'?", parent=self.window):
            try:
                self.db_manager.delete('postos_combustivel', self.id_posto_em_edicao)
                self._limpar_campos()
                self._load_postos_from_db()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro",
                                     "Não é possível excluir este posto, pois ele está associado a abastecimentos.",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.window)

    def _importar_csv(self):
        """Pede um arquivo ao usuário e usa a classe importadora para processá-lo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV de Postos",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not filepath:
            return

        importer = ImportadorDePostos(self.db_manager, filepath)
        resultado = importer.executar()

        if "erro_leitura" in resultado:
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo: {resultado['erro_leitura']}",
                                 parent=self.window)
        else:
            messagebox.showinfo("Importação Concluída",
                                f"Importação finalizada!\n\n"
                                f"Registros importados: {resultado['sucesso']}\n"
                                f"Duplicados ignorados: {resultado['duplicados']}\n"
                                f"Linhas com erro: {resultado['erros']}",
                                parent=self.window)

        self._load_from_db()  # Atualiza a tabela na tela