import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
from tkcalendar import DateEntry
import csv
from database_manager import DatabaseManager
from abastecimento import Abastecimento


class RelatoriosAbastecimentoWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager

        self.abastecimentos = []
        self.fator_co2_por_combustivel = {}

        self.window = tk.Toplevel(parent)
        self.window.title("Relatórios de Abastecimento e Emissões de CO2")
        self.window.state('zoomed')

        self._load_initial_data()
        self._build_ui()

        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _load_initial_data(self):
        """Carrega dados que não mudam com frequência, como os parâmetros de CO2."""
        parametros_db = self.db_manager.fetch_all('parametros_co2')
        self.fator_co2_por_combustivel = {p['tipo_combustivel']: p['fator_emissao'] for p in parametros_db}

    def _build_ui(self):
        """Constrói a interface gráfica completa da janela de relatórios."""
        # --- Frame de Filtros e Botões ---
        frame_filtros = tk.LabelFrame(self.window, text="Filtros e Ações", padx=10, pady=10)
        frame_filtros.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_filtros, text="Data Início:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_data_inicio = DateEntry(frame_filtros, width=15, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_inicio.pack(side=tk.LEFT, padx=5)

        tk.Label(frame_filtros, text="Data Fim:").pack(side=tk.LEFT, padx=5)
        self.entry_data_fim = DateEntry(frame_filtros, width=15, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_fim.pack(side=tk.LEFT, padx=5)

        btn_gerar_relatorio = tk.Button(frame_filtros, text="Gerar Relatório", command=self._gerar_relatorio_filtrado)
        btn_gerar_relatorio.pack(side=tk.LEFT, padx=10)

        btn_exportar_csv = tk.Button(frame_filtros, text="Exportar para CSV", command=self._exportar_para_csv)
        btn_exportar_csv.pack(side=tk.RIGHT, padx=5)

        # --- Frame de Exibição do Total ---
        frame_total = tk.Frame(self.window, pady=5)
        frame_total.pack(fill='x', padx=10, pady=5)
        tk.Label(frame_total, text="Total de CO2 Emitido no Período:").pack(side=tk.LEFT, padx=5)
        self.label_total_co2 = tk.Label(frame_total, text="0.00 kg", font=('Helvetica', 12, 'bold'))
        self.label_total_co2.pack(side=tk.LEFT)

        # --- Tabela de Exibição do Relatório ---
        frame_tabela = tk.LabelFrame(self.window, text="Detalhes do Relatório", padx=10, pady=10)
        frame_tabela.pack(pady=10, padx=10, fill="both", expand=True)

        # --- AQUI ESTÁ A CORREÇÃO ---
        columns_ab = ("data_hora", "motorista", "veiculo", "centro_custo",
                      "tipo_combustivel", "litros", "valor_unitario",
                      "valor_total", "outros_gastos_valor", "custo_total_nota",
                      "emissao_co2", "outros_gastos_descricao")
        self.tree_relatorio = ttk.Treeview(frame_tabela, columns=columns_ab, show="headings")

        self.tree_relatorio.heading("data_hora", text="Data/Hora")
        self.tree_relatorio.heading("motorista", text="Motorista")
        self.tree_relatorio.heading("veiculo", text="Veículo")
        self.tree_relatorio.heading("centro_custo", text="Centro de Custo")
        self.tree_relatorio.heading("tipo_combustivel", text="Combustível")
        self.tree_relatorio.heading("litros", text="Litros")
        self.tree_relatorio.heading("valor_unitario", text="R$/Litro")
        self.tree_relatorio.heading("valor_total", text="Valor Comb. (R$)")
        self.tree_relatorio.heading("outros_gastos_valor", text="Outros Gastos (R$)")
        self.tree_relatorio.heading("custo_total_nota", text="Custo Total Nota (R$)")
        self.tree_relatorio.heading("emissao_co2", text="CO2 Emitido (kg)")
        self.tree_relatorio.heading("outros_gastos_descricao", text="Descrição Gastos")

        self.tree_relatorio.column("data_hora", width=120, anchor=tk.CENTER)
        self.tree_relatorio.column("motorista", width=120, anchor=tk.W)
        self.tree_relatorio.column("veiculo", width=150, anchor=tk.W)
        self.tree_relatorio.column("centro_custo", width=100, anchor=tk.W)
        self.tree_relatorio.column("tipo_combustivel", width=80, anchor=tk.W)
        self.tree_relatorio.column("litros", width=70, anchor="e")
        self.tree_relatorio.column("valor_unitario", width=70, anchor="e")
        self.tree_relatorio.column("valor_total", width=110, anchor="e")
        self.tree_relatorio.column("outros_gastos_valor", width=110, anchor="e")
        self.tree_relatorio.column("custo_total_nota", width=120, anchor="e")
        self.tree_relatorio.column("emissao_co2", width=100, anchor="e")
        self.tree_relatorio.column("outros_gastos_descricao", width=200, anchor="w")

        scrollbar = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL, command=self.tree_relatorio.yview)
        self.tree_relatorio.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_relatorio.pack(fill="both", expand=True)



    def _gerar_relatorio_filtrado(self):
        """Gera o relatório usando a consulta otimizada do DatabaseManager."""
        try:
            data_inicio = self.entry_data_inicio.get_date()
            data_fim = self.entry_data_fim.get_date()

            data_inicio_str = data_inicio.strftime('%Y-%m-%d')
            data_fim_str = data_fim.strftime('%Y-%m-%d')
        except Exception:
            messagebox.showwarning("Filtro Vazio", "Por favor, preencha as datas de início e fim.", parent=self.window)
            return

        if data_inicio > data_fim:
            messagebox.showwarning("Erro de Filtro", "A data de início não pode ser maior que a data de fim.",
                                   parent=self.window)
            return

        for item in self.tree_relatorio.get_children():
            self.tree_relatorio.delete(item)

        dados_relatorio = self.db_manager.fetch_abastecimentos_com_detalhes(data_inicio_str, data_fim_str)

        if not dados_relatorio:
            messagebox.showinfo("Relatório", "Nenhum abastecimento encontrado para o período selecionado.",
                                parent=self.window)
            self.label_total_co2.config(text="0.00 kg")
            return

        total_co2_emitido = 0.0
        for row in dados_relatorio:
            abastecimento_data_hora = datetime.fromisoformat(row['data_hora'])
            quantidade_litros = row['quantidade_litros']
            tipo_combustivel = row['tipo_combustivel']

            fator_emissao = self.fator_co2_por_combustivel.get(tipo_combustivel, 0.0)
            co2_abastecimento = quantidade_litros * fator_emissao
            total_co2_emitido += co2_abastecimento

            self.tree_relatorio.insert("", tk.END, values=(
                datetime.fromisoformat(row['data_hora']).strftime('%d/%m/%Y'),
                row['motorista_nome'],
                row['veiculo_info'],
                row['centro_custo_nome'],
                row['tipo_combustivel'],
                f"{row['quantidade_litros']:.2f}",
                f"{row['valor_unitario']:.2f}",
                f"{row['valor_total']:.2f}",
                f"{row.get('outros_gastos_valor', 0.0):.2f}",
                f"{row.get('custo_total_nota', 0.0):.2f}",
                f"{co2_abastecimento:.2f}",
                row.get('outros_gastos_descricao', '')
            ))

        self.label_total_co2.config(text=f"{total_co2_emitido:.2f} kg")

    def _exportar_para_csv(self):
        """Exporta os dados atualmente visíveis na tabela de histórico para um arquivo CSV."""
        if not self.tree_relatorio.get_children():
            messagebox.showwarning("Exportar CSV", "Não há dados na tabela para exportar. Gere um relatório primeiro.",
                                   parent=self.window)
            return

        try:
            nome_arquivo = f"relatorio_abastecimento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(nome_arquivo, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')

                colunas = [self.tree_relatorio.heading(col, "text") for col in self.tree_relatorio['columns']]
                writer.writerow(colunas)

                for row_id in self.tree_relatorio.get_children():
                    valores_linha = self.tree_relatorio.item(row_id)['values']
                    writer.writerow(valores_linha)

            messagebox.showinfo("Exportar CSV", f"Relatório exportado com sucesso para o arquivo:\n{nome_arquivo}",
                                parent=self.window)

        except Exception as e:
            messagebox.showerror("Erro de Exportação", f"Ocorreu um erro ao exportar o arquivo: {e}",
                                 parent=self.window)