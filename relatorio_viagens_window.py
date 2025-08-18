# relatorio_viagens_window.py

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
from tkcalendar import DateEntry
import csv
from database_manager import DatabaseManager


class RelatorioViagensWindow:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db_manager = db_manager

        self.window = tk.Toplevel(parent)
        self.window.title("Relatório de Viagens de Frete")
        self.window.state('zoomed')

        self._build_ui()

        self.window.transient(parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        # Frame de Filtros
        frame_filtros = tk.LabelFrame(self.window, text="Filtros e Ações", padx=10, pady=10)
        frame_filtros.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_filtros, text="Data Início:").pack(side=tk.LEFT, padx=(0, 5))
        self.entry_data_inicio = DateEntry(frame_filtros, width=12, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_inicio.pack(side=tk.LEFT)

        tk.Label(frame_filtros, text="Data Fim:").pack(side=tk.LEFT, padx=(10, 5))
        self.entry_data_fim = DateEntry(frame_filtros, width=12, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.entry_data_fim.pack(side=tk.LEFT)

        btn_filtrar = tk.Button(frame_filtros, text="Gerar Relatório", command=self._gerar_relatorio)
        btn_filtrar.pack(side=tk.LEFT, padx=10)

        btn_exportar_csv = tk.Button(frame_filtros, text="Exportar para CSV", command=self._exportar_csv)
        btn_exportar_csv.pack(side=tk.RIGHT, padx=5)

        # Frame da Tabela
        frame_tabela = tk.LabelFrame(self.window, text="Viagens Realizadas", padx=10, pady=10)
        frame_tabela.pack(pady=10, padx=10, fill="both", expand=True)

        cols = ("data", "transportadora", "localidade", "tipo_caminhao", "veiculo", "motorista", "valor")
        self.tree_relatorio = ttk.Treeview(frame_tabela, columns=cols, show="headings")

        self.tree_relatorio.heading("data", text="Data")
        self.tree_relatorio.heading("transportadora", text="Transportadora")
        self.tree_relatorio.heading("localidade", text="Destino")
        self.tree_relatorio.heading("tipo_caminhao", text="Tipo Caminhão")
        self.tree_relatorio.heading("veiculo", text="Veículo")
        self.tree_relatorio.heading("motorista", text="Motorista")
        self.tree_relatorio.heading("valor", text="Valor (R$)")

        self.tree_relatorio.column("data", width=100, anchor="center")
        self.tree_relatorio.column("valor", width=120, anchor="e")

        self.tree_relatorio.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL, command=self.tree_relatorio.yview)
        self.tree_relatorio.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _gerar_relatorio(self):
        data_inicio = self.entry_data_inicio.get_date()
        data_fim = self.entry_data_fim.get_date()

        if data_inicio > data_fim:
            messagebox.showwarning("Erro", "A data de início não pode ser maior que a data de fim.", parent=self.window)
            return

        dados = self.db_manager.fetch_viagens_com_detalhes(data_inicio.strftime('%Y-%m-%d'),
                                                           data_fim.strftime('%Y-%m-%d'))

        for item in self.tree_relatorio.get_children():
            self.tree_relatorio.delete(item)

        if not dados:
            messagebox.showinfo("Relatório", "Nenhuma viagem encontrada para o período selecionado.",
                                parent=self.window)
            return

        for row in dados:
            data_formatada = datetime.strptime(row['data_viagem'], '%Y-%m-%d').strftime('%d/%m/%Y')
            self.tree_relatorio.insert("", tk.END, values=(
                data_formatada,
                row['transportadora_nome'],
                row['localidade_nome'],
                row['tipo_caminhao'],
                row['veiculo_info'],
                row['motorista_nome'],
                f"{row['valor_cobrado']:.2f}"
            ))

    def _exportar_csv(self):
        if not self.tree_relatorio.get_children():
            messagebox.showwarning("Exportar", "Não há dados para exportar. Gere um relatório primeiro.",
                                   parent=self.window)
            return

        nome_arquivo = f"relatorio_viagens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(nome_arquivo, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                colunas = [self.tree_relatorio.heading(col, "text") for col in self.tree_relatorio['columns']]
                writer.writerow(colunas)
                for row_id in self.tree_relatorio.get_children():
                    writer.writerow(self.tree_relatorio.item(row_id)['values'])
            messagebox.showinfo("Sucesso", f"Relatório salvo com sucesso em:\n{nome_arquivo}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao exportar o arquivo: {e}", parent=self.window)