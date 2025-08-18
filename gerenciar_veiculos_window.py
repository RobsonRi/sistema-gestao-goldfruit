import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import sqlite3
import csv
from importadores import ImportadorDeVeiculos

from veiculo import Veiculo
from transportadora import Transportadora
from database_manager import DatabaseManager


class GerenciarVeiculosWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager

        self.transportadoras = [Transportadora.from_dict(row) for row in self.db_manager.fetch_all('transportadoras')]

        self.veiculos = []
        self.id_veiculo_em_edicao = None

        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Frota de Veículos")
        self.window.state('zoomed')

        self._build_ui()
        self._load_veiculos_from_db()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        # Frame do Formulário
        frame_cadastro = tk.LabelFrame(self.window, text="Cadastrar/Atualizar Veículo", padx=10, pady=10)
        frame_cadastro.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_cadastro, text="Propriedade:").grid(row=0, column=0, sticky="w", pady=5)
        self.propriedade_var = tk.StringVar(value='PROPRIO')
        frame_radio = tk.Frame(frame_cadastro)
        frame_radio.grid(row=0, column=1, sticky="w", pady=2)
        tk.Radiobutton(frame_radio, text="Próprio", variable=self.propriedade_var, value='PROPRIO',
                       command=self._toggle_transportadora_combo).pack(side=tk.LEFT)
        tk.Radiobutton(frame_radio, text="De Terceiro", variable=self.propriedade_var, value='TERCEIRO',
                       command=self._toggle_transportadora_combo).pack(side=tk.LEFT, padx=10)

        tk.Label(frame_cadastro, text="Transportadora:").grid(row=0, column=2, padx=(10, 0), sticky="w", pady=2)
        nomes_transportadoras = [t.nome for t in self.transportadoras]
        self.combo_transportadora = ttk.Combobox(frame_cadastro, values=nomes_transportadoras, state="disabled")
        self.combo_transportadora.grid(row=0, column=3, sticky="ew", pady=2)

        tk.Label(frame_cadastro, text="Placa:").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_placa = tk.Entry(frame_cadastro)
        self.entry_placa.grid(row=1, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Marca:").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_marca = tk.Entry(frame_cadastro)
        self.entry_marca.grid(row=2, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Modelo:").grid(row=3, column=0, sticky="w", pady=2)
        self.entry_modelo = tk.Entry(frame_cadastro)
        self.entry_modelo.grid(row=3, column=1, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Ano:").grid(row=1, column=2, padx=(10, 0), sticky="w", pady=2)
        self.entry_ano = tk.Entry(frame_cadastro)
        self.entry_ano.grid(row=1, column=3, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Cor:").grid(row=2, column=2, padx=(10, 0), sticky="w", pady=2)
        self.entry_cor = tk.Entry(frame_cadastro)
        self.entry_cor.grid(row=2, column=3, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Km Atual:").grid(row=3, column=2, padx=(10, 0), sticky="w", pady=2)
        self.entry_km_atual = tk.Entry(frame_cadastro)
        self.entry_km_atual.grid(row=3, column=3, sticky="ew", pady=2)
        tk.Label(frame_cadastro, text="Tipo de Combustível:").grid(row=4, column=0, sticky="w", pady=2)
        self.combobox_combustivel = ttk.Combobox(frame_cadastro, values=["Gasolina", "Etanol", "Diesel", "Flex"],
                                                 state="readonly")
        self.combobox_combustivel.grid(row=4, column=1, sticky="ew", pady=2)

        frame_botoes_form = tk.Frame(frame_cadastro)
        frame_botoes_form.grid(row=5, column=0, columnspan=4, pady=10)
        self.btn_salvar = tk.Button(frame_botoes_form, text="Salvar Veículo", command=self._salvar_veiculo)
        self.btn_salvar.pack(side=tk.LEFT, padx=5)
        btn_limpar = tk.Button(frame_botoes_form, text="Limpar Campos", command=self._limpar_campos)
        btn_limpar.pack(side=tk.LEFT, padx=5)

        # Frame da Tabela
        frame_lista = tk.LabelFrame(self.window, text="Veículos Cadastrados", padx=10, pady=10)
        frame_lista.pack(pady=10, padx=10, fill="both", expand=True)

        frame_busca = tk.Frame(frame_lista)
        frame_busca.pack(pady=5, fill="x")
        tk.Label(frame_busca, text="Buscar por Placa ou Modelo:").pack(side=tk.LEFT)
        self.entry_busca_veiculo = tk.Entry(frame_busca)
        self.entry_busca_veiculo.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca_veiculo.bind("<KeyRelease>", self._filtrar_veiculos_na_tabela)

        frame_tree = tk.Frame(frame_lista)
        frame_tree.pack(fill="both", expand=True)
        columns = ("id", "placa", "modelo", "tipo_propriedade", "transportadora_nome")
        self.tree_veiculos = ttk.Treeview(frame_tree, columns=columns, show="headings")

        cabecalhos = {"id": "ID", "placa": "Placa", "modelo": "Modelo", "tipo_propriedade": "Propriedade",
                      "transportadora_nome": "Transportadora"}
        for col, texto in cabecalhos.items():
            self.tree_veiculos.heading(col, text=texto, command=lambda c=col: self._ordenar_coluna(c, False))

        self.tree_veiculos.column("id", width=0, stretch=tk.NO)
        self.tree_veiculos.column("placa", width=100, anchor="center")
        self.tree_veiculos.column("modelo", width=200)
        self.tree_veiculos.column("tipo_propriedade", width=100, anchor="center")
        self.tree_veiculos.column("transportadora_nome", width=200)

        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_veiculos.yview)
        self.tree_veiculos.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_veiculos.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_veiculos.bind('<<TreeviewSelect>>', self._on_veiculo_select)

        frame_botoes_tabela = tk.Frame(frame_lista)
        frame_botoes_tabela.pack(pady=5)
        btn_excluir = tk.Button(frame_botoes_tabela, text="Excluir Selecionado", command=self._excluir_veiculo)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        btn_importar_csv = tk.Button(frame_botoes_tabela, text="Importar de CSV", command=self._importar_csv)
        btn_importar_csv.pack(side=tk.LEFT, padx=15)

    def _load_veiculos_from_db(self):
        self.veiculos = [Veiculo.from_dict(row) for row in self.db_manager.fetch_all('veiculos')]
        self._carregar_veiculos_na_tabela(self.veiculos)

    def _carregar_veiculos_na_tabela(self, lista_veiculos):
        self.tree_veiculos.delete(*self.tree_veiculos.get_children())
        transp_lookup = {t.id: t.nome for t in self.transportadoras}

        # Usamos enumerate para ter o contador 'i'
        for i, v in enumerate(lista_veiculos):
            nome_transportadora = transp_lookup.get(v.transportadora_id, "") if v.tipo_propriedade == 'TERCEIRO' else ""

            # Decide qual tag de cor usar
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'

            # Adiciona a tag ao inserir a linha
            self.tree_veiculos.insert("", "end",
                                      values=(v.id, v.placa, v.modelo, v.tipo_propriedade, nome_transportadora),
                                      tags=(tag,))

    def _filtrar_veiculos_na_tabela(self, event=None):
        texto = self.entry_busca_veiculo.get().lower()
        if not texto:
            filtrados = self.veiculos
        else:
            filtrados = [v for v in self.veiculos if texto in v.placa.lower() or texto in v.modelo.lower()]
        self._carregar_veiculos_na_tabela(filtrados)

    def _ordenar_coluna(self, coluna, reversa):
        # AQUI ESTÁ A CORREÇÃO DO ERRO DE DIGITAÇÃO
        lista = [(self.tree_veiculos.set(k, coluna), k) for k in self.tree_veiculos.get_children('')]

        # Lógica de ordenação (números vs. texto)
        if coluna == 'id' or coluna == 'ano':
            lista.sort(key=lambda t: int(t[0]), reverse=reversa)
        else:
            lista.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)

        for i, (val, k) in enumerate(lista):
            self.tree_veiculos.move(k, '', i)

        self.tree_veiculos.heading(coluna, command=lambda: self._ordenar_coluna(coluna, not reversa))

    def _toggle_transportadora_combo(self):
        if self.propriedade_var.get() == 'TERCEIRO':
            self.combo_transportadora.config(state="readonly")
        else:
            self.combo_transportadora.set('')
            self.combo_transportadora.config(state="disabled")

    def _limpar_campos(self):
        self.entry_placa.delete(0, tk.END)
        self.entry_marca.delete(0, tk.END)
        self.entry_modelo.delete(0, tk.END)
        self.entry_ano.delete(0, tk.END)
        self.entry_cor.delete(0, tk.END)
        self.combobox_combustivel.set('')
        self.entry_km_atual.delete(0, tk.END)
        self.propriedade_var.set('PROPRIO')
        self._toggle_transportadora_combo()

        self.id_veiculo_em_edicao = None
        self.btn_salvar.config(text="Salvar Veículo")
        if self.tree_veiculos.selection():
            self.tree_veiculos.selection_remove(self.tree_veiculos.selection())

    def _on_veiculo_select(self, event):
        selected_items = self.tree_veiculos.selection()
        if not selected_items: return

        item_id = self.tree_veiculos.item(selected_items[0])['values'][0]
        veiculo_obj = next((v for v in self.veiculos if v.id == item_id), None)
        if not veiculo_obj: return

        self._limpar_campos()

        self.propriedade_var.set(veiculo_obj.tipo_propriedade)
        if veiculo_obj.tipo_propriedade == 'TERCEIRO':
            transp_nome = next((t.nome for t in self.transportadoras if t.id == veiculo_obj.transportadora_id), "")
            self.combo_transportadora.set(transp_nome)

        self.entry_placa.insert(0, veiculo_obj.placa)
        self.entry_marca.insert(0, veiculo_obj.marca)
        self.entry_modelo.insert(0, veiculo_obj.modelo)
        self.entry_ano.insert(0, veiculo_obj.ano)
        self.entry_cor.insert(0, veiculo_obj.cor)
        self.combobox_combustivel.set(veiculo_obj.tipo_combustivel)
        self.entry_km_atual.insert(0, str(veiculo_obj.km_atual).replace('.', ','))

        self._toggle_transportadora_combo()
        self.id_veiculo_em_edicao = veiculo_obj.id
        self.btn_salvar.config(text="Atualizar Veículo")

    def _salvar_veiculo(self):
        placa = self.entry_placa.get().strip().upper()
        marca = self.entry_marca.get().strip().upper()
        modelo = self.entry_modelo.get().strip().upper()
        ano_str = self.entry_ano.get().strip()
        cor = self.entry_cor.get().strip().upper()
        tipo_combustivel = self.combobox_combustivel.get().strip().upper()
        km_atual_str = self.entry_km_atual.get().strip().replace(',', '.')
        tipo_propriedade = self.propriedade_var.get()
        transportadora_id = None

        if not placa or not marca or not modelo:
            messagebox.showwarning("Validação", "Placa, Marca e Modelo são obrigatórios.", parent=self.window)
            return

        try:
            ano = int(ano_str) if ano_str else 0
            km_atual = float(km_atual_str) if km_atual_str else 0.0
        except ValueError:
            messagebox.showwarning("Validação", "Ano e Km Atual devem ser números.", parent=self.window)
            return

        if tipo_propriedade == 'TERCEIRO':
            nome_transp = self.combo_transportadora.get()
            if not nome_transp:
                messagebox.showwarning("Validação", "Para veículo de terceiro, a transportadora é obrigatória.",
                                       parent=self.window)
                return
            transportadora_id = next((t.id for t in self.transportadoras if t.nome == nome_transp), None)

        try:
            veiculo_data = Veiculo(
                placa=placa, marca=marca, modelo=modelo, ano=ano,
                cor=cor, tipo_combustivel=tipo_combustivel, km_atual=km_atual,
                tipo_propriedade=tipo_propriedade,
                transportadora_id=transportadora_id
            )

            if self.id_veiculo_em_edicao:
                self.db_manager.update('veiculos', self.id_veiculo_em_edicao, veiculo_data.to_dict())
                messagebox.showinfo("Sucesso", f"Veículo de placa '{placa}' atualizado com sucesso!",
                                    parent=self.window)
            else:
                self.db_manager.insert('veiculos', veiculo_data.to_dict())
                messagebox.showinfo("Sucesso", f"Veículo de placa '{placa}' cadastrado com sucesso!",
                                    parent=self.window)

            self._limpar_campos()
            self._load_veiculos_from_db()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe um veículo com a placa '{placa}'.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro: {e}", parent=self.window)

    def _excluir_veiculo(self):
        if not self.id_veiculo_em_edicao:
            messagebox.showwarning("Nenhum Veículo Selecionado",
                                   "Por favor, selecione um veículo na tabela para excluir.", parent=self.window)
            return

        placa = self.entry_placa.get()
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o veículo de placa {placa}?",
                               parent=self.window):
            try:
                self.db_manager.delete('veiculos', self.id_veiculo_em_edicao)
                self._limpar_campos()
                self._load_veiculos_from_db()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro de Exclusão",
                                     "Não é possível excluir este veículo, pois ele está associado a abastecimentos ou viagens.",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao excluir: {e}", parent=self.window)

    def _importar_csv(self):
        """Pede um arquivo ao usuário e usa a classe importadora para processá-lo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV de Veículos",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not filepath:
            return

        importer = ImportadorDeVeiculos(self.db_manager, filepath)
        resultado = importer.executar()

        if "erro_leitura" in resultado:
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo: {resultado['erro_leitura']}",
                                 parent=self.window)
        else:
            messagebox.showinfo("Importação Concluída",
                                f"Importação finalizada!\n\n"
                                f"Registros importados: {resultado['sucesso']}\n"
                                f"Duplicados (placa): {resultado['duplicados']}\n"
                                f"Linhas com erro: {resultado['erros']}",
                                parent=self.window)

        self._load_veiculos_from_db()  # Atualiza a tabela