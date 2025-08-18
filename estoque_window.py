import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from datetime import datetime
import sqlite3
import csv

from produto import Produto
from movimentacao_estoque import MovimentacaoEstoque
from pessoa import Pessoa
from database_manager import DatabaseManager
from tkcalendar import DateEntry


class EstoqueWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager

        self.produtos = []
        self.movimentacoes = []
        self.pessoas = []
        self.id_produto_em_edicao = None

        self.window = tk.Toplevel(parent)
        self.window.title("Controle de Estoque")
        self.window.state('zoomed')

        self._build_ui()
        self._load_all_data_and_ui()

        self.window.grab_set()
        self.parent.wait_window(self.window)



    def _build_ui(self):
        """Constrói a interface gráfica com as abas de gerenciamento."""
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        frame_gerenciar_produtos = ttk.Frame(self.notebook)
        self.notebook.add(frame_gerenciar_produtos, text="Gerenciar Produtos")
        self._build_gerenciar_produtos_tab(frame_gerenciar_produtos)

        frame_movimentar_estoque = ttk.Frame(self.notebook)
        self.notebook.add(frame_movimentar_estoque, text="Movimentar Estoque")
        self._build_movimentar_estoque_tab(frame_movimentar_estoque)

        frame_historico = ttk.Frame(self.notebook)
        self.notebook.add(frame_historico, text="Histórico de Movimentações")
        self._build_historico_movimentacoes_tab(frame_historico)

    def _build_gerenciar_produtos_tab(self, parent_frame):
        # Frame do Formulário
        frame_cadastro = tk.LabelFrame(parent_frame, text="Cadastrar/Atualizar Produto", padx=10, pady=10)
        frame_cadastro.pack(pady=10, padx=10, fill="x")
        tk.Label(frame_cadastro, text="Nome do Produto:").grid(row=0, column=0, sticky="w", pady=2)

        self.entry_produto_nome = tk.Entry(frame_cadastro, width=50)

        self.entry_produto_nome.grid(row=0, column=1, sticky="ew", pady=2)

        tk.Label(frame_cadastro, text="Descrição:").grid(row=1, column=0, sticky="w", pady=2)

        self.entry_produto_descricao = tk.Entry(frame_cadastro, width=50)

        self.entry_produto_descricao.grid(row=1, column=1, sticky="ew", pady=2)

        tk.Label(frame_cadastro, text="Qtd. em Estoque:").grid(row=2, column=0, sticky="w", pady=2)

        self.entry_produto_qtd_inicial = tk.Entry(frame_cadastro, width=20)

        self.entry_produto_qtd_inicial.grid(row=2, column=1, sticky="w", pady=2)

        self.entry_produto_qtd_inicial.insert(0, "0")

        frame_botoes_form = tk.Frame(frame_cadastro)

        frame_botoes_form.grid(row=3, column=0, columnspan=2, pady=10)

        self.btn_salvar_produto = tk.Button(frame_botoes_form, text="Salvar Produto", command=self._salvar_produto)

        self.btn_salvar_produto.pack(side=tk.LEFT, padx=5)

        btn_limpar_produto = tk.Button(frame_botoes_form, text="Limpar Campos", command=self._limpar_campos_produto)

        btn_limpar_produto.pack(side=tk.LEFT, padx=5)

        # Frame da Tabela e Busca
        frame_lista = tk.LabelFrame(parent_frame, text="Produtos Cadastrados", padx=10, pady=10)
        frame_lista.pack(pady=10, padx=10, fill="both", expand=True)

        frame_busca = tk.Frame(frame_lista)
        frame_busca.pack(pady=5, fill="x")
        tk.Label(frame_busca, text="Buscar por Nome:").pack(side=tk.LEFT)
        self.entry_busca_produto = tk.Entry(frame_busca)
        self.entry_busca_produto.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca_produto.bind("<KeyRelease>", self._filtrar_produtos_na_tabela)

        frame_tree = tk.Frame(frame_lista)
        frame_tree.pack(fill="both", expand=True)
        columns_produtos = ("id", "nome", "descricao", "quantidade_estoque")
        self.tree_produtos = ttk.Treeview(frame_tree, columns=columns_produtos, show="headings")
        cabecalhos = {"id": "ID", "nome": "Nome", "descricao": "Descrição", "quantidade_estoque": "Qtd. Estoque"}
        for col, texto in cabecalhos.items():
            self.tree_produtos.heading(col, text=texto,
                                       command=lambda c=col: self._ordenar_coluna(self.tree_produtos, c, False))
        self.tree_produtos.column("id", width=0, stretch=tk.NO)
        self.tree_produtos.column("nome", width=300)
        self.tree_produtos.column("descricao", width=400)
        self.tree_produtos.column("quantidade_estoque", width=100, anchor="center")
        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_produtos.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_produtos.bind('<<TreeviewSelect>>', self._on_produto_select)

        frame_botoes_tabela = tk.Frame(frame_lista)
        frame_botoes_tabela.pack(pady=5)
        btn_excluir_produto = tk.Button(frame_botoes_tabela, text="Excluir Selecionado", command=self._excluir_produto)
        btn_excluir_produto.pack(side=tk.LEFT, padx=5)
        btn_importar_produtos = tk.Button(frame_botoes_tabela, text="Importar de CSV",
                                          command=self._importar_produtos_csv)
        btn_importar_produtos.pack(side=tk.LEFT, padx=15)

    def _build_movimentar_estoque_tab(self, parent_frame):
        """Cria os widgets da aba 'Movimentar Estoque'."""
        frame_movimentacao = tk.LabelFrame(parent_frame, text="Registrar Movimentação", padx=10, pady=10)
        frame_movimentacao.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_movimentacao, text="Produto:").grid(row=0, column=0, sticky="w", pady=2)
        self.produto_selecionado = tk.StringVar()
        self.combobox_produtos = ttk.Combobox(frame_movimentacao, textvariable=self.produto_selecionado,
                                              state="normal", width=50)
        self.combobox_produtos.grid(row=0, column=1, sticky="ew", pady=2)
        self.combobox_produtos.bind("<KeyRelease>", self._filter_products_combobox)

        tk.Label(frame_movimentacao, text="Tipo:").grid(row=1, column=0, sticky="w", pady=2)
        self.tipo_movimentacao = tk.StringVar(value="saida")
        ttk.Radiobutton(frame_movimentacao, text="Entrada", variable=self.tipo_movimentacao, value="entrada").grid(
            row=1, column=1, sticky="w")
        ttk.Radiobutton(frame_movimentacao, text="Saída", variable=self.tipo_movimentacao, value="saida").grid(row=1,
                                                                                                               column=1,
                                                                                                               sticky="w",
                                                                                                               padx=80)

        tk.Label(frame_movimentacao, text="Quantidade:").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_qtd_movimentacao = tk.Entry(frame_movimentacao, width=20)
        self.entry_qtd_movimentacao.grid(row=2, column=1, sticky="w", pady=2)

        tk.Label(frame_movimentacao, text="Funcionário (Saída):").grid(row=3, column=0, sticky="w", pady=2)
        self.funcionario_selecionado = tk.StringVar()
        self.combobox_funcionarios = ttk.Combobox(frame_movimentacao, textvariable=self.funcionario_selecionado,
                                                  state="normal", width=50)
        self.combobox_funcionarios.grid(row=3, column=1, sticky="ew", pady=2)
        self.combobox_funcionarios.bind("<KeyRelease>", self._filter_employees_combobox)

        tk.Label(frame_movimentacao, text="Observação:").grid(row=4, column=0, sticky="w", pady=2)
        self.entry_mov_observacao = tk.Entry(frame_movimentacao, width=50)
        self.entry_mov_observacao.grid(row=4, column=1, sticky="ew", pady=2)

        btn_registrar_mov = tk.Button(frame_movimentacao, text="Registrar Movimentação",
                                      command=self._registrar_movimentacao)
        btn_registrar_mov.grid(row=5, column=0, columnspan=2, pady=5)

    def _build_historico_movimentacoes_tab(self, parent_frame):
        """Cria os widgets da aba 'Histórico de Movimentações'."""
        frame_historico_movs = tk.LabelFrame(parent_frame, text="Histórico de Movimentações", padx=10, pady=10)
        frame_historico_movs.pack(pady=10, padx=10, fill="both", expand=True)

        columns_movs = ("id", "tipo", "produto_nome", "quantidade", "data_hora", "funcionario_nome",
                        "funcionario_funcao", "observacao")
        self.tree_movimentacoes = ttk.Treeview(frame_historico_movs, columns=columns_movs, show="headings")

        self.tree_movimentacoes.heading("id", text="ID")
        self.tree_movimentacoes.heading("tipo", text="Tipo")
        self.tree_movimentacoes.heading("produto_nome", text="Produto")
        self.tree_movimentacoes.heading("quantidade", text="Qtd")
        self.tree_movimentacoes.heading("data_hora", text="Data/Hora")
        self.tree_movimentacoes.heading("funcionario_nome", text="Funcionário")
        self.tree_movimentacoes.heading("funcionario_funcao", text="Função")
        self.tree_movimentacoes.heading("observacao", text="Observação")

        self.tree_movimentacoes.column("id", width=0, stretch=tk.NO)
        self.tree_movimentacoes.column("tipo", width=70, anchor=tk.CENTER)
        self.tree_movimentacoes.column("produto_nome", width=150, anchor=tk.W)
        self.tree_movimentacoes.column("quantidade", width=60, anchor=tk.CENTER)
        self.tree_movimentacoes.column("data_hora", width=120, anchor=tk.CENTER)
        self.tree_movimentacoes.column("funcionario_nome", width=120, anchor=tk.W)
        self.tree_movimentacoes.column("funcionario_funcao", width=100, anchor=tk.W)
        self.tree_movimentacoes.column("observacao", width=250, anchor=tk.W)

        self.tree_movimentacoes.pack(fill="both", expand=True)

        scrollbar_movs = ttk.Scrollbar(frame_historico_movs, orient=tk.VERTICAL, command=self.tree_movimentacoes.yview)
        self.tree_movimentacoes.configure(yscrollcommand=scrollbar_movs.set)
        scrollbar_movs.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_all_data_and_ui(self):
        """Carrega todos os dados do banco e atualiza a interface completa."""
        self.produtos = [Produto.from_dict(row) for row in self.db_manager.fetch_all('produtos')]
        self.movimentacoes = [MovimentacaoEstoque.from_dict(row) for row in
                              self.db_manager.fetch_all('movimentacoes_estoque')]
        self.pessoas = [Pessoa.from_dict(row) for row in self.db_manager.fetch_all('pessoas')]

        self._carregar_produtos_na_tabela(self.produtos)
        self._load_movimentacoes_to_ui()
        self._load_combobox_data()

    def _carregar_produtos_na_tabela(self, lista_produtos):
        self.tree_produtos.delete(*self.tree_produtos.get_children())
        for produto in lista_produtos:
            self.tree_produtos.insert("", "end",
                                      values=(produto.id, produto.nome, produto.descricao, produto.quantidade_estoque))

    def _filtrar_produtos_na_tabela(self, event=None):
        texto_busca = self.entry_busca_produto.get().lower()
        filtrados = [p for p in self.produtos if texto_busca in p.nome.lower()]
        self._carregar_produtos_na_tabela(filtrados)


    def _salvar_produto(self):
        nome = self.entry_produto_nome.get().strip().upper()
        descricao = self.entry_produto_descricao.get().strip()
        if not nome:
            messagebox.showwarning("Validação", "Nome do produto é obrigatório.", parent=self.window)
            return

        try:
            if self.id_produto_em_edicao:
                produto_data = {'nome': nome, 'descricao': descricao}
                self.db_manager.update('produtos', self.id_produto_em_edicao, produto_data)
                messagebox.showinfo("Sucesso", f"Produto '{nome}' atualizado com sucesso!", parent=self.window)
            else:
                qtd_inicial_str = self.entry_produto_qtd_inicial.get().strip()
                quantidade_inicial = int(qtd_inicial_str) if qtd_inicial_str else 0
                novo_produto = Produto(nome=nome, descricao=descricao, quantidade_estoque=quantidade_inicial)
                self.db_manager.insert('produtos', novo_produto.to_dict())
                messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!", parent=self.window)

            self._limpar_campos_produto()
            self._load_all_data_and_ui()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe um produto com o nome '{nome}'.", parent=self.window)
        except ValueError:
            messagebox.showwarning("Validação", "Quantidade Inicial deve ser um número inteiro.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro: {e}", parent=self.window)

    def _ordenar_coluna(self, treeview, coluna, reversa):
        lista_de_dados = [(treeview.set(item_id, coluna), item_id) for item_id in treeview.get_children('')]

        colunas_numericas = ['id', 'quantidade_estoque', 'quantidade']
        if coluna in colunas_numericas:
            lista_de_dados.sort(key=lambda t: int(t[0]), reverse=reversa)
        else:
            lista_de_dados.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)

        for indice, (valor, item_id) in enumerate(lista_de_dados):
            treeview.move(item_id, '', indice)

        treeview.heading(coluna, command=lambda: self._ordenar_coluna(treeview, coluna, not reversa))



    def _limpar_campos_produto(self):
        self.entry_produto_nome.delete(0, tk.END)
        self.entry_produto_descricao.delete(0, tk.END)
        self.entry_produto_qtd_inicial.config(state="normal")
        self.entry_produto_qtd_inicial.delete(0, tk.END)
        self.entry_produto_qtd_inicial.insert(0, "0")
        self.id_produto_em_edicao = None
        self.btn_salvar_produto.config(text="Salvar Produto")
        if self.tree_produtos.selection():
            self.tree_produtos.selection_remove(self.tree_produtos.selection())

    def _on_produto_select(self, event):
        selected_items = self.tree_produtos.selection()
        if not selected_items: return
        item_id = self.tree_produtos.item(selected_items[0])['values'][0]
        produto_obj = next((p for p in self.produtos if p.id == item_id), None)
        if not produto_obj: return

        self._limpar_campos_produto()
        self.entry_produto_nome.insert(0, produto_obj.nome)
        self.entry_produto_descricao.insert(0, produto_obj.descricao)
        self.entry_produto_qtd_inicial.insert(0, str(produto_obj.quantidade_estoque))
        self.entry_produto_qtd_inicial.config(state="disabled")
        self.id_produto_em_edicao = produto_obj.id
        self.btn_salvar_produto.config(text="Atualizar Produto")

    def _registrar_movimentacao(self):
        """Registra uma movimentação de estoque de forma atômica no banco de dados."""
        # --- 1. COLETA E VALIDAÇÃO DOS DADOS DA INTERFACE ---
        produto_nome_selecionado = self.produto_selecionado.get().strip()
        tipo = self.tipo_movimentacao.get()
        qtd_str = self.entry_qtd_movimentacao.get().strip()
        funcionario_nome_selecionado = self.funcionario_selecionado.get().strip()
        observacao = self.entry_mov_observacao.get().strip()

        # Validações iniciais (fora da transação)
        if not produto_nome_selecionado or produto_nome_selecionado == "Nenhum produto cadastrado":
            messagebox.showwarning("Erro", "Selecione um produto.", parent=self.window)
            return

        try:
            quantidade = int(qtd_str)
        except ValueError:
            messagebox.showwarning("Erro", "Quantidade inválida. Digite um número inteiro.", parent=self.window)
            return

        produto_encontrado = next((p for p in self.produtos if p.nome == produto_nome_selecionado), None)
        if not produto_encontrado:
            messagebox.showerror("Erro Interno", "Produto selecionado não encontrado na lista.", parent=self.window)
            return

        pessoa_id = None
        if tipo == "saida":
            if not funcionario_nome_selecionado or funcionario_nome_selecionado == "Nenhum funcionário cadastrado":
                messagebox.showwarning("Erro", "Para saídas, selecione o funcionário.", parent=self.window)
                return

            pessoa_encontrada = next((p for p in self.pessoas if p.nome == funcionario_nome_selecionado), None)
            if not pessoa_encontrada:
                messagebox.showerror("Erro Interno", "Funcionário selecionado não encontrado na lista.",
                                     parent=self.window)
                return
            pessoa_id = pessoa_encontrada.id

        # --- 2. LÓGICA DE NEGÓCIO E TRANSAÇÃO ATÔMICA ---
        try:
            # Primeiro, tenta executar a lógica de negócio nos objetos em memória.
            # Isso pode levantar um ValueError, que será capturado abaixo.
            if tipo == "entrada":
                produto_encontrado.adicionar_estoque(quantidade)
            else:  # tipo == "saida"
                produto_encontrado.remover_estoque(quantidade)

            # Se a lógica de negócio foi bem-sucedida, executa a transação no banco.
            self.db_manager.update('produtos', produto_encontrado.id,
                                   {'quantidade_estoque': produto_encontrado.quantidade_estoque})

            # Operação 2: Cria e insere o registro da movimentação no banco
            nova_movimentacao = MovimentacaoEstoque(
                tipo=tipo,
                produto_id=produto_encontrado.id,
                quantidade=quantidade,
                pessoa_id=pessoa_id,
                observacao=observacao
            )
            self.db_manager.insert('movimentacoes_estoque', nova_movimentacao.to_dict())

            # --- 3. SUCESSO ---
            # Se chegamos aqui, o bloco 'with' terminou sem erros e fez o commit.
            messagebox.showinfo("Sucesso", "Movimentação registrada com sucesso!", parent=self.window)

            # Limpa os campos da interface e recarrega os dados
            self.produto_selecionado.set("")
            self.entry_qtd_movimentacao.delete(0, tk.END)
            self.funcionario_selecionado.set("")
            self.entry_mov_observacao.delete(0, tk.END)
            self._load_all_data_and_ui()

        except ValueError as e:
            # Captura erros de validação da lógica de negócio (ex: estoque insuficiente).
            messagebox.showwarning("Erro de Validação", str(e), parent=self.window)
        except sqlite3.Error as e:
            # Captura erros específicos do banco de dados. O rollback já foi feito.
            messagebox.showerror("Erro de Banco de Dados", f"A operação falhou e foi revertida: {e}",
                                 parent=self.window)
        except Exception as e:
            # Captura qualquer outro erro inesperado. O rollback já foi feito.
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado: {e}", parent=self.window)

    def _load_produtos_to_ui(self):
        for produto in self.produtos:
            self.tree_produtos.insert("", tk.END, values=(
                produto.id,
                produto.nome,
                produto.descricao,
                produto.quantidade_estoque
            ))

    def _excluir_produto(self):
        if not self.id_produto_em_edicao:
            messagebox.showwarning("Aviso", "Selecione um produto para excluir.", parent=self.window)
            return

        nome_produto = self.entry_produto_nome.get()
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o produto '{nome_produto}'?",
                               parent=self.window):
            try:
                self.db_manager.delete('produtos', self.id_produto_em_edicao)
                messagebox.showinfo("Sucesso", "Produto excluído com sucesso!", parent=self.window)
                self._limpar_campos_produto()
                self._load_all_data_and_ui()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro",
                                     "Não é possível excluir este produto, pois ele possui movimentações de estoque registradas.",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao excluir: {e}", parent=self.window)

    def _load_movimentacoes_to_ui(self):
        """Atualiza a tabela de histórico de movimentações na interface."""
        self.tree_movimentacoes.delete(*self.tree_movimentacoes.get_children())
        for mov in self.movimentacoes:
            produto_nome = next((p.nome for p in self.produtos if p.id == mov.produto_id), "N/A")
            funcionario_nome, funcionario_funcao = "N/A", "N/A"
            if mov.pessoa_id:
                pessoa = next((p for p in self.pessoas if p.id == mov.pessoa_id), None)
                if pessoa:
                    funcionario_nome = pessoa.nome
                    funcionario_funcao = pessoa.funcao if pessoa.funcao else "Não Informada"

            self.tree_movimentacoes.insert("", tk.END, values=(
                mov.id,
                mov.tipo.capitalize(),
                produto_nome,
                mov.quantidade,
                mov.data_hora.strftime('%d/%m/%Y %H:%M:%S'),
                funcionario_nome,
                funcionario_funcao,
                mov.observacao
            ))

    def _importar_produtos_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if not filepath: return
        sucesso, erros, duplicados = 0, 0, 0
        try:
            with open(filepath, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        produto_data = Produto(
                            nome=row.get('nome', '').strip().upper(),
                            descricao=row.get('descricao', '').strip(),
                            quantidade_estoque=int(row.get('quantidade_estoque', 0))
                        )
                        if not produto_data.nome:
                            erros += 1;
                            continue

                        self.db_manager.insert('produtos', produto_data.to_dict())
                        sucesso += 1
                    except sqlite3.IntegrityError:
                        duplicados += 1
                    except (ValueError, TypeError):
                        erros += 1

            messagebox.showinfo("Importação Concluída", f"Sucesso: {sucesso}\nDuplicados: {duplicados}\nErros: {erros}")
            self._load_all_data_and_ui()
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo.\nErro: {e}")

    def _load_combobox_data(self):
        """Carrega os nomes dos produtos e funcionários e preenche os ComboBoxes."""
        self.all_product_names = sorted([p.nome for p in self.produtos])
        self.all_employee_names = sorted([p.nome for p in self.pessoas])

        # Preenche o ComboBox de produtos
        self.combobox_produtos['values'] = self.all_product_names
        self.combobox_produtos.set("")
        if not self.all_product_names:
            self.combobox_produtos.set("Nenhum produto cadastrado")

        # Preenche o ComboBox de funcionários
        if self.all_employee_names:
            self.combobox_funcionarios['values'] = self.all_employee_names
            self.combobox_funcionarios.set("")
            self.combobox_funcionarios.config(state="normal")
        else:
            self.combobox_funcionarios['values'] = []
            self.combobox_funcionarios.set("Nenhum funcionário cadastrado")
            self.combobox_funcionarios.config(state="disabled")

    def _filter_products_combobox(self, event):
        """Filtra a lista de produtos no ComboBox."""
        typed_text = self.produto_selecionado.get().strip().lower()
        if not typed_text:
            self.combobox_produtos['values'] = self.all_product_names
        else:
            filtered_names = [name for name in self.all_product_names if typed_text in name.lower()]
            self.combobox_produtos['values'] = filtered_names

    def _filter_employees_combobox(self, event):
        """Filtra a lista de funcionários no ComboBox."""
        typed_text = self.funcionario_selecionado.get().strip().lower()
        if not typed_text:
            self.combobox_funcionarios['values'] = self.all_employee_names
        else:
            filtered_names = [name for name in self.all_employee_names if typed_text in name.lower()]
            self.combobox_funcionarios['values'] = filtered_names