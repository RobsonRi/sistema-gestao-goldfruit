import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox, filedialog
from importadores import ImportadorDeTransportadoras, ImportadorDeLocalidades
from transportadora import Transportadora
from localidade import Localidade
from preco_frete import PrecoFrete
from database_manager import DatabaseManager
from firebase_admin import firestore


class GerenciarFretesWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager

        # Listas de dados
        self.transportadoras = []
        self.localidades = []

        # Variáveis de estado para edição
        self.id_transportadora_em_edicao = None
        self.id_localidade_em_edicao = None

        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Fretes")
        self.window.state('zoomed')

        self._build_ui()
        self._load_all_data()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        frame_transportadoras = ttk.Frame(self.notebook)
        self.notebook.add(frame_transportadoras, text="Transportadoras")
        self._build_transportadoras_tab(frame_transportadoras)

        frame_localidades = ttk.Frame(self.notebook)
        self.notebook.add(frame_localidades, text="Localidades")
        self._build_localidades_tab(frame_localidades)

        frame_precos = ttk.Frame(self.notebook)
        self.notebook.add(frame_precos, text="Tabela de Preços")
        self._build_precos_tab(frame_precos)

    def _load_all_data(self):
        """Carrega/recarrega todos os dados para todas as abas."""
        self._load_transportadoras_from_db()
        self._load_localidades_from_db()
        self._load_precos_to_ui()

    def _ordenar_coluna(self, treeview, coluna, reversa):
        """Função genérica para ordenar qualquer Treeview na janela."""
        lista_de_dados = [(treeview.set(item_id, coluna), item_id) for item_id in treeview.get_children('')]
        colunas_numericas = ['id', 'valor', 'valor_truck', 'valor_toco', 'valor_3_4']

        if coluna in colunas_numericas:
            try:
                lista_de_dados.sort(key=lambda t: float(str(t[0]).replace('R$', '').replace(',', '.').strip()),
                                    reverse=reversa)
            except (ValueError, TypeError):
                pass
        else:
            lista_de_dados.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)

        for indice, (valor, item_id) in enumerate(lista_de_dados):
            treeview.move(item_id, '', indice)

        treeview.heading(coluna, command=lambda: self._ordenar_coluna(treeview, coluna, not reversa))

    # ===================================================================
    # --- MÉTODOS DA ABA DE TRANSPORTADORAS ---
    # ===================================================================
    def _build_transportadoras_tab(self, parent_frame):
        form_frame = tk.LabelFrame(parent_frame, text="Cadastrar/Atualizar Transportadora", padx=10, pady=10)
        form_frame.pack(pady=10, padx=10, fill="x")
        tk.Label(form_frame, text="Nome:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_transp_nome = tk.Entry(form_frame, width=40)
        self.entry_transp_nome.grid(row=0, column=1, sticky="ew", pady=2)
        tk.Label(form_frame, text="Telefone:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_transp_telefone = tk.Entry(form_frame, width=40)
        self.entry_transp_telefone.grid(row=1, column=1, sticky="ew", pady=2)
        tk.Label(form_frame, text="Contato:").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_transp_contato = tk.Entry(form_frame, width=40)
        self.entry_transp_contato.grid(row=2, column=1, sticky="ew", pady=2)
        botoes_form_frame = tk.Frame(form_frame)
        botoes_form_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.btn_salvar_transp = tk.Button(botoes_form_frame, text="Salvar", command=self._salvar_transportadora)
        self.btn_salvar_transp.pack(side=tk.LEFT, padx=5)
        btn_limpar_transp = tk.Button(botoes_form_frame, text="Limpar", command=self._limpar_campos_transportadora)
        btn_limpar_transp.pack(side=tk.LEFT, padx=5)

        tabela_frame = tk.LabelFrame(parent_frame, text="Transportadoras Cadastradas", padx=10, pady=10)
        tabela_frame.pack(pady=10, padx=10, fill="both", expand=True)
        frame_busca = tk.Frame(tabela_frame)
        frame_busca.pack(pady=5, fill="x")
        tk.Label(frame_busca, text="Buscar por Nome:").pack(side=tk.LEFT)
        self.entry_busca_transp = tk.Entry(frame_busca)
        self.entry_busca_transp.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca_transp.bind("<KeyRelease>", self._filtrar_transportadoras_na_tabela)

        frame_tree = tk.Frame(tabela_frame)
        frame_tree.pack(fill="both", expand=True)
        cols = ("id", "nome", "telefone", "contato")
        self.tree_transportadoras = ttk.Treeview(frame_tree, columns=cols, show="headings")
        cabecalhos = {"id": "ID", "nome": "Nome", "telefone": "Telefone", "contato": "Contato"}
        for col, texto in cabecalhos.items():
            self.tree_transportadoras.heading(col, text=texto,
                                              command=lambda c=col: self._ordenar_coluna(self.tree_transportadoras, c,
                                                                                         False))
        self.tree_transportadoras.column("id", width=0, stretch=tk.NO)
        self.tree_transportadoras.column("nome", width=300)
        self.tree_transportadoras.column("telefone", width=150, anchor="center")
        self.tree_transportadoras.column("contato", width=200)

        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_transportadoras.yview)
        self.tree_transportadoras.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_transportadoras.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_transportadoras.bind("<<TreeviewSelect>>", self._on_transportadora_select)

        botoes_tabela_frame = tk.Frame(tabela_frame)
        botoes_tabela_frame.pack(pady=5)
        btn_excluir_transp = tk.Button(botoes_tabela_frame, text="Excluir Selecionada",
                                       command=self._excluir_transportadora)
        btn_excluir_transp.pack(side=tk.LEFT, padx=5)
        btn_importar_transp = tk.Button(botoes_tabela_frame, text="Importar de CSV",
                                        command=self._importar_transportadoras_csv)
        btn_importar_transp.pack(side=tk.LEFT, padx=15)

    def _load_transportadoras_from_db(self):
        self.transportadoras = [Transportadora.from_dict(row) for row in self.db_manager.fetch_all('transportadoras')]
        self._carregar_transportadoras_na_tabela(self.transportadoras)

    def _carregar_transportadoras_na_tabela(self, lista):
        self.tree_transportadoras.delete(*self.tree_transportadoras.get_children())
        for transp in lista:
            self.tree_transportadoras.insert("", tk.END, values=(transp.id, transp.nome, transp.telefone or "",
                                                                 transp.contato or ""))

    def _filtrar_transportadoras_na_tabela(self, event=None):
        texto = self.entry_busca_transp.get().lower()
        filtrados = self.transportadoras if not texto else [t for t in self.transportadoras if texto in t.nome.lower()]
        self._carregar_transportadoras_na_tabela(filtrados)

    def _limpar_campos_transportadora(self):
        self.entry_transp_nome.delete(0, tk.END)
        self.entry_transp_telefone.delete(0, tk.END)
        self.entry_transp_contato.delete(0, tk.END)
        self.id_transportadora_em_edicao = None
        self.btn_salvar_transp.config(text="Salvar")
        if self.tree_transportadoras.selection():
            self.tree_transportadoras.selection_remove(self.tree_transportadoras.selection())

    def _on_transportadora_select(self, event):
        selected = self.tree_transportadoras.selection()
        if not selected: return
        item_id = self.tree_transportadoras.item(selected[0], "values")[0]
        transp_obj = next((t for t in self.transportadoras if t.id == item_id), None)
        if not transp_obj: return
        self.entry_transp_nome.delete(0, tk.END);
        self.entry_transp_nome.insert(0, transp_obj.nome)
        self.entry_transp_telefone.delete(0, tk.END);
        self.entry_transp_telefone.insert(0, transp_obj.telefone or "")
        self.entry_transp_contato.delete(0, tk.END);
        self.entry_transp_contato.insert(0, transp_obj.contato or "")
        self.id_transportadora_em_edicao = item_id
        self.btn_salvar_transp.config(text="Atualizar")

    def _salvar_transportadora(self):
        nome = self.entry_transp_nome.get().strip().upper()
        telefone = self.entry_transp_telefone.get().strip()
        contato = self.entry_transp_contato.get().strip().upper()
        if not nome:
            messagebox.showwarning("Validação", "O nome da transportadora é obrigatório.", parent=self.window)
            return
        transp = Transportadora(nome, telefone, contato)
        try:
            if self.id_transportadora_em_edicao:
                self.db_manager.update('transportadoras', self.id_transportadora_em_edicao, transp.to_dict())
                messagebox.showinfo("Sucesso", "Transportadora atualizada com sucesso.", parent=self.window)
            else:
                self.db_manager.insert('transportadoras', transp.to_dict())
                messagebox.showinfo("Sucesso", "Transportadora cadastrada com sucesso.", parent=self.window)
            self._limpar_campos_transportadora()
            self._load_all_data()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe uma transportadora com o nome '{nome}'.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.window)

    def _excluir_transportadora(self):
        if not self.id_transportadora_em_edicao:
            messagebox.showwarning("Aviso", "Selecione uma transportadora para excluir.", parent=self.window)
            return
        nome = self.entry_transp_nome.get()
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir a transportadora '{nome}'?",
                               parent=self.window):
            try:
                self.db_manager.delete('transportadoras', self.id_transportadora_em_edicao)
                self._limpar_campos_transportadora()
                self._load_all_data()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro",
                                     "Não é possível excluir. Transportadora associada a preços de frete ou viagens.",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.window)

    def _build_localidades_tab(self, parent_frame):
        form_frame = tk.LabelFrame(parent_frame, text="Cadastrar/Atualizar Localidade", padx=10, pady=10)
        form_frame.pack(pady=10, padx=10, fill="x")

        tk.Label(form_frame, text="Nome (Ex: Fazenda X):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_loc_nome = tk.Entry(form_frame, width=40)
        self.entry_loc_nome.grid(row=0, column=1, sticky="ew", pady=2)
        tk.Label(form_frame, text="Cidade:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_loc_cidade = tk.Entry(form_frame, width=40)
        self.entry_loc_cidade.grid(row=1, column=1, sticky="ew", pady=2)
        tk.Label(form_frame, text="Estado (UF):").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_loc_estado = tk.Entry(form_frame, width=40)
        self.entry_loc_estado.grid(row=2, column=1, sticky="ew", pady=2)

        botoes_form_frame = tk.Frame(form_frame)
        botoes_form_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.btn_salvar_loc = tk.Button(botoes_form_frame, text="Salvar", command=self._salvar_localidade)
        self.btn_salvar_loc.pack(side=tk.LEFT, padx=5)
        btn_limpar_loc = tk.Button(botoes_form_frame, text="Limpar", command=self._limpar_campos_localidade)
        btn_limpar_loc.pack(side=tk.LEFT, padx=5)

        tabela_frame = tk.LabelFrame(parent_frame, text="Localidades Cadastradas", padx=10, pady=10)
        tabela_frame.pack(pady=10, padx=10, fill="both", expand=True)

        frame_busca_loc = tk.Frame(tabela_frame)
        frame_busca_loc.pack(pady=5, fill="x")
        tk.Label(frame_busca_loc, text="Buscar por Nome/Cidade:").pack(side=tk.LEFT)
        self.entry_busca_loc = tk.Entry(frame_busca_loc)
        self.entry_busca_loc.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca_loc.bind("<KeyRelease>", self._filtrar_localidades_na_tabela)

        frame_tree_loc = tk.Frame(tabela_frame)
        frame_tree_loc.pack(fill="both", expand=True)

        cols = ("id", "nome", "cidade", "estado")
        self.tree_localidades = ttk.Treeview(frame_tree_loc, columns=cols, show="headings")
        cabecalhos = {"id": "ID", "nome": "Nome", "cidade": "Cidade", "estado": "Estado"}
        for col, texto in cabecalhos.items():
            self.tree_localidades.heading(col, text=texto,
                                          command=lambda c=col: self._ordenar_coluna(self.tree_localidades, c, False))
        self.tree_localidades.column("id", width=0, stretch=tk.NO,anchor="center")
        self.tree_localidades.column("nome", width=80,anchor="center")
        self.tree_localidades.column("cidade", width=200,anchor="center")
        self.tree_localidades.column("estado", width=80, anchor="center")

        scrollbar_loc = ttk.Scrollbar(frame_tree_loc, orient=tk.VERTICAL, command=self.tree_localidades.yview)
        self.tree_localidades.configure(yscroll=scrollbar_loc.set)
        scrollbar_loc.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_localidades.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_localidades.bind("<<TreeviewSelect>>", self._on_localidade_select)

        botoes_tabela_frame = tk.Frame(tabela_frame)
        botoes_tabela_frame.pack(pady=5)
        btn_excluir_loc = tk.Button(botoes_tabela_frame, text="Excluir Selecionada", command=self._excluir_localidade)
        btn_excluir_loc.pack(side=tk.LEFT, padx=5)
        btn_importar_loc = tk.Button(botoes_tabela_frame, text="Importar de CSV",
                                     command=self._importar_localidades_csv)
        btn_importar_loc.pack(side=tk.LEFT, padx=15)

    def _load_localidades_from_db(self):
        self.localidades = [Localidade.from_dict(row) for row in self.db_manager.fetch_all('localidades')]
        self._carregar_localidades_na_tabela(self.localidades)

    def _carregar_localidades_na_tabela(self, lista):
        self.tree_localidades.delete(*self.tree_localidades.get_children())
        for loc in lista:
            self.tree_localidades.insert("", tk.END, values=(loc.id, loc.nome, loc.cidade or "", loc.estado or ""))

    def _filtrar_localidades_na_tabela(self, event=None):
        texto = self.entry_busca_loc.get().lower()
        filtrados = self.localidades if not texto else [loc for loc in self.localidades if
                                                        texto in loc.nome.lower() or texto in (
                                                                    loc.cidade or "").lower()]
        self._carregar_localidades_na_tabela(filtrados)

    def _limpar_campos_localidade(self):
        self.entry_loc_nome.delete(0, tk.END)
        self.entry_loc_cidade.delete(0, tk.END)
        self.entry_loc_estado.delete(0, tk.END)
        self.id_localidade_em_edicao = None
        self.btn_salvar_loc.config(text="Salvar")
        if self.tree_localidades.selection():
            self.tree_localidades.selection_remove(self.tree_localidades.selection())

    def _on_localidade_select(self, event):
        selected = self.tree_localidades.selection()
        if not selected: return
        item_id = self.tree_localidades.item(selected[0], "values")[0]
        loc_obj = next((loc for loc in self.localidades if loc.id == item_id), None)
        if not loc_obj: return
        self.entry_loc_nome.delete(0, tk.END);
        self.entry_loc_nome.insert(0, loc_obj.nome)
        self.entry_loc_cidade.delete(0, tk.END);
        self.entry_loc_cidade.insert(0, loc_obj.cidade or "")
        self.entry_loc_estado.delete(0, tk.END);
        self.entry_loc_estado.insert(0, loc_obj.estado or "")
        self.id_localidade_em_edicao = item_id
        self.btn_salvar_loc.config(text="Atualizar")

    def _salvar_localidade(self):
        nome = self.entry_loc_nome.get().strip().upper()
        cidade = self.entry_loc_cidade.get().strip().upper()
        estado = self.entry_loc_estado.get().strip().upper()
        if not nome:
            messagebox.showwarning("Validação", "O nome da localidade é obrigatório.", parent=self.window)
            return
        loc = Localidade(nome, cidade, estado)
        try:
            if self.id_localidade_em_edicao:
                self.db_manager.update('localidades', self.id_localidade_em_edicao, loc.to_dict())
                messagebox.showinfo("Sucesso", "Localidade atualizada com sucesso.", parent=self.window)
            else:
                new_loc_id = self.db_manager.insert('localidades', loc.to_dict())
                self.db_manager.insert('tabela_precos_frete', {'localidade_id': new_loc_id})
                messagebox.showinfo("Sucesso", "Localidade cadastrada com sucesso.", parent=self.window)
            self._limpar_campos_localidade()
            self._load_all_data()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe uma localidade com o nome '{nome}'.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}", parent=self.window)

    def _excluir_localidade(self):
        if not self.id_localidade_em_edicao:
            messagebox.showwarning("Aviso", "Selecione uma localidade para excluir.", parent=self.window)
            return

        nome = self.entry_loc_nome.get()
        if messagebox.askyesno("Confirmar", f"Tem certeza que deseja excluir a localidade '{nome}' e seus preços?",
                               parent=self.window):
            try:
                # --- A LÓGICA DE BUSCA FOI ATUALIZADA AQUI ---
                precos_ref = self.db_manager.db.collection('tabela_precos_frete')

                # Usando a nova sintaxe com FieldFilter
                query = precos_ref.where(
                    filter=firestore.FieldFilter('localidade_id', '==', self.id_localidade_em_edicao)
                ).limit(1)

                docs = query.stream()
                # ----------------------------------------------------

                batch = self.db_manager.db.batch()

                for doc in docs:
                    batch.delete(doc.reference)
                    break

                loc_ref = self.db_manager.db.collection('localidades').document(self.id_localidade_em_edicao)
                batch.delete(loc_ref)
                batch.commit()

                messagebox.showinfo("Sucesso", "Localidade e preços associados foram excluídos.", parent=self.window)
                self._limpar_campos_localidade()
                self._load_all_data()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Não é possível excluir, localidade associada a viagens já registradas.",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao excluir: {e}", parent=self.window)

    # ===================================================================
    # --- MÉTODOS DA ABA DE TABELA DE PREÇOS ---
    # ===================================================================
    def _build_precos_tab(self, parent_frame):
        tabela_frame = tk.LabelFrame(parent_frame, text="Preços de Frete por Localidade", padx=10, pady=10)
        tabela_frame.pack(pady=10, padx=10, fill="both", expand=True)

        frame_tree_preco = tk.Frame(tabela_frame)
        frame_tree_preco.pack(fill="both", expand=True)

        cols = ("id", "localidade", "valor_truck", "valor_toco", "valor_3_4")
        self.tree_precos = ttk.Treeview(frame_tree_preco, columns=cols, show="headings")

        cabecalhos_preco = {
            "localidade": "Destino", "valor_truck": "Caminhão Truck (R$)",
            "valor_toco": "Caminhão Toco (R$)", "valor_3_4": "Caminhão 3/4 (R$)"
        }
        self.tree_precos.column("id", width=0, stretch=tk.NO)
        for col, texto in cabecalhos_preco.items():
            self.tree_precos.heading(col, text=texto,
                                     command=lambda c=col: self._ordenar_coluna(self.tree_precos, c, False))

        self.tree_precos.column("localidade", width=300)
        self.tree_precos.column("valor_truck", width=150, anchor="e")
        self.tree_precos.column("valor_toco", width=150, anchor="e")
        self.tree_precos.column("valor_3_4", width=150, anchor="e")

        scrollbar_preco = ttk.Scrollbar(frame_tree_preco, orient=tk.VERTICAL, command=self.tree_precos.yview)
        self.tree_precos.configure(yscroll=scrollbar_preco.set)
        scrollbar_preco.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_precos.pack(side=tk.LEFT, fill="both", expand=True)

        btn_editar_preco = tk.Button(tabela_frame, text="Editar Preços da Localidade Selecionada",
                                     command=self._abrir_janela_edicao_preco)
        btn_editar_preco.pack(pady=10)

    def _load_precos_to_ui(self):
        precos_data = self.db_manager.fetch_precos_frete_com_detalhes()
        self.tree_precos.delete(*self.tree_precos.get_children())
        for row in precos_data:
            self.tree_precos.insert("", tk.END, values=(
                row['id'], row['localidade_nome'], f"{row['valor_truck']:.2f}",
                f"{row['valor_toco']:.2f}", f"{row['valor_3_4']:.2f}"
            ))

    def _abrir_janela_edicao_preco(self):
        selected_items = self.tree_precos.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Por favor, selecione uma localidade na tabela para editar.",
                                   parent=self.window)
            return

        item_values = self.tree_precos.item(selected_items[0], "values")
        preco_id, localidade_nome, val_truck, val_toco, val_3_4 = item_values

        edit_window = tk.Toplevel(self.window)
        edit_window.title(f"Editar Preços - {localidade_nome}")
        edit_window.geometry("400x200")
        edit_window.transient(self.window)
        edit_window.grab_set()

        frame = tk.Frame(edit_window, padx=15, pady=15)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Caminhão Truck (R$):").grid(row=0, column=0, sticky="w", pady=5)
        entry_truck = tk.Entry(frame)
        entry_truck.grid(row=0, column=1, pady=5)
        entry_truck.insert(0, val_truck.replace('.', ','))

        tk.Label(frame, text="Caminhão Toco (R$):").grid(row=1, column=0, sticky="w", pady=5)
        entry_toco = tk.Entry(frame)
        entry_toco.grid(row=1, column=1, pady=5)
        entry_toco.insert(0, val_toco.replace('.', ','))

        tk.Label(frame, text="Caminhão 3/4 (R$):").grid(row=2, column=0, sticky="w", pady=5)
        entry_3_4 = tk.Entry(frame)
        entry_3_4.grid(row=2, column=1, pady=5)
        entry_3_4.insert(0, val_3_4.replace('.', ','))

        btn_salvar = tk.Button(frame, text="Salvar Alterações",
                               command=lambda: self._salvar_precos_editados(
                                   preco_id, entry_truck.get(), entry_toco.get(),
                                   entry_3_4.get(), edit_window
                               ))
        btn_salvar.grid(row=3, column=0, columnspan=2, pady=15)

    def _salvar_precos_editados(self, preco_id, val_truck_str, val_toco_str, val_3_4_str, edit_window):
        try:
            dados = {
                "valor_truck": float(val_truck_str.replace(',', '.')),
                "valor_toco": float(val_toco_str.replace(',', '.')),
                "valor_3_4": float(val_3_4_str.replace(',', '.'))
            }
        except ValueError:
            messagebox.showerror("Erro de Formato", "Por favor, insira apenas números válidos.", parent=edit_window)
            return

        try:
            self.db_manager.update('tabela_precos_frete', preco_id, dados)
            edit_window.destroy()
            messagebox.showinfo("Sucesso", "Preços atualizados com sucesso!", parent=self.window)
            self._load_all_data()
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar as alterações: {e}", parent=edit_window)

    def _importar_transportadoras_csv(self):
        """Pede um arquivo ao usuário e usa a classe importadora para processá-lo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV de Transportadoras",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not filepath:
            return

        importer = ImportadorDeTransportadoras(self.db_manager, filepath)
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

        self._load_transportadoras_from_db()

    def _importar_localidades_csv(self):
        """Pede um arquivo ao usuário e usa a classe importadora para processá-lo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV de Localidades",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not filepath:
            return

        importer = ImportadorDeLocalidades(self.db_manager, filepath)
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

        self._load_localidades_from_db()
        self._load_all_data()  # Recarrega tudo para a aba de preços atualizar
