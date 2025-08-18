import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from datetime import datetime
import sqlite3
import csv
from tkcalendar import DateEntry
from importadores import ImportadorDeAbastecimentos

# Modelos necessários
from posto import Posto
from pessoa import Pessoa
from veiculo import Veiculo
from centro_custo import CentroCusto
from abastecimento import Abastecimento
from database_manager import DatabaseManager

class AbastecimentoWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager
        self.postos, self.pessoas, self.motoristas, self.veiculos, self.centros_custo, self.abastecimentos = [], [], [], [], [], []
        self.all_motorista_names, self.all_veiculo_placas, self.all_centro_custo_names, self.all_posto_names = [], [], [], []
        self.id_item_em_edicao, self.abastecimento_selecionado_id = None, None
        self.abastecimentos_filtrados_data = []
        self.tipos_combustivel, self.fator_co2_por_combustivel = [], {}
        self.total_litros_filtro, self.total_combustivel_filtro, self.total_outros_filtro, self.custo_geral_filtro = 0.0, 0.0, 0.0, 0.0

        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Abastecimentos")
        self.window.state('zoomed')

        self._load_all_data_from_db()
        self._build_ui()
        self._load_all_comboboxes_initial()
        self._filter_abastecimentos_by_date()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        self._build_form_frame()
        self._build_historico_frame()

    # ===================================================================
    # --- PARTE 2: Construção do Formulário de Registro ---
    # ===================================================================

    def _build_form_frame(self):
        """Constrói o formulário superior com o novo layout de 3 colunas."""
        frame_registrar = tk.LabelFrame(self.window, text="Registrar / Atualizar Abastecimento", padx=15, pady=15)
        frame_registrar.pack(pady=10, padx=20, fill="x", anchor="n")

        # Configura as colunas do grid para terem peso igual
        frame_registrar.columnconfigure(1, weight=1)
        frame_registrar.columnconfigure(3, weight=1)
        frame_registrar.columnconfigure(5, weight=1)

        # --- LINHA 0 ---
        tk.Label(frame_registrar, text="Data:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.date_entry = DateEntry(frame_registrar, width=15, date_pattern='dd/mm/yyyy', locale='pt_BR',
                                    state='readonly')
        self.date_entry.grid(row=0, column=1, sticky="ew", pady=5)

        tk.Label(frame_registrar, text="Motorista:").grid(row=0, column=2, sticky="w", pady=5, padx=15)
        self.ab_motorista_var = tk.StringVar()
        self.combobox_ab_motorista = ttk.Combobox(frame_registrar, textvariable=self.ab_motorista_var)
        self.combobox_ab_motorista.grid(row=0, column=3, sticky="ew", pady=5)
        self.combobox_ab_motorista.bind("<KeyRelease>", self._filter_motorista_combobox)

        tk.Label(frame_registrar, text="Placa do Veículo:").grid(row=0, column=4, sticky="w", pady=5, padx=15)
        self.ab_placa_veiculo_var = tk.StringVar()
        self.combobox_ab_placa_veiculo = ttk.Combobox(frame_registrar, textvariable=self.ab_placa_veiculo_var)
        self.combobox_ab_placa_veiculo.grid(row=0, column=5, sticky="ew", pady=5)
        self.combobox_ab_placa_veiculo.bind("<KeyRelease>", self._filter_veiculo_combobox)
        self.combobox_ab_placa_veiculo.bind("<<ComboboxSelected>>", self._on_placa_selected)

        # --- LINHA 1 ---
        tk.Label(frame_registrar, text="Posto de Combustível:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.ab_posto_var = tk.StringVar()
        self.combobox_ab_posto = ttk.Combobox(frame_registrar, textvariable=self.ab_posto_var)
        self.combobox_ab_posto.grid(row=1, column=1, sticky="ew", pady=5)
        self.combobox_ab_posto.bind("<KeyRelease>", self._filter_posto_combobox)

        tk.Label(frame_registrar, text="Centro de Custo:").grid(row=1, column=2, sticky="w", pady=5, padx=15)
        self.ab_centro_custo_var = tk.StringVar()
        self.combobox_ab_centro_custo = ttk.Combobox(frame_registrar, textvariable=self.ab_centro_custo_var)
        self.combobox_ab_centro_custo.grid(row=1, column=3, sticky="ew", pady=5)
        self.combobox_ab_centro_custo.bind("<KeyRelease>", self._filter_centro_custo_combobox)

        tk.Label(frame_registrar, text="Veículo (Modelo):").grid(row=1, column=4, sticky="w", pady=5, padx=15)
        self.label_ab_veiculo_modelo = tk.Label(frame_registrar, text="Aguardando seleção...", anchor="w")
        self.label_ab_veiculo_modelo.grid(row=1, column=5, sticky="ew", pady=5)

        # --- LINHA 2 ---
        tk.Label(frame_registrar, text="Nº Cupom:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.entry_ab_num_cupom = tk.Entry(frame_registrar)
        self.entry_ab_num_cupom.grid(row=2, column=1, sticky="w", pady=5)

        tk.Label(frame_registrar, text="Tipo de Combustível:").grid(row=2, column=2, sticky="w", pady=5, padx=15)
        self.ab_tipo_combustivel_var = tk.StringVar()
        self.combobox_tipo_combustivel = ttk.Combobox(frame_registrar, textvariable=self.ab_tipo_combustivel_var,
                                                      state="readonly", width=15)
        self.combobox_tipo_combustivel.grid(row=2, column=3, sticky="w", pady=5)

        # --- LINHA 3 - VALORES ---
        frame_valores = tk.Frame(frame_registrar)
        frame_valores.grid(row=3, column=0, columnspan=6, sticky="ew", pady=10, padx=5)
        tk.Label(frame_valores, text="Qtd (Lts):").pack(side=tk.LEFT)
        self.entry_ab_qtd = tk.Entry(frame_valores, width=10)
        self.entry_ab_qtd.pack(side=tk.LEFT, padx=(5, 15))
        self.entry_ab_qtd.bind("<KeyRelease>", self._calcular_valor_total)
        tk.Label(frame_valores, text="Valor Unit (R$):").pack(side=tk.LEFT)
        self.entry_ab_valor_unitario = tk.Entry(frame_valores, width=10)
        self.entry_ab_valor_unitario.pack(side=tk.LEFT, padx=(5, 15))
        self.entry_ab_valor_unitario.bind("<KeyRelease>", self._calcular_valor_total)
        tk.Label(frame_valores, text="Outros Gastos (R$):").pack(side=tk.LEFT)
        self.entry_ab_outros_gastos_valor = tk.Entry(frame_valores, width=10)
        self.entry_ab_outros_gastos_valor.pack(side=tk.LEFT, padx=5)

        # --- LINHA 4 - DESCRIÇÕES ---
        tk.Label(frame_registrar, text="Descrição Cupom:").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.entry_ab_descricao_cupom = tk.Entry(frame_registrar)
        self.entry_ab_descricao_cupom.grid(row=4, column=1, columnspan=5, sticky="ew", pady=5)

        tk.Label(frame_registrar, text="Descrição Outros Gastos:").grid(row=5, column=0, sticky="w", pady=5, padx=5)
        self.entry_ab_outros_gastos_descricao = tk.Entry(frame_registrar)
        self.entry_ab_outros_gastos_descricao.grid(row=5, column=1, columnspan=5, sticky="ew", pady=5)

        # --- LINHA FINAL - BOTÕES E TOTAL ---
        frame_final = tk.Frame(frame_registrar)
        frame_final.grid(row=6, column=0, columnspan=6, pady=10)
        tk.Label(frame_final, text="Valor Combustível (R$):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.label_ab_valor_total = tk.Label(frame_final, text="0,00", font=("Arial", 12, "bold"), anchor="w",
                                             fg="darkgreen")
        self.label_ab_valor_total.pack(side=tk.LEFT, padx=5)
        frame_botoes_form = tk.Frame(frame_final)
        frame_botoes_form.pack(side=tk.RIGHT, expand=True, fill='x')
        btn_limpar_ab_campos = tk.Button(frame_botoes_form, text="Limpar Campos",
                                         command=self._limpar_abastecimento_campos, height=2)
        btn_limpar_ab_campos.pack(side=tk.RIGHT)
        self.btn_registrar_ab = tk.Button(frame_botoes_form, text="Registrar Abastecimento",
                                          command=self._salvar_abastecimento, height=2, bg="#DDF0DD")
        self.btn_registrar_ab.pack(side=tk.RIGHT, padx=10)



    # ===================================================================
    # --- PARTE 3: Construção da Tabela de Histórico ---
    # ===================================================================

    def _build_historico_frame(self):
        """Constrói o frame inferior com a tabela de histórico, filtros, busca, e a linha de resumo."""
        frame_historico_ab = tk.LabelFrame(self.window, text="Histórico de Abastecimentos", padx=10, pady=10)
        frame_historico_ab.pack(pady=10, padx=20, fill="both", expand=True)

        # --- WIDGETS DE BAIXO (empacotados primeiro com side=tk.BOTTOM) ---

        # Frame para a Linha de Resumo/Totais
        frame_resumo = tk.LabelFrame(frame_historico_ab, text="Resumo do Filtro Atual", padx=10, pady=5)
        frame_resumo.pack(side=tk.BOTTOM, fill="x", pady=(10, 0))

        tk.Label(frame_resumo, text="Total Litros:", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.label_total_litros = tk.Label(frame_resumo, text="0.00 L", font=('Helvetica', 9))
        self.label_total_litros.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(frame_resumo, text="Total Combustível:", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.label_total_combustivel = tk.Label(frame_resumo, text="R$ 0,00", font=('Helvetica', 9))
        self.label_total_combustivel.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(frame_resumo, text="Total Outros:", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.label_total_outros = tk.Label(frame_resumo, text="R$ 0,00", font=('Helvetica', 9))
        self.label_total_outros.pack(side=tk.LEFT, padx=(0, 20))
        tk.Label(frame_resumo, text="CUSTO TOTAL:", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.label_custo_total_geral = tk.Label(frame_resumo, text="R$ 0,00", font=('Helvetica', 10, 'bold'),
                                                fg="darkblue")
        self.label_custo_total_geral.pack(side=tk.LEFT, padx=(0, 20))

        # Frame para os Botões de Ação da Tabela
        frame_botoes_acoes = tk.Frame(frame_historico_ab)
        frame_botoes_acoes.pack(side=tk.BOTTOM, pady=5)
        btn_editar = tk.Button(frame_botoes_acoes, text="Editar Selecionado", command=self._editar_abastecimento)
        btn_editar.pack(side=tk.LEFT, padx=5)
        btn_excluir = tk.Button(frame_botoes_acoes, text="Excluir Selecionado", command=self._excluir_abastecimento)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        btn_importar = tk.Button(frame_botoes_acoes, text="Importar de CSV", command=self._importar_abastecimentos_csv)
        btn_importar.pack(side=tk.LEFT, padx=15)
        btn_exportar = tk.Button(frame_botoes_acoes, text="Exportar CSV", command=self._exportar_abastecimentos_csv)
        btn_exportar.pack(side=tk.LEFT, padx=5)

        # --- WIDGETS DE CIMA ---
        frame_controles = tk.Frame(frame_historico_ab)
        frame_controles.pack(side=tk.TOP, fill="x", pady=5)

        tk.Label(frame_controles, text="Buscar por Posto/Motorista:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_busca_abastecimento = tk.Entry(frame_controles)
        self.entry_busca_abastecimento.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca_abastecimento.bind("<KeyRelease>", self._filtrar_abastecimentos_na_tabela)

        tk.Label(frame_controles, text="De:").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_data_inicio = DateEntry(frame_controles, width=12, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_inicio.pack(side=tk.LEFT)
        tk.Label(frame_controles, text="Até:").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_data_fim = DateEntry(frame_controles, width=12, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_fim.pack(side=tk.LEFT)
        btn_filtrar = tk.Button(frame_controles, text="Filtrar por Data", command=self._filter_abastecimentos_by_date)
        btn_filtrar.pack(side=tk.LEFT, padx=10)

        self.label_total_co2 = tk.Label(frame_controles, text="Total CO2 (Filtro): 0.00 kg",
                                        font=('Helvetica', 10, 'bold'))
        self.label_total_co2.pack(side=tk.RIGHT, padx=5)


        frame_tree = tk.Frame(frame_historico_ab)
        frame_tree.pack(side=tk.TOP, fill="both", expand=True, pady=(5, 0))

        columns_ab = ("id", "data_hora", "posto_nome", "motorista_nome", "veiculo_placa",
                      "centro_custo_nome", "tipo_combustivel", "qtd_litros", "valor_unitario",
                      "valor_total", "outros_gastos_valor", "custo_total_nota", "emissao_co2",
                      "outros_gastos_descricao")
        self.tree_abastecimentos = ttk.Treeview(frame_tree, columns=columns_ab, show="headings")
        self.tree_abastecimentos.tag_configure('oddrow', background='#F0F0F0')
        self.tree_abastecimentos.tag_configure('evenrow', background='white')
        cabecalhos = {
            "id": "ID", "data_hora": "Data", "posto_nome": "Posto", "motorista_nome": "Motorista",
            "veiculo_placa": "Placa", "centro_custo_nome": "Centro de Custo",
            "tipo_combustivel": "Combustível", "qtd_litros": "Litros", "valor_unitario": "R$/Litro",
            "valor_total": "Valor Comb. (R$)", "outros_gastos_valor": "Outros Gastos (R$)",
            "custo_total_nota": "Custo Total (R$)", "emissao_co2": "CO2 (kg)",
            "outros_gastos_descricao": "Descrição Gastos"
        }
        for col, texto in cabecalhos.items():
            self.tree_abastecimentos.heading(col, text=texto,
                                             command=lambda c=col: self._ordenar_coluna(self.tree_abastecimentos, c,
                                                                                        False))

        self.tree_abastecimentos.column("id", width=0, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("data_hora", width=90, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("posto_nome", width=180,anchor="center")
        self.tree_abastecimentos.column("motorista_nome", width=180,anchor="center")
        self.tree_abastecimentos.column("veiculo_placa", width=90, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("centro_custo_nome", width=150,anchor="center")
        self.tree_abastecimentos.column("tipo_combustivel", width=100, stretch=tk.NO,anchor="center")
        self.tree_abastecimentos.column("qtd_litros", width=80, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("valor_unitario", width=80, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("valor_total", width=110, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("outros_gastos_valor", width=110, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("custo_total_nota", width=110, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("emissao_co2", width=80, stretch=tk.NO, anchor="center")
        self.tree_abastecimentos.column("outros_gastos_descricao", width=250,anchor="center")



        scrollbar_v = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_abastecimentos.yview)
        scrollbar_h = ttk.Scrollbar(frame_tree, orient=tk.HORIZONTAL, command=self.tree_abastecimentos.xview)
        self.tree_abastecimentos.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)


        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_abastecimentos.pack(side=tk.LEFT, fill="both", expand=True)

        self.tree_abastecimentos.bind('<<TreeviewSelect>>', self._on_item_select)
    # ===================================================================
    # --- PARTE 4: Carregamento de Dados e Lógica dos ComboBoxes ---
    # ===================================================================

    def _load_all_data_from_db(self):
        self.postos = [Posto.from_dict(row) for row in self.db_manager.fetch_all('postos_combustivel')]
        all_pessoas_data = self.db_manager.fetch_all('pessoas')
        self.pessoas = [Pessoa.from_dict(row) for row in all_pessoas_data]
        self.motoristas = [p for p in self.pessoas if p.is_motorista]
        self.veiculos = [Veiculo.from_dict(row) for row in self.db_manager.fetch_all('veiculos')]
        self.centros_custo = [CentroCusto.from_dict(row) for row in self.db_manager.fetch_all('centros_custo')]
        self.abastecimentos = [Abastecimento.from_dict(row) for row in self.db_manager.fetch_all('abastecimentos')]

        parametros_co2_db = self.db_manager.fetch_all('parametros_co2')
        self.tipos_combustivel = sorted([p['tipo_combustivel'] for p in parametros_co2_db])
        self.fator_co2_por_combustivel = {p['tipo_combustivel'].upper(): p['fator_emissao'] for p in parametros_co2_db}

    def _load_all_comboboxes_initial(self):
        self.all_motorista_names = sorted([p.nome for p in self.motoristas])
        self.combobox_ab_motorista['values'] = self.all_motorista_names
        self.all_veiculo_placas = sorted([v.placa for v in self.veiculos])
        self.combobox_ab_placa_veiculo['values'] = self.all_veiculo_placas
        self.all_centro_custo_names = sorted([cc.nome for cc in self.centros_custo])
        self.combobox_ab_centro_custo['values'] = self.all_centro_custo_names
        self.all_posto_names = sorted([p.nome for p in self.postos])
        self.combobox_ab_posto['values'] = self.all_posto_names
        self.combobox_tipo_combustivel['values'] = self.tipos_combustivel
        if self.tipos_combustivel: self.combobox_tipo_combustivel.set(self.tipos_combustivel[0])

    def _filter_motorista_combobox(self, event):
        typed_text = self.ab_motorista_var.get().strip().lower()
        filtered = self.all_motorista_names if not typed_text else [name for name in self.all_motorista_names if
                                                                    typed_text in name.lower()]
        self.combobox_ab_motorista['values'] = filtered

    def _filter_veiculo_combobox(self, event):
        typed_text = self.ab_placa_veiculo_var.get().strip().lower()
        filtered = self.all_veiculo_placas if not typed_text else [placa for placa in self.all_veiculo_placas if
                                                                   typed_text in placa.lower()]
        self.combobox_ab_placa_veiculo['values'] = filtered

    def _filter_centro_custo_combobox(self, event):
        typed_text = self.ab_centro_custo_var.get().strip().lower()
        filtered = self.all_centro_custo_names if not typed_text else [name for name in self.all_centro_custo_names if
                                                                       typed_text in name.lower()]
        self.combobox_ab_centro_custo['values'] = filtered

    def _filter_posto_combobox(self, event):
        typed_text = self.ab_posto_var.get().strip().lower()
        filtered = self.all_posto_names if not typed_text else [name for name in self.all_posto_names if
                                                                typed_text in name.lower()]
        self.combobox_ab_posto['values'] = filtered

    def _on_placa_selected(self, event=None):
        placa = self.ab_placa_veiculo_var.get()
        modelo = next((f"{v.marca} {v.modelo} ({v.ano})" for v in self.veiculos if v.placa == placa), "Não encontrado")
        self.label_ab_veiculo_modelo.config(text=modelo)

    def _calcular_valor_total(self, event=None):
        try:
            qtd = float(self.entry_ab_qtd.get().replace(',', '.') or 0)
            valor_unit = float(self.entry_ab_valor_unitario.get().replace(',', '.') or 0)
            self.label_ab_valor_total.config(text=f"{qtd * valor_unit:.2f}".replace('.', ','))
        except ValueError:
            self.label_ab_valor_total.config(text="0,00")

    def _on_item_select(self, event):
        selected = self.tree_abastecimentos.selection()
        self.abastecimento_selecionado_id = self.tree_abastecimentos.item(selected[0], 'values')[
            0] if selected else None

    def _filter_abastecimentos_by_date(self):
        data_inicio = self.entry_data_inicio.get_date()
        data_fim = self.entry_data_fim.get_date()
        if data_inicio > data_fim:
            messagebox.showwarning("Erro de Filtro", "A data de início não pode ser maior que a data de fim.", parent=self.window)
            return
        self.abastecimentos_filtrados_data = [ab for ab in self.abastecimentos if data_inicio <= ab.data_hora.date() <= data_fim]
        self._filtrar_abastecimentos_na_tabela()

    def _filtrar_abastecimentos_na_tabela(self, event=None):
        texto = self.entry_busca_abastecimento.get().lower()
        if not hasattr(self, 'abastecimentos_filtrados_data'):
            self.abastecimentos_filtrados_data = self.abastecimentos

        lista_base = self.abastecimentos_filtrados_data
        if not texto:
            self._load_abastecimentos_to_ui(lista_base)
            return

        motoristas_lookup = {p.id: p.nome.lower() for p in self.motoristas}
        postos_lookup = {p.id: p.nome.lower() for p in self.postos}

        filtrados = [ab for ab in lista_base if
                     texto in postos_lookup.get(ab.posto_id, "") or texto in motoristas_lookup.get(ab.motorista_id, "")]
        self._load_abastecimentos_to_ui(filtrados)

    def _load_abastecimentos_to_ui(self, lista_a_exibir=None):
        """Carrega os abastecimentos na Treeview, aplicando as cores e calculando os totais."""
        self.tree_abastecimentos.delete(*self.tree_abastecimentos.get_children())

        postos_lookup = {p.id: p.nome for p in self.postos}
        motoristas_lookup = {p.id: p.nome for p in self.motoristas}
        veiculos_lookup = {v.id: v.placa for v in self.veiculos}
        centros_custo_lookup = {cc.id: cc.nome for cc in self.centros_custo}

        abastecimentos_para_exibir = lista_a_exibir if lista_a_exibir is not None else self.abastecimentos

        self.total_litros_filtro, self.total_combustivel_filtro, self.total_outros_filtro, total_co2 = 0.0, 0.0, 0.0, 0.0

        for i, ab in enumerate(abastecimentos_para_exibir):
            self.total_litros_filtro += ab.quantidade_litros
            self.total_combustivel_filtro += ab.valor_total
            self.total_outros_filtro += ab.outros_gastos_valor


            posto_nome = postos_lookup.get(ab.posto_id, "N/A")


            motorista_nome = motoristas_lookup.get(ab.motorista_id, "N/A")
            veiculo_placa = veiculos_lookup.get(ab.veiculo_id, "N/A")
            centro_custo_nome = centros_custo_lookup.get(ab.centro_custo_id, "N/A")

            fator = self.fator_co2_por_combustivel.get(ab.tipo_combustivel.upper(), 0.0)
            co2 = ab.quantidade_litros * fator
            total_co2 += co2
            custo_total = ab.valor_total + ab.outros_gastos_valor

            tag = 'evenrow' if i % 2 == 0 else 'oddrow'

            self.tree_abastecimentos.insert("", tk.END, values=(
                ab.id, ab.data_hora.strftime('%d/%m/%Y'), posto_nome, motorista_nome, veiculo_placa,
                centro_custo_nome, ab.tipo_combustivel, f"{ab.quantidade_litros:.2f}",
                f"{ab.valor_unitario:.2f}", f"{ab.valor_total:.2f}",
                f"{ab.outros_gastos_valor:.2f}", f"{custo_total:.2f}",
                f"{co2:.2f}", ab.outros_gastos_descricao
            ), tags=(tag,))

        self.custo_geral_filtro = self.total_combustivel_filtro + self.total_outros_filtro
        self.label_total_litros.config(text=f"{self.total_litros_filtro:,.2f} L".replace(',', '.'))
        self.label_total_combustivel.config(
            text=f"R$ {self.total_combustivel_filtro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.label_total_outros.config(
            text=f"R$ {self.total_outros_filtro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.label_custo_total_geral.config(
            text=f"R$ {self.custo_geral_filtro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.label_total_co2.config(text=f"Total CO2 (Filtro): {total_co2:.2f} kg")

    # ===================================================================
    # --- PARTE 6: Ações de CRUD (Limpar, Editar, Excluir) ---
    # ===================================================================

    def _limpar_abastecimento_campos(self):
        """Limpa todos os campos do formulário e reseta o estado de edição."""
        self.date_entry.set_date(datetime.now())
        self.ab_motorista_var.set("")
        self.ab_placa_veiculo_var.set("")
        self.label_ab_veiculo_modelo.config(text="Aguardando seleção de placa...")
        self.ab_centro_custo_var.set("")
        self.ab_posto_var.set("")
        self.entry_ab_num_cupom.delete(0, tk.END)
        self.entry_ab_descricao_cupom.delete(0, tk.END)
        self.entry_ab_qtd.delete(0, tk.END)
        self.entry_ab_valor_unitario.delete(0, tk.END)
        self.label_ab_valor_total.config(text="0,00")
        self.entry_ab_outros_gastos_valor.delete(0, tk.END)
        self.entry_ab_outros_gastos_descricao.delete(0, tk.END)

        self.id_item_em_edicao = None
        self.abastecimento_selecionado_id = None
        self.btn_registrar_ab.config(text="Registrar Abastecimento")
        if self.tree_abastecimentos.selection():
            self.tree_abastecimentos.selection_remove(self.tree_abastecimentos.selection())

    def _editar_abastecimento(self):
        """Preenche o formulário com os dados do abastecimento selecionado na tabela."""
        if not self.abastecimento_selecionado_id:
            messagebox.showwarning("Nenhum Item Selecionado", "Por favor, selecione um abastecimento para editar.",
                                   parent=self.window)
            return
        try:
            abastecimento_para_editar = next(
                ab for ab in self.abastecimentos if ab.id == self.abastecimento_selecionado_id)
        except (StopIteration, ValueError):
            messagebox.showerror("Erro", "Não foi possível encontrar os dados do abastecimento.", parent=self.window)
            return

        self._limpar_abastecimento_campos()
        self.date_entry.set_date(abastecimento_para_editar.data_hora)

        motorista = next((p for p in self.motoristas if p.id == abastecimento_para_editar.motorista_id), None)
        if motorista: self.ab_motorista_var.set(motorista.nome)

        veiculo = next((v for v in self.veiculos if v.id == abastecimento_para_editar.veiculo_id), None)
        if veiculo:
            self.ab_placa_veiculo_var.set(veiculo.placa)
            self._on_placa_selected()

        cc = next((c for c in self.centros_custo if c.id == abastecimento_para_editar.centro_custo_id), None)
        if cc: self.ab_centro_custo_var.set(cc.nome)

        posto = next((p for p in self.postos if p.id == abastecimento_para_editar.posto_id), None)
        if posto: self.ab_posto_var.set(posto.nome)

        self.entry_ab_num_cupom.insert(0, abastecimento_para_editar.numero_cupom)
        self.entry_ab_descricao_cupom.insert(0, abastecimento_para_editar.descricao_cupom)
        self.ab_tipo_combustivel_var.set(abastecimento_para_editar.tipo_combustivel)
        self.entry_ab_qtd.insert(0, f"{abastecimento_para_editar.quantidade_litros:.2f}".replace('.', ','))
        self.entry_ab_valor_unitario.insert(0, f"{abastecimento_para_editar.valor_unitario:.2f}".replace('.', ','))
        self.entry_ab_outros_gastos_valor.insert(0, f"{abastecimento_para_editar.outros_gastos_valor:.2f}".replace('.',
                                                                                                                   ','))
        self.entry_ab_outros_gastos_descricao.insert(0, abastecimento_para_editar.outros_gastos_descricao)
        self._calcular_valor_total()

        self.id_item_em_edicao = abastecimento_para_editar.id
        self.btn_registrar_ab.config(text="Atualizar Abastecimento")
        self.entry_ab_num_cupom.focus_set()

    def _excluir_abastecimento(self):
        """Exclui o abastecimento selecionado."""
        if not self.abastecimento_selecionado_id:
            messagebox.showwarning("Aviso", "Selecione um abastecimento para excluir.", parent=self.window)
            return
        if messagebox.askyesno("Confirmar",
                               f"Tem certeza que deseja excluir o abastecimento ID {self.abastecimento_selecionado_id}?",
                               parent=self.window):
            try:
                self.db_manager.delete('abastecimentos', self.abastecimento_selecionado_id)
                messagebox.showinfo("Sucesso", "Abastecimento excluído com sucesso!", parent=self.window)
                self._limpar_abastecimento_campos()
                self._load_all_data_from_db()
                self._filter_abastecimentos_by_date()
            except Exception as e:
                messagebox.showerror("Erro de Exclusão", f"Ocorreu um erro: {e}", parent=self.window)

    # ===================================================================
    # --- PARTE 7: Ação Principal de Salvar ---
    # ===================================================================

    def _salvar_abastecimento(self):
        """Salva um novo abastecimento ou atualiza um existente."""
        # Coleta de dados
        data_str = self.date_entry.get()
        motorista_nome = self.ab_motorista_var.get().strip()
        veiculo_placa = self.ab_placa_veiculo_var.get().strip()
        cc_nome = self.ab_centro_custo_var.get().strip()
        posto_nome = self.ab_posto_var.get().strip()
        num_cupom = self.entry_ab_num_cupom.get().strip()
        desc_cupom = self.entry_ab_descricao_cupom.get().strip()
        tipo_comb = self.ab_tipo_combustivel_var.get().strip()
        qtd_str = self.entry_ab_qtd.get().strip().replace(',', '.')
        valor_unit_str = self.entry_ab_valor_unitario.get().strip().replace(',', '.')
        outros_val_str = self.entry_ab_outros_gastos_valor.get().strip().replace(',', '.') or "0.0"
        outros_desc = self.entry_ab_outros_gastos_descricao.get().strip()

        # Validação
        if not all([data_str, motorista_nome, veiculo_placa, cc_nome, posto_nome, num_cupom, tipo_comb]):
            messagebox.showwarning("Validação",
                                   "Data, Motorista, Veículo, Posto, CC, Nº Cupom e Combustível são obrigatórios.",
                                   parent=self.window)
            return
        try:
            qtd = float(qtd_str) if qtd_str else 0.0
            val_unit = float(valor_unit_str) if valor_unit_str else 0.0
            outros_val = float(outros_val_str)
            val_total = qtd * val_unit
        except (ValueError, TypeError):
            messagebox.showwarning("Validação", "Valores de quantidade/preços são inválidos.", parent=self.window)
            return

        try:
            motorista_id = next((p.id for p in self.motoristas if p.nome == motorista_nome), None)
            veiculo_id = next((v.id for v in self.veiculos if v.placa == veiculo_placa), None)
            cc_id = next((cc.id for cc in self.centros_custo if cc.nome == cc_nome), None)
            posto_id = next((p.id for p in self.postos if p.nome == posto_nome), None)

            if not all([motorista_id, veiculo_id, cc_id, posto_id]):
                messagebox.showerror("Erro de Vínculo",
                                     "Motorista, Veículo, CC ou Posto não encontrado. Verifique as seleções e os cadastros.",
                                     parent=self.window)
                return

            abastecimento_obj = Abastecimento(
                data_hora=data_str, motorista_id=motorista_id, veiculo_id=veiculo_id,
                centro_custo_id=cc_id, posto_id=posto_id, numero_cupom=num_cupom.upper(),
                descricao_cupom=desc_cupom.upper(), tipo_combustivel=tipo_comb.upper(),
                quantidade_litros=qtd, valor_unitario=val_unit, valor_total=val_total,
                outros_gastos_descricao=outros_desc.upper(), outros_gastos_valor=outros_val
            )

            if self.id_item_em_edicao:
                self.db_manager.update('abastecimentos', self.id_item_em_edicao, abastecimento_obj.to_dict())
                messagebox.showinfo("Sucesso", "Abastecimento atualizado com sucesso!", parent=self.window)
            else:
                self.db_manager.insert('abastecimentos', abastecimento_obj.to_dict())
                messagebox.showinfo("Sucesso", "Abastecimento registrado com sucesso!", parent=self.window)

            self._limpar_abastecimento_campos()
            self._load_all_data_from_db()
            self._load_all_comboboxes_initial()
            self._filter_abastecimentos_by_date()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Erro", f"Já existe um abastecimento com o número de cupom '{num_cupom}'.",
                                   parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro inesperado: {e}", parent=self.window)

    # ===================================================================
    # --- PARTE 8: Lógica da Tabela, Importação e Ordenação ---
    # ===================================================================

    def _filter_abastecimentos_by_date(self):
        """Filtra os abastecimentos com base no período de data E depois aplica o filtro de texto."""
        data_inicio = self.entry_data_inicio.get_date()
        data_fim = self.entry_data_fim.get_date()
        if data_inicio > data_fim:
            messagebox.showwarning("Erro de Filtro", "A data de início não pode ser maior que a data de fim.",
                                   parent=self.window)
            return

        # Primeiro, cria uma lista com base apenas nas datas
        self.abastecimentos_filtrados_data = [ab for ab in self.abastecimentos if
                                              data_inicio <= ab.data_hora.date() <= data_fim]

        # Em seguida, chama o filtro de texto para que ele filtre sobre o resultado do filtro de data
        self._filtrar_abastecimentos_na_tabela()

    def _filtrar_abastecimentos_na_tabela(self, event=None):
        """Filtra a lista de abastecimentos com base no texto de busca."""
        texto = self.entry_busca_abastecimento.get().lower()

        # Garante que a lista filtrada por data exista antes de usá-la
        if not hasattr(self, 'abastecimentos_filtrados_data'):
            self.abastecimentos_filtrados_data = self.abastecimentos

        # Se não há texto na busca, exibe o resultado do filtro de data
        if not texto:
            self._load_abastecimentos_to_ui(self.abastecimentos_filtrados_data)
            return

        # Se há texto, filtra AINDA MAIS a lista que já foi filtrada por data
        motoristas_lookup = {p.id: p.nome.lower() for p in self.motoristas}
        postos_lookup = {p.id: p.nome.lower() for p in self.postos}

        filtrados = [
            ab for ab in self.abastecimentos_filtrados_data
            if texto in postos_lookup.get(ab.posto_id, "") or \
               texto in motoristas_lookup.get(ab.motorista_id, "")
        ]
        self._load_abastecimentos_to_ui(filtrados)


    def _importar_abastecimentos_csv(self):
        """Pede um arquivo ao usuário e usa a classe importadora para processá-lo."""
        filepath = filedialog.askopenfilename(
            title="Selecionar Arquivo CSV de Abastecimentos",
            filetypes=[("Arquivos CSV", "*.csv")]
        )
        if not filepath:
            return

        # 1. Cria uma instância do nosso novo importador especialista
        importer = ImportadorDeAbastecimentos(self.db_manager, filepath)

        # 2. Executa a importação
        resultado = importer.executar()

        # 3. Exibe o resumo do resultado
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

        # 4. Atualiza a tela com os novos dados
        self._load_all_data_from_db()
        self._filter_abastecimentos_by_date()

    def _ordenar_coluna(self, treeview, coluna, reversa):
        """Função genérica para ordenar qualquer Treeview e reaplicar as cores."""
        # Passo 1: Pega os dados da coluna para ordenar a lista
        lista_de_dados = [(treeview.set(item_id, coluna), item_id) for item_id in treeview.get_children('')]

        colunas_numericas = ["id", "qtd_litros", "valor_unitario", "valor_total", "emissao_co2", "outros_gastos_valor",
                             "custo_total_nota"]

        try:
            if coluna in colunas_numericas:
                lista_de_dados.sort(
                    key=lambda t: float(str(t[0]).replace('R$', '').replace('%', '').replace(',', '.').strip()),
                    reverse=reversa)
            else:
                lista_de_dados.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)
        except ValueError:
            lista_de_dados.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)

        # Passo 2: Move as linhas para a nova ordem na tabela
        for indice, (valor, item_id) in enumerate(lista_de_dados):
            treeview.move(item_id, '', indice)

        # --- CORREÇÃO APLICADA AQUI ---
        # A linha 'if' foi removida. A lógica de repintar agora roda sempre.
        for i, item_id in enumerate(treeview.get_children('')):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            treeview.item(item_id, tags=(tag,))

        # Passo 4: Inverte o comando do cabeçalho para o próximo clique
        treeview.heading(coluna, command=lambda: self._ordenar_coluna(treeview, coluna, not reversa))

    def _exportar_viagens_csv(self):
        """Exporta os dados visíveis na tabela e adiciona um resumo por transportadora no final."""
        if not self.tree_viagens.get_children():
            messagebox.showwarning("Exportar", "Não há dados na tabela para exportar.", parent=self.window)
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
            title="Salvar Relatório de Viagens"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')

                # Parte 1: Escreve os cabeçalhos e os dados detalhados (sem a coluna de ID)
                colunas_ids = [col for col in self.tree_viagens['columns'] if col != 'id']
                colunas_nomes = [self.tree_viagens.heading(col, "text") for col in colunas_ids]
                writer.writerow(colunas_nomes)

                for row_id in self.tree_viagens.get_children():
                    valores_linha = self.tree_viagens.item(row_id)['values'][1:]  # Pula o ID
                    writer.writerow(valores_linha)

                # --- NOVO: Parte 2: Calcula e escreve o resumo por Transportadora ---
                writer.writerow([])  # Linha em branco para separar
                writer.writerow([])
                writer.writerow([])
                writer.writerow(["RESUMO POR TRANSPORTADORA"])
                writer.writerow(["Transportadora", "Nº de Viagens", "Valor Total a Pagar (R$)"])

                # Pega a lista de dados que está sendo exibida na tela
                lista_filtrada = self.viagens_filtradas

                # Calcula os totais e a contagem de viagens por transportadora
                resumo_por_transportadora = {}
                for viagem in lista_filtrada:
                    nome = viagem['transportadora_nome']
                    valor_base = viagem.get('valor_base_frete', 0.0)
                    bonus = viagem.get('bonus_percentual', 0.0)
                    valor_final = valor_base * (1 + (bonus / 100))

                    if nome not in resumo_por_transportadora:
                        resumo_por_transportadora[nome] = {'viagens': 0, 'total': 0.0}

                    resumo_por_transportadora[nome]['viagens'] += 1
                    resumo_por_transportadora[nome]['total'] += valor_final

                # Escreve uma linha para cada transportadora no CSV, ordenado pelo nome
                for nome, totais in sorted(resumo_por_transportadora.items()):
                    writer.writerow([
                        nome,
                        totais['viagens'],
                        f"{totais['total']:.2f}".replace('.', ',')
                    ])

            messagebox.showinfo("Sucesso", f"Relatório salvo com sucesso em:\n{filepath}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao exportar o arquivo: {e}", parent=self.window)