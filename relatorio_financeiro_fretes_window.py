# relatorio_financeiro_fretes_window.py

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
from tkcalendar import DateEntry
import csv

from database_manager import DatabaseManager


class RelatorioFinanceiroFretesWindow:
    def __init__(self, parent, db_manager):
        self._coluna_ordenada = ""
        self._ordem_reversa = False
        self.parent = parent
        self.db_manager = db_manager

        self.window = tk.Toplevel(parent)
        self.window.title("Relatório Financeiro de Fretes por Transportadora")
        self.window.state('zoomed')

        self._build_ui()

        self.window.transient(parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)

    def _build_ui(self):
        # Frame de Filtros
        frame_filtros = tk.LabelFrame(self.window, text="Período de Análise", padx=10, pady=10)
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
        frame_tabela = tk.LabelFrame(self.window, text="Resumo por Transportadora", padx=10, pady=10)
        frame_tabela.pack(pady=10, padx=10, fill="both", expand=True)

        cols = ("transportadora", "num_viagens", "valor_total")
        self.tree_relatorio = ttk.Treeview(frame_tabela, columns=cols, show="headings")

        self.tree_relatorio.heading("transportadora", text="Transportadora",
                                    command=lambda: self._ordenar_coluna("transportadora", False))
        self.tree_relatorio.heading("num_viagens", text="Nº de Viagens",
                                    command=lambda: self._ordenar_coluna("num_viagens", False))
        self.tree_relatorio.heading("valor_total", text="Valor Total a Pagar (R$)",
                                    command=lambda: self._ordenar_coluna("valor_total", False))

        self.tree_relatorio.column("num_viagens", width=120, anchor="center")
        self.tree_relatorio.column("valor_total", width=200, anchor="e")

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

        dados = self.db_manager.fetch_resumo_fretes_por_transportadora(data_inicio.strftime('%Y-%m-%d'),
                                                                       data_fim.strftime('%Y-%m-%d'))

        for item in self.tree_relatorio.get_children():
            self.tree_relatorio.delete(item)

        if not dados:
            messagebox.showinfo("Relatório", "Nenhum dado encontrado para o período selecionado.", parent=self.window)
            return

        for row in dados:
            self.tree_relatorio.insert("", tk.END, values=(
                row['transportadora_nome'],
                row['numero_viagens'],
                f"{row['valor_total']:.2f}"
            ))

    def _ordenar_coluna(self, coluna, reversa):
        """Ordena os dados na Treeview com base na coluna clicada."""
        # Pega todos os itens da tabela e seus valores para a coluna selecionada
        # A lista conterá tuplas (valor_da_coluna, id_do_item)
        lista_de_dados = []
        for item_id in self.tree_relatorio.get_children(''):
            valor = self.tree_relatorio.set(item_id, coluna)
            lista_de_dados.append((valor, item_id))

        # Converte os valores para o tipo correto antes de ordenar
        # Isso garante que '10' venha depois de '2', e não antes.
        if coluna in ("num_viagens", "valor_total"):
            # Converte para número (float), tratando a vírgula decimal se houver
            lista_de_dados.sort(key=lambda t: float(t[0].replace(',', '.')), reverse=reversa)
        else:
            # Ordenação de texto (case-insensitive)
            lista_de_dados.sort(key=lambda t: str(t[0]).lower(), reverse=reversa)

        # Reinsere os itens na tabela na nova ordem
        for indice, (valor, item_id) in enumerate(lista_de_dados):
            self.tree_relatorio.move(item_id, '', indice)

        # Inverte a direção da ordenação para o próximo clique na mesma coluna
        self.tree_relatorio.heading(coluna, command=lambda: self._ordenar_coluna(coluna, not reversa))

    def _exportar_csv(self):
        if not self.tree_relatorio.get_children():
            messagebox.showwarning("Exportar", "Não há dados para exportar.", parent=self.window)
            return

        nome_arquivo = f"relatorio_financeiro_fretes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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