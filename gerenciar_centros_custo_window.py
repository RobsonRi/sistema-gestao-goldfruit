import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import sqlite3
import csv
from centro_custo import CentroCusto
from database_manager import DatabaseManager
from importadores import ImportadorDeCentrosDeCusto


class GerenciarCentrosCustoWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.centros_custo = []
        self.id_cc_em_edicao = None

        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Centros de Custo")
        self.window.state('zoomed')

        self._build_ui()
        self._load_from_db()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        # Frame do Formulário
        frame_cadastro = tk.LabelFrame(self.window, text="Cadastrar/Atualizar Centro de Custo", padx=10, pady=10)
        frame_cadastro.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_cadastro, text="Nome:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_nome = tk.Entry(frame_cadastro, width=50)
        self.entry_nome.grid(row=0, column=1, sticky="ew", pady=2)

        tk.Label(frame_cadastro, text="Descrição:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_descricao = tk.Entry(frame_cadastro, width=50)
        self.entry_descricao.grid(row=1, column=1, sticky="ew", pady=2)

        frame_botoes_form = tk.Frame(frame_cadastro)
        frame_botoes_form.grid(row=2, column=0, columnspan=2, pady=10)
        self.btn_salvar = tk.Button(frame_botoes_form, text="Salvar", command=self._salvar)
        self.btn_salvar.pack(side=tk.LEFT, padx=5)
        btn_limpar = tk.Button(frame_botoes_form, text="Limpar Campos", command=self._limpar_campos)
        btn_limpar.pack(side=tk.LEFT, padx=5)

        # Frame da Tabela e Busca
        frame_lista = tk.LabelFrame(self.window, text="Centros de Custo Cadastrados", padx=10, pady=10)
        frame_lista.pack(pady=10, padx=10, fill="both", expand=True)

        frame_busca = tk.Frame(frame_lista)
        frame_busca.pack(pady=5, fill="x")
        tk.Label(frame_busca, text="Buscar por Nome:").pack(side=tk.LEFT)
        self.entry_busca = tk.Entry(frame_busca)
        self.entry_busca.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca.bind("<KeyRelease>", self._filtrar_na_tabela)

        frame_tree = tk.Frame(frame_lista)
        frame_tree.pack(fill="both", expand=True)

        cols = ("id", "nome", "descricao")
        self.tree_cc = ttk.Treeview(frame_tree, columns=cols, show="headings")
        cabecalhos = {"id": "ID", "nome": "Nome", "descricao": "Descrição"}
        for col, texto in cabecalhos.items():
            self.tree_cc.heading(col, text=texto, command=lambda c=col: self._ordenar_coluna(c, False))

        self.tree_cc.column("id", width=0,stretch=tk.NO)
        self.tree_cc.column("nome", width=250,anchor="center")
        self.tree_cc.column("descricao", width=250, anchor="center")

        self.tree_cc.tag_configure('oddrow', background='#F0F0F0')  # Cinza claro para linhas ímpares
        self.tree_cc.tag_configure('evenrow', background='white')  # Branco para linhas pares

        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_cc.yview)
        self.tree_cc.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_cc.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_cc.bind("<<TreeviewSelect>>", self._on_select)

        frame_botoes_tabela = tk.Frame(frame_lista)
        frame_botoes_tabela.pack(pady=5)
        btn_excluir = tk.Button(frame_botoes_tabela, text="Excluir Selecionado", command=self._excluir)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        btn_importar = tk.Button(frame_botoes_tabela, text="Importar de CSV", command=self._importar_csv)
        btn_importar.pack(side=tk.LEFT, padx=15)

    def _load_from_db(self):
        self.centros_custo = [CentroCusto.from_dict(row) for row in self.db_manager.fetch_all('centros_custo')]
        self._carregar_na_tabela(self.centros_custo)

    def _carregar_na_tabela(self, lista):
        self.tree_cc.delete(*self.tree_cc.get_children())

        for i, cc in enumerate(lista):
            # Alterna a tag (estilo) entre 'evenrow' (par) e 'oddrow' (ímpar)
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'

            self.tree_cc.insert("", "end", values=(cc.id, cc.nome, cc.descricao or ""), tags=(tag,))

    def _filtrar_na_tabela(self, event=None):
        texto = self.entry_busca.get().lower()
        filtrados = self.centros_custo if not texto else [cc for cc in self.centros_custo if texto in cc.nome.lower()]
        self._carregar_na_tabela(filtrados)

    def _ordenar_coluna(self, coluna, reversa):
        # Passo 1: Pega os dados da coluna para ordenar a lista
        lista = [(self.tree_cc.set(k, coluna), k) for k in self.tree_cc.get_children('')]

        colunas_numericas = ['id', 'descricao']
        if coluna in colunas_numericas:
            try:
                lista.sort(key=lambda t: float(t[0]), reverse=reversa)
            except (ValueError, TypeError):
                lista.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)
        else:
            lista.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)

        # Passo 2: Move as linhas para a nova ordem na tabela
        for i, (val, k) in enumerate(lista):
            self.tree_cc.move(k, '', i)

        # --- NOVO: Passo 3: Re-aplica as cores (tags) na nova ordem ---
        for i, item_id in enumerate(self.tree_cc.get_children('')):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree_cc.item(item_id, tags=(tag,))
        # --- FIM DA NOVA LÓGICA ---

        # Passo 4: Inverte o comando do cabeçalho para o próximo clique
        self.tree_cc.heading(coluna, command=lambda: self._ordenar_coluna(coluna, not reversa))

    def _limpar_campos(self):
        self.entry_nome.delete(0, tk.END)
        self.entry_descricao.delete(0, tk.END)
        self.id_cc_em_edicao = None
        self.btn_salvar.config(text="Salvar")
        if self.tree_cc.selection():
            self.tree_cc.selection_remove(self.tree_cc.selection())

    def _on_select(self, event):
        selected = self.tree_cc.selection()
        if not selected: return
        item_id = self.tree_cc.item(selected[0], "values")[0]
        cc_obj = next((cc for cc in self.centros_custo if cc.id == item_id), None)
        if not cc_obj: return
        self.entry_nome.delete(0, tk.END);
        self.entry_nome.insert(0, cc_obj.nome)
        self.entry_descricao.delete(0, tk.END);
        self.entry_descricao.insert(0, cc_obj.descricao or "")
        self.id_cc_em_edicao = item_id
        self.btn_salvar.config(text="Atualizar")

    def _salvar(self):
        nome = self.entry_nome.get().strip().upper()
        descricao = self.entry_descricao.get().strip().upper()
        if not nome:
            messagebox.showwarning("Validação", "O nome é obrigatório.", parent=self.window)
            return
        cc = CentroCusto(nome=nome, descricao=descricao)
        try:
            if self.id_cc_em_edicao:
                self.db_manager.update('centros_custo', self.id_cc_em_edicao, cc.to_dict())
            else:
                self.db_manager.insert('centros_custo', cc.to_dict())
            messagebox.showinfo("Sucesso", "Centro de Custo salvo com sucesso.", parent=self.window)
            self._limpar_campos()
            self._load_from_db()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe um centro de custo com o nome '{nome}'.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.window)

    def _excluir(self):
        if not self.id_cc_em_edicao:
            messagebox.showwarning("Aviso", "Selecione um item para excluir.", parent=self.window)
            return
        nome = self.entry_nome.get()
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir o centro de custo '{nome}'?",
                               parent=self.window):
            try:
                self.db_manager.delete('centros_custo', self.id_cc_em_edicao)
                self._limpar_campos()
                self._load_from_db()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Não é possível excluir, pois está associado a abastecimentos.",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.window)

    def _importar_csv(self):
        """Pede um arquivo ao usuário e usa a classe importadora para processá-lo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV de Centros de Custo",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not filepath:
            return

        # 1. Cria uma instância do importador
        importer = ImportadorDeCentrosDeCusto(self.db_manager, filepath)

        # 2. Executa a importação
        resultado = importer.executar()

        # 3. Exibe o resultado para o usuário
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

        # 4. Atualiza a tabela na tela
        self._load_from_db()