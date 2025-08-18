import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime
import csv
from firebase_admin import firestore

from viagem import Viagem
from database_manager import DatabaseManager
from importadores import ImportadorDeViagens


class GerenciarViagensWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager

        # Listas de dados
        self.transportadoras = []
        self.localidades = []
        self.all_localidades_nomes = []
        self.veiculos_terceiros = []
        self.precos_lookup = {}
        self.viagens_filtradas = []
        self.id_viagem_em_edicao = None

        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar Viagens de Frete")
        self.window.state('zoomed')

        self._load_data()
        self._build_ui()
        self._aplicar_filtros()  # Carrega a lista inicial

        self.window.transient(parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _load_data(self):
        """Carrega todos os dados necessários para os ComboBoxes e para a lógica de preços."""
        self.transportadoras = self.db_manager.fetch_all('transportadoras')
        self.localidades = self.db_manager.fetch_all('localidades')
        self.all_localidades_nomes = sorted([l['nome'] for l in self.localidades])

        todos_veiculos = self.db_manager.fetch_all('veiculos')
        self.veiculos_terceiros = [v for v in todos_veiculos if v['tipo_propriedade'] == 'TERCEIRO']

        precos_db = self.db_manager.fetch_all('tabela_precos_frete')
        self.precos_lookup.clear()
        for preco in precos_db:
            loc_id = preco['localidade_id']
            if loc_id not in self.precos_lookup:
                self.precos_lookup[loc_id] = {}
            self.precos_lookup[loc_id]['TRUCK'] = preco['valor_truck']
            self.precos_lookup[loc_id]['TOCO'] = preco['valor_toco']
            self.precos_lookup[loc_id]['3/4'] = preco['valor_3_4']

    def _build_ui(self):
        # Frame do Formulário (parte de cima)
        self._build_form_frame()

        # Frame do histórico (parte de baixo)
        self._build_historico_frame()

    def _build_form_frame(self):
        frame_registrar = tk.LabelFrame(self.window, text="Registrar / Atualizar Viagem", padx=15, pady=15)
        frame_registrar.pack(pady=10, padx=20, fill="x", anchor="n")

        # --- Frame da Esquerda (Entradas) ---
        frame_esquerda = tk.Frame(frame_registrar)
        frame_esquerda.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))

        # Grid para alinhar os labels e campos
        frame_esquerda.columnconfigure(1, weight=1)

        tk.Label(frame_esquerda, text="Data:").grid(row=0, column=0, sticky="w", pady=5)
        self.date_entry = DateEntry(frame_esquerda, width=15, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.date_entry.grid(row=0, column=1, sticky="ew", pady=5)

        tk.Label(frame_esquerda, text="Transportadora:").grid(row=1, column=0, sticky="w", pady=5)
        transp_nomes = [t['nome'] for t in self.transportadoras]
        self.combo_transportadora = ttk.Combobox(frame_esquerda, values=transp_nomes, state="readonly")
        self.combo_transportadora.grid(row=1, column=1, sticky="ew", pady=5)

        tk.Label(frame_esquerda, text="Veículo de Terceiro:").grid(row=2, column=0, sticky="w", pady=5)
        veiculos_nomes = [f"{v['placa']} ({v['modelo']})" for v in self.veiculos_terceiros]
        self.combo_veiculo = ttk.Combobox(frame_esquerda, values=veiculos_nomes, state="readonly")
        self.combo_veiculo.grid(row=2, column=1, sticky="ew", pady=5)

        tk.Label(frame_esquerda, text="Localidade (Destino):").grid(row=3, column=0, sticky="w", pady=5)
        self.ab_localidade_var = tk.StringVar()
        self.combo_localidade = ttk.Combobox(frame_esquerda, textvariable=self.ab_localidade_var)
        self.combo_localidade['values'] = self.all_localidades_nomes
        self.combo_localidade.grid(row=3, column=1, sticky="ew", pady=5)
        self.combo_localidade.bind("<<ComboboxSelected>>", self._atualizar_preco_exibido)
        self.combo_localidade.bind("<KeyRelease>", self._filtrar_localidades_combobox)

        tk.Label(frame_esquerda, text="Tipo de Caminhão:").grid(row=4, column=0, sticky="w", pady=5)
        tipos_caminhao = ['TRUCK', 'TOCO', '3/4']
        self.combo_tipo_caminhao = ttk.Combobox(frame_esquerda, values=tipos_caminhao, state="readonly")
        self.combo_tipo_caminhao.grid(row=4, column=1, sticky="ew", pady=5)
        self.combo_tipo_caminhao.bind("<<ComboboxSelected>>", self._atualizar_preco_exibido)

        tk.Label(frame_esquerda, text="Motorista:").grid(row=5, column=0, sticky="w", pady=5)
        self.entry_motorista = tk.Entry(frame_esquerda)
        self.entry_motorista.grid(row=5, column=1, sticky="ew", pady=5)

        # --- Frame da Direita (Resultados e Ações) ---
        frame_direita = tk.Frame(frame_registrar)
        frame_direita.pack(side=tk.LEFT, fill="x", expand=True, padx=(10, 0))

        frame_direita.columnconfigure(1, weight=1)

        tk.Label(frame_direita, text="Veículo (Modelo):").grid(row=0, column=0, sticky="w", pady=5)
        self.label_ab_veiculo_modelo = tk.Label(frame_direita, text="Aguardando seleção...", anchor="w")
        self.label_ab_veiculo_modelo.grid(row=0, column=1, sticky="ew", pady=5)

        tk.Label(frame_direita, text="Bônus (%):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_bonus = tk.Entry(frame_direita)
        self.entry_bonus.grid(row=1, column=1, sticky="ew", pady=5)
        self.entry_bonus.insert(0, "0")
        self.entry_bonus.bind("<KeyRelease>", self._calcular_e_exibir_valor_final)

        tk.Label(frame_direita, text="Valor Base (R$):").grid(row=2, column=0, sticky="w", pady=5)
        self.label_preco_base = tk.Label(frame_direita, text="0.00", font=('Helvetica', 10, 'bold'))
        self.label_preco_base.grid(row=2, column=1, sticky="ew", pady=5)

        tk.Label(frame_direita, text="VALOR FINAL (R$):").grid(row=3, column=0, sticky="w", pady=5)
        self.label_preco_final = tk.Label(frame_direita, text="0.00", font=('Helvetica', 14, 'bold'), fg="blue")
        self.label_preco_final.grid(row=3, column=1, sticky="ew", pady=5)

        # Frame para os botões, dentro do frame da direita
        frame_botoes_form = tk.Frame(frame_direita)
        frame_botoes_form.grid(row=4, column=0, columnspan=2, pady=20, sticky="ew")

        self.btn_salvar = tk.Button(frame_botoes_form, text="Salvar Viagem", command=self._salvar_viagem, height=2,
                                    bg="#DDF0DD")
        self.btn_salvar.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 5))

        btn_limpar = tk.Button(frame_botoes_form, text="Limpar Campos", command=self._limpar_campos, height=2)
        btn_limpar.pack(side=tk.LEFT, expand=True, fill='x', padx=(5, 0))

    def _build_historico_frame(self):
        """Constrói o frame inferior com a tabela de histórico e altura fixa."""
        frame_historico = tk.LabelFrame(self.window, text="Histórico de Viagens", padx=10, pady=10)
        frame_historico.pack(pady=10, padx=20, fill="x", expand=True)

        # --- WIDGETS DE BAIXO (ancorados primeiro com side=tk.BOTTOM) ---
        frame_botoes_acoes = tk.Frame(frame_historico)
        frame_botoes_acoes.pack(side=tk.BOTTOM, pady=5)
        btn_excluir = tk.Button(frame_botoes_acoes, text="Excluir Viagem", command=self._excluir_viagem)
        btn_excluir.pack(side=tk.LEFT, padx=5)
        btn_importar = tk.Button(frame_botoes_acoes, text="Importar de CSV", command=self._importar_viagens_csv)
        btn_importar.pack(side=tk.LEFT, padx=15)
        btn_exportar = tk.Button(frame_botoes_acoes, text="Exportar CSV", command=self._exportar_viagens_csv)
        btn_exportar.pack(side=tk.LEFT, padx=5)

        frame_resumo = tk.LabelFrame(frame_historico, text="Resumo do Filtro", padx=10, pady=5)
        frame_resumo.pack(side=tk.BOTTOM, fill="x", pady=(10, 0))
        tk.Label(frame_resumo, text="CUSTO TOTAL (Período):", font=('Helvetica', 10, 'bold')).pack(side=tk.LEFT,
                                                                                                   padx=(0, 5))
        self.label_custo_total_geral = tk.Label(frame_resumo, text="R$ 0,00", font=('Helvetica', 12, 'bold'),
                                                fg="darkblue")
        self.label_custo_total_geral.pack(side=tk.LEFT, padx=(0, 20))

        # --- WIDGETS DE CIMA ---
        frame_controles = tk.Frame(frame_historico)
        frame_controles.pack(side=tk.TOP, fill="x", pady=5)

        tk.Label(frame_controles, text="Buscar por Transportadora:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_busca = tk.Entry(frame_controles)
        self.entry_busca.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.entry_busca.bind("<KeyRelease>", self._aplicar_filtros)

        tk.Label(frame_controles, text="De:").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_data_inicio = DateEntry(frame_controles, width=12, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_inicio.pack(side=tk.LEFT)
        tk.Label(frame_controles, text="Até:").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_data_fim = DateEntry(frame_controles, width=12, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_fim.pack(side=tk.LEFT)
        btn_filtrar = tk.Button(frame_controles, text="Filtrar por Data", command=self._aplicar_filtros)
        btn_filtrar.pack(side=tk.LEFT, padx=10)

        # --- WIDGET DO MEIO (ocupa o resto do espaço) ---
        frame_tree = tk.Frame(frame_historico)
        frame_tree.pack(side=tk.TOP, fill="both", expand=True)

        cols = ("id", "data", "transportadora", "localidade", "tipo_caminhao", "veiculo", "motorista", "valor_base",
                "bonus", "valor_final")

        # --- A CORREÇÃO ESTÁ AQUI: height=10 ---
        self.tree_viagens = ttk.Treeview(frame_tree, columns=cols, show="headings", height=10)

        self.tree_viagens.tag_configure('oddrow', background='#F0F0F0')
        self.tree_viagens.tag_configure('evenrow', background='white')

        cabecalhos = {
            "id": "ID", "data": "Data", "transportadora": "Transportadora", "localidade": "Destino",
            "tipo_caminhao": "Tipo Caminhão", "veiculo": "Veículo", "motorista": "Motorista",
            "valor_base": "Valor Base (R$)", "bonus": "Bônus (%)", "valor_final": "Valor Final (R$)"
        }
        for col, texto in cabecalhos.items():
            self.tree_viagens.heading(col, text=texto,
                                      command=lambda c=col: self._ordenar_coluna(self.tree_viagens, c, False))

        self.tree_viagens.column("id", width=0, stretch=tk.NO)
        self.tree_viagens.column("data", width=90, anchor="center")
        self.tree_viagens.column("transportadora", width=200)
        self.tree_viagens.column("localidade", width=200)
        self.tree_viagens.column("tipo_caminhao", width=110, anchor="center")
        self.tree_viagens.column("veiculo", width=120, anchor="center")
        self.tree_viagens.column("motorista", width=150)
        self.tree_viagens.column("valor_base", width=110, anchor="e")
        self.tree_viagens.column("bonus", width=80, anchor="center")
        self.tree_viagens.column("valor_final", width=110, anchor="e")

        scrollbar = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self.tree_viagens.yview)
        self.tree_viagens.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_viagens.pack(side=tk.LEFT, fill="both", expand=True)
        self.tree_viagens.bind("<<TreeviewSelect>>", self._on_viagem_select)

    def _atualizar_preco_exibido(self, event=None):
        """Busca o preço na tabela e atualiza o label de valor BASE."""
        loc_nome = self.combo_localidade.get()
        tipo_caminhao = self.combo_tipo_caminhao.get()
        if not loc_nome or not tipo_caminhao:
            self.label_preco_base.config(text="0.00")
        else:
            try:
                loc_id = next(l['id'] for l in self.localidades if l['nome'] == loc_nome)
                preco = self.precos_lookup.get(loc_id, {}).get(tipo_caminhao, 0.0)
                self.label_preco_base.config(text=f"{preco:.2f}")
            except StopIteration:
                self.label_preco_base.config(text="Erro")
        self._calcular_e_exibir_valor_final()

    def _calcular_e_exibir_valor_final(self, event=None):
        """Pega o valor base e o bônus, calcula e exibe o valor final."""
        try:
            valor_base = float(self.label_preco_base.cget("text"))
            bonus_str = self.entry_bonus.get().replace(',', '.') or "0"
            bonus = float(bonus_str)
            valor_final = valor_base * (1 + (bonus / 100))
            self.label_preco_final.config(text=f"{valor_final:.2f}")
        except (ValueError, tk.TclError):
            self.label_preco_final.config(text="Inválido")

    def _filtrar_localidades_combobox(self, event=None):
        """Filtra o combobox de localidades em tempo real."""
        texto_digitado = self.ab_localidade_var.get().strip().lower()
        if not texto_digitado:
            self.combo_localidade['values'] = self.all_localidades_nomes
        else:
            filtrados = [nome for nome in self.all_localidades_nomes if texto_digitado in nome.lower()]
            self.combo_localidade['values'] = filtrados
        self._atualizar_preco_exibido()

    def _on_viagem_select(self, event):
        """Preenche o formulário ao selecionar uma viagem na tabela."""
        selected = self.tree_viagens.selection()
        if not selected: return

        item_id = self.tree_viagens.item(selected[0], "values")[0]


        viagem_dict = self.db_manager.fetch_by_id('viagens', item_id)
        # ---------------------------

        if not viagem_dict:
            messagebox.showerror("Erro", f"Não foi possível encontrar os dados para a viagem ID {item_id}",
                                 parent=self.window)
            return

        self._limpar_campos()

        data_obj = datetime.strptime(viagem_dict['data_viagem'], '%Y-%m-%d').date()
        self.date_entry.set_date(data_obj)

        transp_nome = next((t['nome'] for t in self.transportadoras if t['id'] == viagem_dict['transportadora_id']), "")
        self.combo_transportadora.set(transp_nome)

        loc_nome = next((l['nome'] for l in self.localidades if l['id'] == viagem_dict['localidade_id']), "")
        self.ab_localidade_var.set(loc_nome)

        if viagem_dict.get('veiculo_id'):
            veiculo_obj = next((v for v in self.veiculos_terceiros if v['id'] == viagem_dict['veiculo_id']), None)
            if veiculo_obj:
                self.combo_veiculo.set(f"{veiculo_obj['placa']} ({veiculo_obj['modelo']})")

        self.combo_tipo_caminhao.set(viagem_dict['tipo_caminhao'])
        self.entry_motorista.insert(0, viagem_dict.get('motorista_nome') or "")
        self.entry_bonus.delete(0, tk.END)
        self.entry_bonus.insert(0, str(viagem_dict.get('bonus_percentual', 0)).replace('.', ','))

        self._atualizar_preco_exibido()
        self.id_viagem_em_edicao = viagem_dict['id']
        self.btn_salvar.config(text="Atualizar Viagem")

    def _aplicar_filtros(self, event=None):
        """Aplica o filtro de data e o filtro de texto combinados."""
        data_inicio = self.entry_data_inicio.get_date().strftime('%Y-%m-%d')
        data_fim = self.entry_data_fim.get_date().strftime('%Y-%m-%d')

        viagens_db = self.db_manager.fetch_viagens_com_detalhes(data_inicio, data_fim)

        texto_busca = self.entry_busca.get().lower()
        if not texto_busca:
            viagens_finais = viagens_db
        else:
            viagens_finais = [
                v for v in viagens_db
                if texto_busca in v['transportadora_nome'].lower()
            ]

        self._carregar_viagens_na_tabela(viagens_finais)

    def _carregar_viagens_na_tabela(self, viagens):
        self.tree_viagens.delete(*self.tree_viagens.get_children())

        custo_geral_do_filtro = 0.0  # Inicializa o contador

        for i, viagem in enumerate(viagens):
            valor_base = viagem.get('valor_base_frete', 0.0)
            bonus = viagem.get('bonus_percentual', 0.0)
            valor_final = valor_base * (1 + (bonus / 100))

            custo_geral_do_filtro += valor_final  # Acumula o valor final

            data_formatada = datetime.strptime(viagem['data_viagem'], '%Y-%m-%d').strftime('%d/%m/%Y')
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'

            self.tree_viagens.insert("", tk.END, tags=(tag,), values=(
                viagem['id'], data_formatada, viagem['transportadora_nome'],
                viagem['localidade_nome'], viagem['tipo_caminhao'], viagem['veiculo_info'],
                viagem['motorista_nome'], f"{valor_base:.2f}",
                f"{bonus:.2f}", f"{valor_final:.2f}"
            ))

        # Atualiza o label de resumo com o total calculado
        self.label_custo_total_geral.config(
            text=f"R$ {custo_geral_do_filtro:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    def _limpar_campos(self):
        """Limpa todos os campos do formulário e reseta o estado de edição."""
        self.date_entry.set_date(datetime.now())
        self.combo_transportadora.set('')
        self.combo_veiculo.set('')
        self.ab_localidade_var.set('')
        self.combo_localidade['values'] = self.all_localidades_nomes
        self.combo_tipo_caminhao.set('')
        self.entry_motorista.delete(0, tk.END)
        self.entry_bonus.delete(0, tk.END)
        self.entry_bonus.insert(0, "0")
        self.label_preco_base.config(text="0.00")
        self.label_preco_final.config(text="0.00")

        self.id_viagem_em_edicao = None
        self.btn_salvar.config(text="Salvar Viagem")
        if self.tree_viagens.selection():
            self.tree_viagens.selection_remove(self.tree_viagens.selection())

    def _excluir_viagem(self):
        """Exclui a viagem selecionada."""
        if not self.id_viagem_em_edicao:
            messagebox.showwarning("Aviso", "Selecione uma viagem para excluir.", parent=self.window);
            return
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir a viagem selecionada?", parent=self.window):
            try:
                self.db_manager.delete('viagens', self.id_viagem_em_edicao)
                messagebox.showinfo("Sucesso", "Viagem excluída com sucesso.")
                self._limpar_campos()
                self._aplicar_filtros()
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao excluir: {e}", parent=self.window)

    def _salvar_viagem(self):
        """Salva uma nova viagem ou atualiza uma existente."""
        data_str = self.date_entry.get_date().strftime('%Y-%m-%d')
        transp_nome = self.combo_transportadora.get()
        veiculo_sel = self.combo_veiculo.get()
        loc_nome = self.ab_localidade_var.get()
        tipo_caminhao = self.combo_tipo_caminhao.get()
        motorista = self.entry_motorista.get().strip().upper()
        valor_base_str = self.label_preco_base.cget("text")
        bonus_str = self.entry_bonus.get().replace(',', '.') or "0"

        if not all([data_str, transp_nome, loc_nome, tipo_caminhao]):
            messagebox.showwarning("Validação", "Data, Transportadora, Localidade e Tipo de Caminhão são obrigatórios.",
                                   parent=self.window)
            return

        try:
            transp_id = next(t['id'] for t in self.transportadoras if t['nome'] == transp_nome)
            loc_id = next(l['id'] for l in self.localidades if l['nome'] == loc_nome)
            valor_base = float(valor_base_str)
            bonus = float(bonus_str)
            veiculo_id = None
            if veiculo_sel:
                placa_veiculo = veiculo_sel.split(' ')[0]
                veiculo_id = next(v['id'] for v in self.veiculos_terceiros if v['placa'] == placa_veiculo)
        except (StopIteration, ValueError):
            messagebox.showerror("Erro", "Seleção inválida ou preço não encontrado.", parent=self.window)
            return

        viagem_obj = Viagem(
            data_viagem=data_str, transportadora_id=transp_id, localidade_id=loc_id,
            tipo_caminhao=tipo_caminhao, valor_base_frete=valor_base, bonus_percentual=bonus,
            motorista_nome=motorista, veiculo_id=veiculo_id)

        try:
            if self.id_viagem_em_edicao:
                self.db_manager.update('viagens', self.id_viagem_em_edicao, viagem_obj.to_dict())
            else:
                self.db_manager.insert('viagens', viagem_obj.to_dict())

            messagebox.showinfo("Sucesso",
                                f"Viagem {'atualizada' if self.id_viagem_em_edicao else 'registrada'} com sucesso!",
                                parent=self.window)
            self._limpar_campos()
            self._aplicar_filtros()
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro: {e}", parent=self.window)

    def _importar_viagens_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("Arquivos CSV", "*.csv")])
        if not filepath: return
        importer = ImportadorDeViagens(self.db_manager, filepath)
        resultado = importer.executar()
        if "erro_leitura" in resultado:
            messagebox.showerror("Erro", f"Não foi possível ler o arquivo: {resultado['erro_leitura']}",
                                 parent=self.window)
        else:
            messagebox.showinfo("Importação Concluída", f"Sucesso: {resultado['sucesso']}\nErros: {resultado['erros']}",
                                parent=self.window)
        self._aplicar_filtros()

    def _exportar_viagens_csv(self):
        if not self.tree_viagens.get_children():
            messagebox.showwarning("Exportar", "Não há dados para exportar.", parent=self.window);
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Arquivos CSV", "*.csv")])
        if not filepath: return
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                colunas_ids = [col for col in self.tree_viagens['columns'] if col != 'id']
                colunas = [self.tree_viagens.heading(col, "text") for col in colunas_ids]
                writer.writerow(colunas)
                for row_id in self.tree_viagens.get_children():
                    valores = self.tree_viagens.item(row_id)['values'][1:]
                    writer.writerow(valores)
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{filepath}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao exportar: {e}", parent=self.window)

    def _ordenar_coluna(self, treeview, coluna, reversa):
        """Função genérica para ordenar a tabela de viagens."""
        lista_de_dados = [(treeview.set(item_id, coluna), item_id) for item_id in treeview.get_children('')]

        colunas_numericas = ['id', 'valor_base', 'bonus', 'valor_final']

        try:
            if coluna in colunas_numericas:
                lista_de_dados.sort(
                    key=lambda t: float(str(t[0]).replace('R$', '').replace('%', '').replace(',', '.').strip()),
                    reverse=reversa)
            elif coluna == 'data':
                lista_de_dados.sort(key=lambda t: datetime.strptime(t[0], '%d/%m/%Y'), reverse=reversa)
            else:
                lista_de_dados.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)
        except ValueError:
            lista_de_dados.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)

        for indice, (valor, item_id) in enumerate(lista_de_dados):
            treeview.move(item_id, '', indice)

        for i, item_id in enumerate(treeview.get_children('')):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            treeview.item(item_id, tags=(tag,))

        treeview.heading(coluna, command=lambda: self._ordenar_coluna(treeview, coluna, not reversa))