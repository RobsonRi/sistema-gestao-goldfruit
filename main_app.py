import tkinter as tk
from tkinter import messagebox
#from database_manager import DatabaseManager
from gerenciar_funcionarios_window import GerenciarFuncionariosWindow
from estoque_window import EstoqueWindow
from gerenciar_veiculos_window import GerenciarVeiculosWindow
from abastecimento_window import AbastecimentoWindow
from relatorios_abastecimento_window import RelatoriosAbastecimentoWindow
from parametros_co2_window import ParametrosCO2Window
from gerenciar_fretes_window import GerenciarFretesWindow
from gerenciar_viagens_window import GerenciarViagensWindow
from relatorio_viagens_window import RelatorioViagensWindow
from relatorio_financeiro_fretes_window import RelatorioFinanceiroFretesWindow
from gerenciar_postos_window import GerenciarPostosWindow
from gerenciar_centros_custo_window import GerenciarCentrosCustoWindow
from firebase_manager import FirebaseManager

class MainApplication:
    def __init__(self, master):
        self.master = master
        master.title("Sistema de Gestão da Empresa")
        master.state('zoomed')

        self.db_manager = FirebaseManager()

        # Defina a cor de fundo para a janela principal (aqui é onde a mágica acontece!)
        self.master.configure(bg="#F0F0F0")  # Um cinza bem claro
        self.master.option_add("*Toplevel*background", "#F0F0F0") # Para garantir que novas janelas tenham o mesmo fundo
        self.master.option_add("*Dialog*background", "#F0F0F0") # Para as caixas de mensagem

        self._create_menu()
        self._create_widgets()

    def _create_menu(self):
        """Cria a barra de menus principal com as funcionalidades."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        menu_cadastros = tk.Menu(menubar, tearoff=0)
        menu_movimentacoes = tk.Menu(menubar, tearoff=0)
        menu_fretes = tk.Menu(menubar, tearoff=0)
        menu_relatorios = tk.Menu(menubar, tearoff=0)
        menu_configuracoes = tk.Menu(menubar, tearoff=0)

        menubar.add_cascade(label="Cadastros", menu=menu_cadastros)
        menubar.add_cascade(label="Movimentações", menu=menu_movimentacoes)
        menubar.add_cascade(label="Fretes", menu=menu_fretes)
        menubar.add_cascade(label="Relatórios", menu=menu_relatorios)
        menubar.add_cascade(label="Configurações", menu=menu_configuracoes)

        menu_cadastros.add_command(label="Cadastrar Funcionário", command=self.abrir_cadastro_motorista)
        menu_cadastros.add_command(label="Cadastrar Veículo", command=self.abrir_cadastro_veiculo)
        menu_cadastros.add_command(label="Cadastrar Centro de Custo", command=self.abrir_gerenciar_centros_custo)
        menu_cadastros.add_command(label="Cadastrar Posto de Combustível", command=self.abrir_gerenciar_postos)
        # Adicione aqui os outros cadastros, como Centros de Custo

        menu_movimentacoes.add_command(label="Gerenciar Custos", command=self.abrir_gerenciar_abastecimentos)
        menu_movimentacoes.add_command(label="Controle de Estoque", command=self.abrir_controle_estoque)

        menu_relatorios.add_command(label="Relatórios de Abastecimento", command=self.abrir_relatorios_abastecimento)

        menu_configuracoes.add_command(label="Parâmetros de CO2", command=self.abrir_config_co2)
        menu_configuracoes.add_separator()
        menu_fretes.add_command(label="Gerenciar Fretes", command=self.abrir_gerenciar_fretes)
        menu_fretes.add_separator()  # Adiciona uma linha de separação
        menu_fretes.add_command(label="Gerenciar Viagens", command=self.abrir_gerenciar_viagens)
        menu_relatorios.add_command(label="Relatório de Viagens", command=self.abrir_relatorio_viagens)
        menu_relatorios.add_command(label="Relatório Financeiro de Fretes",
                                    command=self.abrir_relatorio_financeiro_fretes)
        menu_configuracoes.add_command(label="Sair", command=self.on_closing)


    def _create_widgets(self):
        """Cria os widgets da janela principal (neste caso, apenas a mensagem de boas-vindas)."""
        # Adicione o parâmetro 'bg' para que o Label tenha a mesma cor de fundo
        label_bem_vindo = tk.Label(self.master, text="Bem-vindo ao Sistema de Gestão GoldFruit!", font=("Arial", 16, "bold"), bg="#F0F0F0")
        label_bem_vindo.pack(pady=50)

        # Adicione o parâmetro 'bg' para que o Label tenha a mesma cor de fundo
        label_instrucoes = tk.Label(self.master, text="Use o menu acima para acessar as funcionalidades.", font=("Arial", 12), bg="#F0F0F0")
        label_instrucoes.pack(pady=10)

    def abrir_cadastro_motorista(self):
        GerenciarFuncionariosWindow(self.master, self.db_manager)

    def abrir_controle_estoque(self):
        EstoqueWindow(self.master, self.db_manager)

    def abrir_cadastro_veiculo(self):
        GerenciarVeiculosWindow(self.master, self.db_manager)

    def abrir_gerenciar_abastecimentos(self):
        AbastecimentoWindow(self.master, self.db_manager)

    def abrir_relatorios_abastecimento(self):
        RelatoriosAbastecimentoWindow(self.master, self.db_manager)

    def abrir_config_co2(self):
        ParametrosCO2Window(self.master, self.db_manager)

    def abrir_gerenciar_fretes(self):
        GerenciarFretesWindow(self.master, self.db_manager)

    def abrir_gerenciar_viagens(self):
        GerenciarViagensWindow(self.master, self.db_manager)

    def abrir_relatorio_viagens(self):
        RelatorioViagensWindow(self.master, self.db_manager)

    def abrir_relatorio_financeiro_fretes(self):
        RelatorioFinanceiroFretesWindow(self.master, self.db_manager)

    def abrir_gerenciar_postos(self):
        GerenciarPostosWindow(self.master, self.db_manager)

    def abrir_gerenciar_centros_custo(self):
        GerenciarCentrosCustoWindow(self.master, self.db_manager)




    def on_closing(self):
        if messagebox.askokcancel("Sair", "Tem certeza que deseja sair?"):
            # Não precisamos mais de commit ou close_connection para o Firebase
            self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.state('zoomed')
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
