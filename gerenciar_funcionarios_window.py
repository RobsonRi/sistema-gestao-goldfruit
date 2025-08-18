import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import sqlite3
import csv
from pessoa import Pessoa
from importadores import ImportadorDeFuncionarios
from database_manager import DatabaseManager


class GerenciarFuncionariosWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.pessoas = []
        self.id_pessoa_em_edicao = None

        # Variáveis de estado para ordenação
        self._coluna_ordenada = ""
        self._ordem_reversa = False

        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Funcionários")
        self.window.state('zoomed')

        self._build_ui()
        self._load_pessoas_from_db()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        # Frame do Formulário
        frame_cadastro = tk.LabelFrame(self.window, text="Cadastrar/Atualizar Funcionário", padx=10, pady=10)
        frame_cadastro.pack(pady=10, padx=10, fill="x")

        # Layout do Formulário
        tk.Label(frame_cadastro, text="Nome:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_nome = tk.Entry(frame_cadastro, width=40)
        self.entry_nome.grid(row=0, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Função:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_funcao = tk.Entry(frame_cadastro, width=40)
        self.entry_funcao.grid(row=1, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="CPF:").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_cpf = tk.Entry(frame_cadastro, width=40)
        self.entry_cpf.grid(row=2, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Data de Nasc. (DD/MM/AAAA):").grid(row=3, column=0, sticky="w", pady=2)
        self.entry_data_nascimento = tk.Entry(frame_cadastro, width=40)
        self.entry_data_nascimento.grid(row=3, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Telefone:").grid(row=0, column=2, padx=(10, 0), sticky="w", pady=2)
        self.entry_telefone = tk.Entry(frame_cadastro, width=40)
        self.entry_telefone.grid(row=0, column=3, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Email:").grid(row=1, column=2, padx=(10, 0), sticky="w", pady=2)
        self.entry_email = tk.Entry(frame_cadastro, width=40)
        self.entry_email.grid(row=1, column=3, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="CNH:").grid(row=2, column=2, padx=(10, 0), sticky="w", pady=2)
        self.entry_cnh = tk.Entry(frame_cadastro, width=40)
        self.entry_cnh.grid(row=2, column=3, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Categoria CNH:").grid(row=3, column=2, padx=(10, 0), sticky="w", pady=2)
        self.entry_categoria_cnh = tk.Entry(frame_cadastro, width=40)
        self.entry_categoria_cnh.grid(row=3, column=3, sticky="ew", pady=2)
        self.is_motorista_var = tk.IntVar()
        self.check_is_motorista = tk.Checkbutton(frame_cadastro, text="É Motorista?", variable=self.is_motorista_var)
        self.check_is_motorista.grid(row=4, column=0, pady=5)

        frame_botoes_form = tk.Frame(frame_cadastro)
        frame_botoes_form.grid(row=5, column=0, columnspan=4, pady=10)
        self.btn_salvar = tk.Button(frame_botoes_form, text="Salvar Funcionário", command=self._salvar_pessoa)
        self.btn_salvar.pack(side=tk.LEFT, padx=5)
        btn_limpar = tk.Button(frame_botoes_form, text="Limpar Campos", command=self._limpar_campos)
        btn_limpar.pack(side=tk.LEFT, padx=5)

        # Frame da Tabela e Busca
        frame_lista = tk.LabelFrame(self.window, text="Funcionários Cadastrados", padx=10, pady=10)
        frame_lista.pack(pady=10, padx=10, fill="both", expand=True)

        frame_busca = tk.Frame(frame_lista)
        frame_busca.pack(pady=5, fill="x")
        tk.Label(frame_busca, text="Buscar por Nome:").pack(side=tk.LEFT)
        self.entry_busca = tk.Entry(frame_busca)
        self.entry_busca.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca.bind("<KeyRelease>", self._filtrar_pessoas_na_tabela)

        frame_tree = tk.Frame(frame_lista)
        frame_tree.pack(fill="both", expand=True)

        columns = ("id", "nome", "funcao", "cpf", "telefone", "is_motorista")
        self.tree_pessoas = ttk.Treeview(frame_tree, columns=columns, show="headings")

        cabecalhos = {"id": "ID", "nome": "Nome", "funcao": "Função", "cpf": "CPF", "telefone": "Telefone",
                      "is_motorista": "É Motorista?"}
        for col, texto in cabecalhos.items():
            self.tree_pessoas.heading(col, text=texto, command=lambda c=col: self._ordenar_coluna(c, False))

        self.tree_pessoas.column("id", width=0, stretch=tk.NO)
        self.tree_pessoas.column("nome", width=250)
        self.tree_pessoas.column("funcao", width=150)
        self.tree_pessoas.column("cpf", width=110, anchor="center")
        self.tree_pessoas.column("telefone", width=110, anchor="center")
        self.tree_pessoas.column("is_motorista", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_pessoas.yview)
        self.tree_pessoas.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_pessoas.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_pessoas.bind("<<TreeviewSelect>>", self._on_pessoa_select)

        frame_botoes_tabela = tk.Frame(frame_lista)
        frame_botoes_tabela.pack(pady=5)
        btn_excluir = tk.Button(frame_botoes_tabela, text="Excluir Selecionado", command=self._excluir_pessoa)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        btn_importar = tk.Button(frame_botoes_tabela, text="Importar de CSV", command=self._importar_csv)
        btn_importar.pack(side=tk.LEFT, padx=15)

    def _load_pessoas_from_db(self):
        """Carrega a lista mestre de pessoas do banco de dados uma vez."""
        self.pessoas = [Pessoa.from_dict(row) for row in self.db_manager.fetch_all('pessoas')]
        self._carregar_pessoas_na_tabela(self.pessoas)

    def _carregar_pessoas_na_tabela(self, lista_pessoas):
        """Limpa a tabela e a preenche com os dados de uma lista específica."""
        self.tree_pessoas.delete(*self.tree_pessoas.get_children())
        for p in lista_pessoas:
            status = "Sim" if p.is_motorista else "Não"
            self.tree_pessoas.insert("", "end", values=(p.id, p.nome, p.funcao, p.cpf or "", p.telefone or "", status))

    def _filtrar_pessoas_na_tabela(self, event=None):
        """Filtra a tabela em tempo real com base no que é digitado na busca."""
        texto = self.entry_busca.get().lower()
        if not texto:
            filtrados = self.pessoas
        else:
            filtrados = [p for p in self.pessoas if texto in p.nome.lower()]
        self._carregar_pessoas_na_tabela(filtrados)

    def _ordenar_coluna(self, coluna, reversa):
        """Ordena os dados da tabela ao clicar em um cabeçalho."""
        lista = [(self.tree_pessoas.set(k, coluna), k) for k in self.tree_pessoas.get_children('')]

        def get_sort_key(item):
            value = item[0]
            if coluna == 'id':
                return int(value)
            if coluna == 'is_motorista':
                return 1 if value == "Sim" else 0
            return str(value).lower()

        lista.sort(key=get_sort_key, reverse=reversa)

        for i, (val, k) in enumerate(lista):
            self.tree_pessoas.move(k, '', i)

        self.tree_pessoas.heading(coluna, command=lambda: self._ordenar_coluna(coluna, not reversa))

    def _limpar_campos(self):
        """Limpa o formulário e reseta o estado de edição."""
        self.entry_nome.delete(0, tk.END)
        self.entry_funcao.delete(0, tk.END)
        self.entry_cpf.delete(0, tk.END)
        self.entry_data_nascimento.delete(0, tk.END)
        self.entry_telefone.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_cnh.delete(0, tk.END)
        self.entry_categoria_cnh.delete(0, tk.END)
        self.is_motorista_var.set(0)

        self.id_pessoa_em_edicao = None
        self.btn_salvar.config(text="Salvar Funcionário")
        if self.tree_pessoas.selection():
            self.tree_pessoas.selection_remove(self.tree_pessoas.selection())

    def _on_pessoa_select(self, event):
        """Preenche o formulário ao selecionar um item na tabela."""
        selected_items = self.tree_pessoas.selection()
        if not selected_items: return

        item_id = self.tree_pessoas.item(selected_items[0])['values'][0]
        pessoa_obj = next((p for p in self.pessoas if p.id == item_id), None)
        if not pessoa_obj: return

        # Limpa os campos um por um antes de preencher
        self.entry_nome.delete(0, tk.END);
        self.entry_nome.insert(0, pessoa_obj.nome)
        self.entry_funcao.delete(0, tk.END);
        self.entry_funcao.insert(0, pessoa_obj.funcao)
        self.entry_cpf.delete(0, tk.END);
        self.entry_cpf.insert(0, pessoa_obj.cpf or "")
        self.entry_data_nascimento.delete(0, tk.END);
        self.entry_data_nascimento.insert(0, pessoa_obj.data_nascimento or "")
        self.entry_telefone.delete(0, tk.END);
        self.entry_telefone.insert(0, pessoa_obj.telefone or "")
        self.entry_email.delete(0, tk.END);
        self.entry_email.insert(0, pessoa_obj.email or "")
        self.entry_cnh.delete(0, tk.END);
        self.entry_cnh.insert(0, pessoa_obj.cnh or "")
        self.entry_categoria_cnh.delete(0, tk.END);
        self.entry_categoria_cnh.insert(0, pessoa_obj.categoria_cnh or "")
        self.is_motorista_var.set(pessoa_obj.is_motorista)

        self.id_pessoa_em_edicao = pessoa_obj.id
        self.btn_salvar.config(text="Atualizar Funcionário")

    def _excluir_pessoa(self):
        """Exclui a pessoa selecionada."""
        if not self.id_pessoa_em_edicao:
            messagebox.showwarning("Aviso", "Selecione um funcionário na tabela para excluir.", parent=self.window)
            return

        nome = self.entry_nome.get()
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o funcionário {nome}?",
                               parent=self.window):
            try:
                self.db_manager.delete('pessoas', self.id_pessoa_em_edicao)
                messagebox.showinfo("Sucesso", "Funcionário excluído com sucesso!", parent=self.window)
                self._limpar_campos()
                self._load_pessoas_from_db()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro de Exclusão",
                                     "Não é possível excluir este funcionário, pois ele está associado a outros registros (abastecimentos, etc.).",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao excluir: {e}", parent=self.window)

    def _salvar_pessoa(self):
        """Salva uma nova pessoa ou atualiza uma existente."""
        nome = self.entry_nome.get().strip().upper()
        funcao = self.entry_funcao.get().strip().upper()
        cpf = self.entry_cpf.get().strip()
        data_nascimento = self.entry_data_nascimento.get().strip()
        telefone = self.entry_telefone.get().strip()
        email = self.entry_email.get().strip()
        cnh = self.entry_cnh.get().strip().upper()
        categoria_cnh = self.entry_categoria_cnh.get().strip().upper()
        is_motorista = self.is_motorista_var.get()

        if not nome or not funcao:
            messagebox.showwarning("Validação", "Nome e Função são obrigatórios.", parent=self.window)
            return

        pessoa_data = Pessoa(
            nome=nome, funcao=funcao, cpf=cpf, data_nascimento=data_nascimento,
            telefone=telefone, email=email, cnh=cnh, categoria_cnh=categoria_cnh,
            is_motorista=is_motorista
        )

        try:
            if self.id_pessoa_em_edicao:
                self.db_manager.update('pessoas', self.id_pessoa_em_edicao, pessoa_data.to_dict())
                messagebox.showinfo("Sucesso", f"Funcionário '{nome}' atualizado.", parent=self.window)
            else:
                self.db_manager.insert('pessoas', pessoa_data.to_dict())
                messagebox.showinfo("Sucesso", f"Funcionário '{nome}' cadastrado.", parent=self.window)

            self._limpar_campos()
            self._load_pessoas_from_db()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe um funcionário com estes dados (ex: CPF ou Nome únicos).",
                                   parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro: {e}", parent=self.window)

    def _importar_csv(self):
        """Pede um arquivo ao usuário e usa a classe importadora para processá-lo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV de Funcionários",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not filepath:
            return

        # 1. Cria uma instância do importador
        importer = ImportadorDeFuncionarios(self.db_manager, filepath)

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
        self._load_pessoas_from_db()