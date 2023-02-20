import os, pandas
from traceback import print_tb
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox, filedialog
import mysql.connector
import customtkinter, time
from PIL import ImageTk, Image
from win10toast import ToastNotifier
from tkcalendar import *
from datetime import datetime, timedelta, date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
#customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

#///////////////////////// FONTES UTILIZADAS
fonte_padrao = ("Calibri",12)
fonte_padrao_bold = ("Calibri Bold",12)
fonte_padrao_titulo = ("Calibri Bold",20)
fonte_padrao_titulo_janelas = ("Calibri Bold",16)
#///////////////////////// FIM FONTES UTILIZADAS

#///////////////////////// VARIAVEIS GLOBAIS
titulos = 'Simec Refeição 1.2'
usuario_logado = ''
data = time.strftime('%d/%m/%Y', time.localtime())
hora = time.strftime('%H:%M:%S', time.localtime())
hora_calculo_pedido = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())
refeicoes = ''
centro_custo = ''
contador_aprov = ''
controla_loop = 0
cursor = ''
contador_notificacao_inicial = 0
contador_notificacao_final = 0
#///////////////////////// FIM VARIAVEIS GLOBAIS

#///////////////////////// ESTILOS
estilo_botao_padrao_form = {'fg_color':'#232527', 'hover_color':'#343638', 'text_font':fonte_padrao }
estilo_botao_excluir = {'fg_color':'#8B0000', 'hover_color':'#343638', 'text_font':fonte_padrao, 'text_color':'#ffffff'}
estilo_entry_padrao = {'placeholder_text':" ", 'justify':'center','text_font':fonte_padrao, 'fg_color':'#f3f3f3', 'bg_color':'#ffffff', 'text_color':'#2a2d2e', 'border_color':'#2a2d2e'}
estilo_scrolledtext_padrão = {'font':fonte_padrao, 'wrap':WORD, 'relief':'flat', 'highlightthickness':2, 'highlightbackground':'#2a2d2e', 'highlightcolor':'#2a2d2e'}
estilo_optionmenu = {'fg_color':"#2a2d2e", 'button_color':'#1c1c1c', 'button_hover_color':'#4F4F4F', 'text_font':fonte_padrao}
cor_azul = '#1d366c'
cor_cinza = '#2a2d2e'
cor_branca = '#ffffff'
#///////////////////////// FIM ESTILOS

#///////////////////////// FUNÇÕES
def relatorio():
    cursor.execute("select \
            pedidos.id,\
            pedidos.data_pedido,\
            pedidos.hora_pedido,\
            usuarios.nome,\
            usuarios.email,\
            ccUser.descricao_cc,\
            ccPedido.descricao_cc,\
            ccNumPedido.nome_cc,\
            refeicoes.refeicoes,\
            pedidos.quantidade,\
            pedidos.custo_total,\
            pedidos.motivo,\
            pedidos.observacoes,\
            pedidos.data_entrega_prevista,\
            pedidos.hora,\
			pedidos.atendente,\
            pedidos.data_entrega_realizada,\
            pedidos.status_pedido\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto ccUser on usuarios.id_cc = ccUser.id\
            inner join centrocusto ccPedido on pedidos.id_cc = ccPedido.id\
            inner join centrocusto ccNumPedido on pedidos.id_cc = ccNumPedido.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            ORDER BY pedidos.id DESC")
    lista = cursor.fetchall() 
    df = pandas.DataFrame(lista, columns = ['ID_PEDIDO','DATA DO PEDIDO', 'HORA DO PEDIDO','SOLICITANTE','E-MAIL','C.C DO USUÁRIO','C.C DO PEDIDO','CENTRO DE CUSTO','REFEIÇÃO', 'QUANTIDADE','CUSTO TOTAL(R$)','MOTIVO', 'OBSERVAÇÕES','DT_PREVISTA','HORÁRIO_ENTREGA','FUNCIONÁRIO REFEITÓRIO','DT_ENTREGA','STATUS'])
    df["CUSTO TOTAL(R$)"] = df["CUSTO TOTAL(R$)"].astype(float)
    try:    
        full_path = filedialog.asksaveasfilename(title="Exportar...",initialfile='Relatório(Completo)', filetypes=[('Excel', '.xlsx'),('all files', '.*')], defaultextension='.xlsx', parent=root)
        if full_path != '':
            df.to_excel (full_path, index = False, header=True)
            #df.to_excel (r"C://usr//frete_transportadora.xlsx", index = False, header=True)
    except:
        messagebox.showerror('Relatório:', 'Erro ao exportar o relatório.\nPermissão negada.', parent=root)
        return False
    messagebox.showinfo('Relatório:', 'Relatório exportado com sucesso.', parent=root)

def notificacao():
    toaster = ToastNotifier()
    toaster.show_toast("Simec Refeição","\nExiste um novo PEDIDO para ser atendido.",duration=10, icon_path=None, threaded=True)

def ativa_loop(x):
    global controla_loop
    controla_loop = x

def loop_principal():
    if controla_loop == 1:
        loop = root.after(0, loop_principal)
        root.after_cancel(loop)
    else:
        root.after(180000, atualizar_lista_principal)

def atualizar_lista_principal():
    db.cmd_reset_connection()
    tree_principal.delete(*tree_principal.get_children())
    cursor.execute("SELECT versao FROM versao")
    versao = cursor.fetchone()
    if versao[0] != titulos:
        messagebox.showerror('Atualização:', f'Software desatualizado.\nVersão atual: "{versao[0]}". \n\nAtualize sua versão do software.\n\nQualquer dúvida, entre em contato com o administrador do sistema.\n\n***Contato:***\nRamal:7030\nE-mail: ivan.casagrande@gruposimec.com.br', parent=root)
        root.destroy()
    else:
        #print(usuario_logado)
        if usuario_logado[5] == 'RECURSOS HUMANOS': #\\ RH
            cursor.execute("select\
            pedidos.id,\
            pedidos.data_pedido,\
            usuarios.nome,\
            centrocusto.descricao_cc,\
            refeicoes.refeicoes,\
            pedidos.data_entrega_prevista,\
            pedidos.status_pedido,\
            pedidos.data_entrega_realizada\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto on pedidos.id_cc = centrocusto.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            ORDER BY pedidos.status_pedido = 'Encerrado',\
            pedidos.status_pedido = 'Cancelado',\
            pedidos.status_pedido = 'Em andamento',\
            pedidos.status_pedido = 'Aberto',\
            pedidos.id ASC ")

        elif usuario_logado[6] == '0' and usuario_logado[7] == '0': #\\USUÁRIO COMUM
            cursor.execute("select\
            pedidos.id,\
            pedidos.data_pedido,\
            usuarios.nome,\
            centrocusto.descricao_cc,\
            refeicoes.refeicoes,\
            pedidos.data_entrega_prevista,\
            pedidos.status_pedido,\
            pedidos.data_entrega_realizada\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto on pedidos.id_cc = centrocusto.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            WHERE usuarios.nome = %s\
            ORDER BY pedidos.status_pedido = 'Encerrado',\
            pedidos.status_pedido = 'Cancelado',\
            pedidos.status_pedido = 'Em andamento',\
            pedidos.status_pedido = 'Aberto',\
            pedidos.id ASC", (usuario_logado[1],))
        
        elif usuario_logado[6] == '1' and usuario_logado[7] == '0': #\\USUÁRIO GESTOR
            cursor.execute("select\
            pedidos.id,\
            pedidos.data_pedido,\
            usuarios.nome,\
            centrocusto.descricao_cc,\
            refeicoes.refeicoes,\
            pedidos.data_entrega_prevista,\
            pedidos.status_pedido,\
            pedidos.data_entrega_realizada\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto on pedidos.id_cc = centrocusto.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            WHERE usuarios.nome = %s\
            ORDER BY pedidos.status_pedido = 'Encerrado',\
            pedidos.status_pedido = 'Cancelado',\
            pedidos.status_pedido = 'Em andamento',\
            pedidos.status_pedido = 'Aberto',\
            pedidos.id ASC", (usuario_logado[1],))
        else:
            cursor.execute("select\
            pedidos.id,\
            pedidos.data_pedido,\
            usuarios.nome,\
            centrocusto.descricao_cc,\
            refeicoes.refeicoes,\
            pedidos.data_entrega_prevista,\
            pedidos.status_pedido,\
            pedidos.data_entrega_realizada\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto on pedidos.id_cc = centrocusto.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            WHERE (status_pedido <> 'Encerrado' AND status_pedido <> 'Cancelado')\
            ORDER BY data_entrega_prevista, status_pedido = 'Aberto' DESC")

        cont = 0
        for row in cursor:
            if cont % 2 == 0:
                tree_principal.insert('', 'end', text=" ",
                                        values=(
                                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]),
                                        tags=('par',))
            else:
                tree_principal.insert('', 'end', text=" ",
                                        values=(
                                        row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]),
                                        tags=('impar',))
            cont += 1
        
        #// CONTADOR PARA EXIBIR NOTIFICAÇÃO NO WINDOWS.        
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        global contador_notificacao_inicial
        global contador_notificacao_final
        contador_notificacao_final = cursor.fetchone()[0]
        if contador_notificacao_final > contador_notificacao_inicial and contador_notificacao_inicial !=0 and usuario_logado[7] == '1':
            contador_notificacao_inicial = contador_notificacao_final
            notificacao()
        else:
            contador_notificacao_inicial = contador_notificacao_final
    
    root.after(0, loop_principal)

def setup_botoes():
    lbl_user.configure(text=f'Usuário: {usuario_logado[1]} | Área: {usuario_logado[5]}')
    #// USUARIO RH COMUM
    if usuario_logado[6] == '0' and usuario_logado[7] == '0' and usuario_logado[5] == 'RECURSOS HUMANOS':
        btn_config.configure(state='normal')
        btn_rel.configure(state='normal')
        btn_aprov.configure(state='disabled')
        btn_solicit.configure(state='normal')
        btn_editar.configure(state='normal')
        #print('rh comum')
    #// USUARIO RH GESTOR
    elif usuario_logado[6] == '1' and usuario_logado[7] == '0' and usuario_logado[5] == 'RECURSOS HUMANOS':
        btn_config.configure(state='normal')
        btn_rel.configure(state='normal')
        btn_aprov.configure(state='disabled')
        btn_solicit.configure(state='normal')
        btn_editar.configure(state='normal')
        #print('rh gestor')

    #// USUARIO COMUM
    elif usuario_logado[6] == '0' and usuario_logado[7] == '0' and usuario_logado[5] != 'RECURSOS HUMANOS':
        btn_config.configure(state='disabled')
        btn_aprov.configure(state='disabled')
        btn_solicit.configure(state='disabled')
        btn_rel.configure(state='disabled')
        btn_editar.configure(state='disabled')
        #print('comum')
    #// USUARIO REFEITORIO
    elif usuario_logado[6] == '0' and usuario_logado[7] == '1':
        btn_config.configure(state='disabled')
        btn_aprov.configure(state='normal')
        btn_solicit.configure(state='disabled')
        btn_editar.configure(state='disabled')
        btn_rel.configure(state='normal')
        #print('refeitorio')
    #// USUARIO GESTOR
    else:
        btn_config.configure(state='disabled')
        btn_aprov.configure(state='disabled')
        btn_solicit.configure(state='normal')
        btn_editar.configure(state='normal')
        btn_rel.configure(state='disabled')

def login():
    ativa_loop(1)
    root2 = Toplevel(root)
    root2.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    root2.unbind_class("Button", "<Key-space>")
    root2.focus_force()
    root2.grab_set()
    
    #///////////////////////// FUNÇÕES
    def logar():
        usuario = ent_usuario.get()
        senha = ent_senha.get()

        if usuario == "" or senha == "":
            messagebox.showwarning('Login:', 'Digite o Usuário ou Senha.', parent=root2)
        else:
            cursor.execute("SELECT\
                usuarios.id,\
                usuarios.nome,\
                usuarios.usuario,\
                usuarios.email,\
                usuarios.senha,\
                centrocusto.descricao_cc,\
                usuarios.gestor,\
                usuarios.refeitorio \
                FROM usuarios inner join centrocusto on usuarios.id_cc = centrocusto.id WHERE usuario=%s AND senha=%s", (usuario, senha,))
            result = cursor.fetchone()
            if result is None:
                    messagebox.showwarning('Login:', 'Usuário ou Senha inválidos.', parent=root2)
            else:
                global usuario_logado
                usuario_logado = result
                root2.destroy()
                setup_botoes()
                ativa_loop(0)
                atualizar_lista_principal()
                
                
    def logar_bind(event):
        logar()
    def sair():
        root2.destroy()
        root.destroy()
    #///////////////////////// LAYOUT
    frame0 = customtkinter.CTkFrame(root2, corner_radius=10, fg_color='#ffffff', border_width=4, border_color='#2a2d2e')
    frame0.pack(padx=4, pady=10, fill="both", expand=True)

    frame1 = Frame(frame0, bg='#ffffff')
    frame1.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame2 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame2.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
    frame3 = Frame(frame0, bg='#ffffff')
    frame3.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame4 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame4.pack(padx=10, pady=10, fill="x", expand=False, side=TOP)
    frame5 = Frame(frame0, bg='#ffffff')
    frame5.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)


    #/////////FRAME1
    lbl_titulo = Label(frame1, text='Login', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#1d366c')
    lbl_titulo.grid(row=0, column=1)
    frame1.grid_columnconfigure(0, weight=1)
    frame1.grid_columnconfigure(2, weight=1)

    #/////////FRAME2 LINHA
        
    #/////////FRAME3
    lbl1=Label(frame3, text='Usuário:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl1.grid(row=0, column=1, sticky="w")
    ent_usuario = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=282)
    ent_usuario.grid(row=1, column=1)
    ent_usuario.focus_force()
    ent_usuario.bind("<Return>", logar_bind)
   
    lbl2=Label(frame3, text='Senha:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl2.grid(row=2, column=1, sticky="w")
    ent_senha = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=282, show='*')
    ent_senha.grid(row=3, column=1)
    ent_senha.bind("<Return>", logar_bind)

    frame3.grid_columnconfigure(0, weight=1)
    frame3.grid_columnconfigure(4, weight=1)

    #/////////FRAME4 LINHA

    #/////////FRAME5
    bt1 = customtkinter.CTkButton(frame5, text='Logar', **estilo_botao_padrao_form, width=134, command=logar)
    bt1.grid(row=0, column=1, padx=5)
    bt1 = customtkinter.CTkButton(frame5, text='Sair', **estilo_botao_padrao_form, width=134, command=sair)
    bt1.grid(row=0, column=2, padx=5)
    frame5.grid_columnconfigure(0, weight=1)
    frame5.grid_columnconfigure(3, weight=1)

    #ent_usuario.insert(0, 'ivan')
    #ent_senha.insert(0,'61765561')

    root2.update()
    largura = root2.winfo_width()
    altura = root2.winfo_height()
    window_width = largura
    window_height = altura+20
    screen_width = root2.winfo_screenwidth()
    screen_height = root2.winfo_screenheight() - 70
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root2.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
    root2.resizable(0, 0)
    root2.configure(bg='#ffffff')
    root2.title(titulos)
    root2.overrideredirect(True)
    root2.iconbitmap('img\\icone.ico')
    root2.wm_protocol("WM_DELETE_WINDOW", lambda: [ativa_loop(0), atualizar_lista_principal(), root2.destroy()])
    root2.mainloop()

def pedidos():
    ativa_loop(1)
    root2 = Toplevel(root)
    root2.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    root2.unbind_class("Button", "<Key-space>")
    root2.focus_force()
    root2.grab_set()

    window_width = 762
    window_height = 682
    screen_width = root2.winfo_screenwidth()
    screen_height = root2.winfo_screenheight() - 70
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root2.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
    #root2.resizable(0, 0)
    root2.configure(bg='#ffffff')
    root2.title(titulos)
    root2.iconbitmap('img\\icone.ico')


    #///////////////////////// FUNÇÕES
    def salvar():
        data = ent_data.get()
        hora_pedido = ent_hora.get()
        solicitante = usuario_logado[0]
        data_entrega = ent_dt_entrega.get()
        refeicao_escolhida = refeicoes        
        quantidade = ent_quant.get()
        total = ent_total.get()
        hora_entrega = clique_horario.get()
        cc_escolhido = centro_custo
        mot = txt_mot.get("1.0", 'end-1c')
        obs = txt_obs.get("1.0", 'end-1c')
        #print(data, solicitante, data_entrega, refeicao_escolhida,quantidade, total, hora_entrega, cc_escolhido, mot, obs)

        if data_entrega == '' or  refeicao_escolhida == '' or quantidade == '' or hora_entrega == '' or cc_escolhido == '' or mot == '' or total == '':
            messagebox.showwarning('+Novo Pedido:', 'Todos os campos devem ser preenchidos.', parent=root2)
        else:
            try:
                cursor.execute("INSERT INTO pedidos (\
                    data_pedido,\
                    id_solicitante,\
                    id_cc,\
                    id_refeicao,\
                    quantidade,\
                    observacoes,\
                    data_entrega_prevista,\
                    data_entrega_realizada,\
                    status_pedido,\
                    hora,\
                    motivo,\
                    custo_total,\
                    hora_pedido)\
                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (data, solicitante, cc_escolhido, refeicao_escolhida, quantidade, obs, data_entrega, '', 'Aberto', hora_entrega, mot, total, hora_pedido))
                db.commit()
            except:
                messagebox.showerror('+Nova Pedido:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                return False
            messagebox.showinfo('+Nova Pedido:', 'Pedido realizado com sucesso.', parent=root2)
            global controla_loop
            controla_loop = 0
            root2.destroy()
            atualizar_lista_principal()
        
    def setup_sm():
        ent_data.insert(0, data)
        ent_data.configure(state='readonly')
        ent_hora.insert(0, hora)
        ent_hora.configure(state='readonly')
        ent_solicitante.insert(0,usuario_logado[1])
        ent_solicitante.configure(state='readonly')
        ent_area_solic.insert(0,usuario_logado[5])
        ent_area_solic.configure(state='readonly')
        ent_email.insert(0,usuario_logado[3])
        ent_email.configure(state='readonly')
        ent_dt_entrega.configure(state='readonly')
        ent_preco.configure(state='readonly')
        txt_descricao.configure(state='disabled')
        ent_total.configure(state='readonly')
        ent_desc_cc.configure(state='readonly')

    def calculo_total():
        valor = float(ent_preco.get())
        qtd = int(ent_quant.get())
        ent_total.configure(state='normal')
        ent_total.delete(0, END)
        ent_total.insert(0, f'{valor*qtd:.2f}')
        ent_total.configure(state='readonly')

    def opt_refeicoes_clique(event):       
        print('22')
        cursor.execute("SELECT * FROM refeicoes WHERE refeicoes=%s", (clique_refeicoes.get(),))
        result_clique = cursor.fetchone()
        global refeicoes
        refeicoes = result_clique[0]
        ent_preco.configure(state='normal')
        ent_preco.delete(0, END)
        ent_preco.insert(0, result_clique[3])
        ent_preco.configure(state='readonly')
        txt_descricao.configure(state='normal')
        txt_descricao.delete('1.0', END)
        txt_descricao.insert(END,result_clique[2])
        txt_descricao.configure(state='disabled')
        ent_quant.delete(0, END)
        ent_total.configure(state='normal')
        ent_total.delete(0, END)
        ent_total.configure(state='disabled')
        clique_horario.set('')

    def opt_horario_clique(event):
        if ent_dt_entrega.get() == '' or clique_refeicoes.get() == '':
            messagebox.showinfo('+Novo Pedido:', 'Selecione a Data de Entrega e a Refeição.', parent=root2)
            clique_horario.set('')

        else:
            hora_selecionada = clique_horario.get()
            data_escolhida = ent_dt_entrega.get()
            hora_final = data_escolhida +' '+ hora_selecionada

            tempo = timedelta()
            time_1 = datetime.strptime(str(hora_calculo_pedido),"%d/%m/%Y %H:%M:%S")
            time_2 = datetime.strptime(str(hora_final),"%d/%m/%Y %H:%M:%S")

            tempo += time_2 - time_1
            tempo_horas = round((tempo.total_seconds()/3600),2)

            cursor.execute("SELECT * FROM refeicoes WHERE refeicoes=%s", (clique_refeicoes.get(),))
            resultado = cursor.fetchone()[4]
            if time_2 < time_1:
                messagebox.showinfo('+Novo Pedido:', 'Horário inválido, escolha outro!', parent=root2)
                clique_horario.set('')
            elif tempo_horas < float(resultado):
                messagebox.showinfo('+Novo Pedido:', f'Esta solicitação deve respeitar o tempo de preparo mínimo\nde {resultado} horas.', parent=root2)
                clique_horario.set('')

    def verifica_preco(event):
        preco = ent_preco.get()
        if preco == '':
            root2.focus_force()
            messagebox.showinfo('+Novo Pedido:', 'Selecione a Refeição primeiramente.', parent=root2)

    def campo_quantidade(event):
        numero = ent_quant.get()
        if numero.isdigit() == False and numero != '':
            messagebox.showinfo('+Novo Pedido:', 'Somente números inteiros são permitidos.', parent=root2)
            ent_quant.focus_force()
        else:
            if numero != '':
                calculo_total()
            else:
                pass

    def calendario():
        root3 = Toplevel(root2)
        window_width = 360
        window_height = 258
        screen_width = root3.winfo_screenwidth()
        screen_height = root3.winfo_screenheight() - 70
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        root3.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
        root3.resizable(0, 0)
        root3.configure(bg='#ffffff')
        root3.title(titulos)
        root3.overrideredirect(True)
        root3.focus_force()
        root3.grab_set()

        def escolher_data_bind(event):
            escolher_data()
        def escolher_data():
            ent_dt_entrega.configure(state='normal')
            ent_dt_entrega.delete(0, END)
            ent_dt_entrega.insert(0, cal.get_date())
            ent_dt_entrega.configure(state='readonly')
            clique_horario.set('')
            root3.destroy()
            root2.focus_force()
            root2.grab_set()
        
        hoje = date.today()
        cal = Calendar(root3, font=fonte_padrao, selectmode='day', locale='pt_BR',
                   mindate=hoje, disabledforeground='red', cursor="hand1")
        
        cal.pack(fill="both", expand=True)
    
        root3.bind('<Double-1>',escolher_data_bind) # Escolhe a data ao clicar 2x com o mouse
        root3,mainloop()

    def verifica_cc(event):
        cc = ent_cc.get()
        if cc != '':
            cc = ent_cc.get()
            cursor.execute("SELECT * FROM centrocusto WHERE nome_cc = %s",(cc,))
            centro = cursor.fetchone()
            if centro != None:
                ent_desc_cc.configure(state='normal')
                ent_desc_cc.delete(0, END)
                ent_desc_cc.insert(0, centro[2])
                ent_desc_cc.configure(state='readonly')
                global centro_custo
                centro_custo = centro[0]
            else:
                messagebox.showinfo('+Novo Pedido:', 'Centro de Custo não encontrado.', parent=root2)
                ent_cc.delete(0, END)
                ent_desc_cc.configure(state='normal')
                ent_desc_cc.delete(0, END)
                ent_desc_cc.configure(state='readonly')
                ent_cc.focus_force()

    #/////////////////////////SCROLLBAR
    def on_mousewheel(event):
        my_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

    def FrameWidth(event):
        canvas_width = event.width
        my_canvas.itemconfig(my_canvas_frame, width = canvas_width)

    def OnFrameConfigure(event):
            my_canvas.configure(scrollregion=my_canvas.bbox("all"))


    frame = customtkinter.CTkFrame(root2, fg_color='#ffffff')
    frame.pack(fill = BOTH, expand = TRUE, padx = 0, pady = 0)

    my_canvas = customtkinter.CTkCanvas(frame, bg= '#ffffff')
    my_canvas.pack(side = LEFT, fill = BOTH, expand = TRUE)
    #my_canvas.bind_all("<MouseWheel>", on_mousewheel) // bind toda area do canvas
    my_canvas.bind("<MouseWheel>", on_mousewheel) # // bind somente a área do scrool

    mailbox_frame = customtkinter.CTkFrame(my_canvas, fg_color='#ffffff')

    my_canvas_frame = my_canvas.create_window((0,0), window=mailbox_frame, anchor = NW)
    #mailbox_frame.pack(side = LEFT, fill = BOTH, expand = True)


    mail_scroll = customtkinter.CTkScrollbar(my_canvas, orientation = "vertical", command = my_canvas.yview, scrollbar_color='#D3D3D3', scrollbar_hover_color='#C0C0C0', fg_color='#ffffff' )
    mail_scroll.pack(side = RIGHT, fill = Y)

    my_canvas.config(yscrollcommand = mail_scroll.set)

    mailbox_frame.bind("<Configure>", OnFrameConfigure)
    my_canvas.bind('<Configure>', FrameWidth)

    #///////////////////////// LAYOUT
    frame0 = customtkinter.CTkFrame(mailbox_frame, corner_radius=10, fg_color='#ffffff', border_width=4, border_color='#2a2d2e')
    frame0.pack(padx=20, pady=10, fill="both", expand=True)

    frame1 = Frame(frame0, bg='#ffffff')
    frame1.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame2 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame2.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
    frame3 = Frame(frame0, bg='#ffffff')
    frame3.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame4 = Frame(frame0, bg='#ffffff')
    frame4.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame5 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame5.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
    frame6 = Frame(frame0, bg='#ffffff')
    frame6.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame7 = Frame(frame0, bg='#ffffff')
    frame7.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame8 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame8.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame9 = Frame(frame0, bg='#ffffff')
    frame9.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame10 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame10.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame11 = Frame(frame0, bg='#ffffff')
    frame11.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)


    lbl_titulo = Label(frame1, text='+Novo Pedido', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#1d366c')
    lbl_titulo.grid(row=0, column=1)
    frame1.grid_columnconfigure(0, weight=1)
    frame1.grid_columnconfigure(2, weight=1)

    #/////////FRAME2 LINHA HORIZONTAL
    
    #/////////FRAME3
    lbl2=Label(frame3, text='Data:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl2.grid(row=0, column=1, sticky="w", padx=3)
    ent_data = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=170)
    ent_data.grid(row=1, column=1, padx=3)

    lbl1=Label(frame3, text='Hora:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl1.grid(row=0, column=2, sticky="w", padx=3)
    ent_hora = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=170)
    ent_hora.grid(row=1, column=2, padx=3)

    lbl1=Label(frame3, text='Solicitante:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl1.grid(row=0, column=3, sticky="w", padx=3)
    ent_solicitante = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=340)
    ent_solicitante.grid(row=1, column=3, padx=3)

    frame3.grid_columnconfigure(0, weight=1)
    frame3.grid_columnconfigure(4, weight=1)

    #/////////FRAME4
    lbl1=Label(frame4, text='Área do Solicitante:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl1.grid(row=2, column=1, sticky="w", padx=5)
    ent_area_solic = customtkinter.CTkEntry(frame4, **estilo_entry_padrao, width=340)
    ent_area_solic.grid(row=3, column=1, padx=5)

    lbl1=Label(frame4, text='E-mail:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl1.grid(row=2, column=2, sticky="w", padx=5)
    ent_email = customtkinter.CTkEntry(frame4, **estilo_entry_padrao, width=340)
    ent_email.grid(row=3, column=2, padx=5)

    frame4.grid_columnconfigure(0, weight=1)
    frame4.grid_columnconfigure(4, weight=1)

    #/////////FRAME5 LINHA HORIZONTAL

    #/////////FRAME6
    img_logo = Image.open('img\\calendario.png')
    resize_logo = img_logo.resize((26, 26))
    nova_img_logo = ImageTk.PhotoImage(resize_logo)

    lbl=Button(frame6, text='Data de Entrega: ', image=nova_img_logo, compound=RIGHT, font=fonte_padrao_bold, fg='#880000',borderwidth=0, relief=RIDGE, bg=cor_branca, activebackground=cor_branca, cursor="hand2", command=calendario)
    lbl.grid(row=0, column=1, sticky="w", padx=6)
    
    ent_dt_entrega = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=180)
    ent_dt_entrega.grid(row=1, column=1, sticky="w", padx=6)

    clique_refeicoes = StringVar()
    lista_refeicoes = []
    cursor.execute("SELECT * FROM refeicoes LIMIT 0,1")
    result = cursor.fetchone()
    if result == None:
        lista_refeicoes.append('')
    else:
        cursor.execute("SELECT * FROM refeicoes ORDER BY refeicoes")
        for i in cursor:
            lista_refeicoes.append(i[1])
    
    lbl=Label(frame6, text='Refeição: ', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
    lbl.grid(row=2, column=1, sticky="w", padx=6)
    opt_refeicoes = ttk.Combobox(frame6, textvariable=clique_refeicoes, values=lista_refeicoes, width=32, height=20, font=fonte_padrao, state='readonly')
    opt_refeicoes.grid(row=3, column=1)
    opt_refeicoes.bind("<<ComboboxSelected>>", opt_refeicoes_clique)

    lbl=Label(frame6, text='Preço(R$):', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl.grid(row=2, column=2, sticky="w")
    ent_preco = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=110, textvariable=campo_quantidade)
    ent_preco.grid(row=3, column=2, sticky="w")

    lbl=Label(frame6, text='Quantidade:', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
    lbl.grid(row=2, column=3, sticky="w")
    ent_quant = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=110, textvariable=campo_quantidade)
    ent_quant.grid(row=3, column=3, sticky="w")
    ent_quant.bind("<FocusIn>", verifica_preco)
    ent_quant.bind("<FocusOut>", campo_quantidade)
    
    lbl=Label(frame6, text='Total(R$):', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl.grid(row=2, column=4, sticky="w")
    ent_total = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=110, textvariable=campo_quantidade)
    ent_total.grid(row=3, column=4, sticky="w")

    lbl=Label(frame6, text='Detalhes: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl.grid(row=4, column=1, sticky="w", padx=6)
    txt_descricao = scrolledtext.ScrolledText(frame6, **estilo_scrolledtext_padrão, width=82, height=2)
    txt_descricao.grid(row=5, column=1, columnspan=4, padx=6)

    frame6.grid_columnconfigure(0, weight=1)
    frame6.grid_columnconfigure(6, weight=1)

    #/////////FRAME7
    clique_horario = StringVar()
    lista_horario = [
        '00:00:00',
        '00:30:00',
        '01:00:00',
        '01:30:00',
        '02:00:00',
        '02:30:00',
        '03:00:00',
        '03:30:00',
        '04:00:00',
        '04:30:00',
        '05:00:00',
        '05:30:00',
        '06:00:00',
        '06:30:00',
        '07:00:00',
        '07:30:00',
        '08:00:00',
        '08:30:00',
        '09:00:00',
        '09:30:00',
        '10:00:00',
        '10:30:00',
        '11:00:00',
        '11:30:00',
        '12:00:00',
        '12:30:00',
        '13:00:00',
        '13:30:00',
        '14:00:00',
        '14:30:00',
        '15:00:00',
        '15:30:00',
        '16:00:00',
        '16:30:00',
        '17:00:00',
        '17:30:00',
        '18:00:00',
        '18:30:00',
        '19:00:00',
        '19:30:00',
        '20:00:00',
        '20:30:00',
        '21:00:00',
        '21:30:00',
        '22:00:00',
        '22:30:00',
        '23:00:00',
        '23:30:00']
    

    lbl=Label(frame7, text='Horário para Entrega: ', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
    lbl.grid(row=2, column=1, sticky="w")
    opt_horario = ttk.Combobox(frame7, textvariable=clique_horario, values=lista_horario, width=22, state='readonly')
    opt_horario.grid(row=3, column=1, sticky="w")
    opt_horario.bind("<<ComboboxSelected>>", opt_horario_clique)
    
    lbl=Label(frame7, text='Centro de Custo:', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
    lbl.grid(row=2, column=2, sticky="w", padx=12)
    ent_cc = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=170, textvariable=campo_quantidade)
    ent_cc.grid(row=3, column=2, sticky="w", padx=12)
    ent_cc.bind("<FocusOut>", verifica_cc)   
    
    lbl=Label(frame7, text='Descrição|Centro de Custo: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl.grid(row=2, column=3, sticky="w")
    ent_desc_cc = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=320, textvariable=campo_quantidade)
    ent_desc_cc.grid(row=3, column=3, sticky="w")

    frame7.grid_columnconfigure(0, weight=1)
    frame7.grid_columnconfigure(4, weight=1)

    
    #/////////FRAME8 LINHA HORIZONTAL

    #/////////FRAME9
    lbl=Label(frame9, text='Motivo:', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
    lbl.grid(row=0, column=1, sticky="w")
    txt_mot = scrolledtext.ScrolledText(frame9, **estilo_scrolledtext_padrão, width=82, height=2)
    txt_mot.grid(row=1, column=1)
    
    lbl=Label(frame9, text='Observações: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl.grid(row=2, column=1, sticky="w")
    txt_obs = scrolledtext.ScrolledText(frame9, **estilo_scrolledtext_padrão, width=82, height=2)
    txt_obs.grid(row=3, column=1)

    frame9.grid_columnconfigure(0, weight=1)
    frame9.grid_columnconfigure(3, weight=1)

    #/////////FRAME10 LINHA HORIZONTAL

    #/////////FRAME11
    bt1 = customtkinter.CTkButton(frame11, text='Confirmar', **estilo_botao_padrao_form, command=salvar)
    bt1.grid(row=0, column=1, pady=2)
    
    frame11.grid_columnconfigure(0, weight=1)
    frame11.grid_columnconfigure(2, weight=1)

    '''root2.update()
    largura = root2.winfo_width()
    altura = root2.winfo_height()
    print(largura, altura)'''

    setup_sm()
    root2.wm_protocol("WM_DELETE_WINDOW", lambda: [ativa_loop(0), atualizar_lista_principal(), root2.destroy()])
    root2.mainloop()

def atender_pedido():
    ativa_loop(0)    
    lista_select = tree_principal.focus()
    if lista_select == "":
        messagebox.showwarning('Atendimento:', 'Selecione um pedido na lista!', parent=root)
    else:
        valor_lista = tree_principal.item(lista_select, "values")[0]
        try:
            cursor.execute("select \
            pedidos.id,\
            pedidos.data_pedido,\
            usuarios.nome,\
            usuarios.email,\
            ccUser.descricao_cc,\
            ccPedido.descricao_cc,\
            ccNumPedido.nome_cc,\
            refeicoes.refeicoes,\
            pedidos.quantidade,\
            pedidos.observacoes,\
            pedidos.data_entrega_prevista,\
			pedidos.atendente,\
            pedidos.data_entrega_realizada,\
            pedidos.status_pedido,\
            pedidos.hora,\
            pedidos.motivo,\
            pedidos.custo_total,\
            pedidos.hora_pedido\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto ccUser on usuarios.id_cc = ccUser.id\
            inner join centrocusto ccPedido on pedidos.id_cc = ccPedido.id\
            inner join centrocusto ccNumPedido on pedidos.id_cc = ccNumPedido.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            WHERE pedidos.id = %s ORDER BY pedidos.id DESC",(valor_lista,))
            result2 = cursor.fetchone()

        except:
            messagebox.showerror('Atendimento:', 'Erro de conexão com o Banco de Dados.', parent=root)
            return False
        
        if result2[13] == 'Encerrado' or result2[13] == 'Cancelado':
            messagebox.showerror('Atendimento:', 'Este pedido foi "Encerrado" ou "Cancelado".', parent=root)
        else:
            root2 = Toplevel(root)
            root2.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
            root2.unbind_class("Button", "<Key-space>")
            root2.focus_force()
            root2.grab_set()

            window_width = 760
            window_height = 690
            screen_width = root2.winfo_screenwidth()
            screen_height = root2.winfo_screenheight() - 70
            x_cordinate = int((screen_width / 2) - (window_width / 2))
            y_cordinate = int((screen_height / 2) - (window_height / 2))
            root2.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
            #root2.resizable(0, 0)
            root2.configure(bg='#ffffff')
            root2.title(titulos)
            root2.iconbitmap('img\\icone.ico')


            #///////////////////////// FUNÇÕES
            def setup_atendimento():
                ent_data.insert(0, result2[1])
                ent_data.configure(state='readonly')
                ent_hora_pedido.insert(0, result2[17])
                ent_hora_pedido.configure(state='readonly')                
                ent_solicitante.insert(0,result2[2])
                ent_solicitante.configure(state='readonly')
                ent_area_solic.insert(0,result2[4])
                ent_area_solic.configure(state='readonly')
                ent_email.insert(0,result2[3])
                ent_email.configure(state='readonly')
                ent_refeicao.insert(0,result2[7])
                ent_refeicao.configure(state='readonly')
                ent_quant.insert(0,result2[8])
                ent_quant.configure(state='readonly')
                ent_dt_entrega.insert(0,result2[10])
                ent_dt_entrega.configure(state='readonly')
                ent_hora.insert(0,result2[14])
                ent_hora.configure(state='readonly')
                ent_area_pedido.insert(0,result2[5])
                ent_area_pedido.configure(state='readonly')
                ent_cc.insert(0,result2[6])
                ent_cc.configure(state='readonly')
                txt_mot.insert(END,result2[15])
                txt_mot.configure(state='disabled')

                if result2[9] == None:
                    txt_obs.insert(END,'')
                    txt_obs.configure(state='disabled')
                else:
                    txt_obs.insert(END,result2[9])
                    txt_obs.configure(state='disabled')

                if result2[11] == None:
                    ent_refeitorio.insert(0, usuario_logado[1])
                    ent_refeitorio.configure(state='readonly')
                else:
                    ent_refeitorio.insert(0,result2[11])
                    ent_refeitorio.configure(state='readonly')
                
                ent_status.insert(0,result2[13])
                ent_status.configure(state='readonly')
                ent_total.insert(0,result2[16])
                ent_total.configure(state='readonly')

            def opt_status_clique(event):
                ent_status.configure(state='normal')    
                ent_status.delete(0,END)      
                ent_status.insert(0,clique_status.get())
                ent_status.configure(state='readonly')         
            def confirmar():
                refeitorio = ent_refeitorio.get()
                status = ent_status.get()
                if status == 'Encerrado' or 'Cancelado':
                    try:
                        cursor.execute("UPDATE pedidos SET status_pedido = %s, atendente = %s, data_entrega_realizada = %s WHERE id = %s",(status, refeitorio, data, result2[0],))
                        db.commit()
                    except:
                        messagebox.showerror('Atendimento:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False
                else:
                    try:
                        cursor.execute("UPDATE pedidos SET status_pedido = %s, atendente = %s WHERE id = %s",(status, refeitorio, result2[0],))
                        db.commit()
                    except:
                        messagebox.showerror('Atendimento:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False                    
                messagebox.showinfo('Atendimento:', 'Alteração realizada com sucesso.', parent=root2)
                root2.destroy()
                atualizar_lista_principal()

                    
            #/////////////////////////SCROLLBAR
            def on_mousewheel(event):
                my_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

            def FrameWidth(event):
                canvas_width = event.width
                my_canvas.itemconfig(my_canvas_frame, width = canvas_width)

            def OnFrameConfigure(event):
                    my_canvas.configure(scrollregion=my_canvas.bbox("all"))


            frame = customtkinter.CTkFrame(root2, fg_color='#ffffff')
            frame.pack(fill = BOTH, expand = TRUE, padx = 0, pady = 0)

            my_canvas = customtkinter.CTkCanvas(frame, bg= '#ffffff')
            my_canvas.pack(side = LEFT, fill = BOTH, expand = TRUE)
            my_canvas.bind_all("<MouseWheel>", on_mousewheel)

            mailbox_frame = customtkinter.CTkFrame(my_canvas, fg_color='#ffffff')

            my_canvas_frame = my_canvas.create_window((0,0), window=mailbox_frame, anchor = NW)
            #mailbox_frame.pack(side = LEFT, fill = BOTH, expand = True)


            mail_scroll = customtkinter.CTkScrollbar(my_canvas, orientation = "vertical", command = my_canvas.yview, scrollbar_color='#D3D3D3', scrollbar_hover_color='#C0C0C0', fg_color='#ffffff' )
            mail_scroll.pack(side = RIGHT, fill = Y)

            my_canvas.config(yscrollcommand = mail_scroll.set)

            mailbox_frame.bind("<Configure>", OnFrameConfigure)
            my_canvas.bind('<Configure>', FrameWidth)            
            
            #///////////////////////// LAYOUT
            frame0 = customtkinter.CTkFrame(mailbox_frame, corner_radius=10, fg_color='#ffffff', border_width=4, border_color='#2a2d2e')
            frame0.pack(padx=20, pady=10, fill="both", expand=True)
       
            frame1 = Frame(frame0, bg='#ffffff')
            frame1.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame2 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame2.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
            frame3 = Frame(frame0, bg='#ffffff')
            frame3.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame4 = Frame(frame0, bg='#ffffff')
            frame4.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame5 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame5.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
            frame6 = Frame(frame0, bg='#ffffff')
            frame6.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame7 = Frame(frame0, bg='#ffffff')
            frame7.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame8 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame8.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame9 = Frame(frame0, bg='#ffffff')
            frame9.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame10 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame10.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame11 = Frame(frame0, bg='#ffffff')
            frame11.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)


            lbl_titulo = Label(frame1, text=f'Atendimento - Pedido: nº {result2[0]}', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#1d366c')
            lbl_titulo.grid(row=0, column=1)
            frame1.grid_columnconfigure(0, weight=1)
            frame1.grid_columnconfigure(2, weight=1)

            #/////////FRAME2 LINHA HORIZONTAL
            
            #/////////FRAME3
            lbl2=Label(frame3, text='Data:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl2.grid(row=0, column=1, sticky="w", padx=3)
            ent_data = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=170)
            ent_data.grid(row=1, column=1, padx=3)

            lbl2=Label(frame3, text='Hora:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl2.grid(row=0, column=2, sticky="w", padx=3)
            ent_hora_pedido = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=170)
            ent_hora_pedido.grid(row=1, column=2, padx=3)

            lbl1=Label(frame3, text='Solicitante:', font=fonte_padrao, bg='#ffffff', fg='#800000')
            lbl1.grid(row=0, column=3, sticky="w", padx=3)
            ent_solicitante = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=340)
            ent_solicitante.grid(row=1, column=3, padx=3)
            
            frame3.grid_columnconfigure(0, weight=1)
            frame3.grid_columnconfigure(4, weight=1)

            #/////////FRAME4
            lbl1=Label(frame4, text='Área do Solicitante:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=2, column=1, sticky="w", padx=5)
            ent_area_solic = customtkinter.CTkEntry(frame4, **estilo_entry_padrao, width=340)
            ent_area_solic.grid(row=3, column=1, padx=5)

            lbl1=Label(frame4, text='E-mail:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=2, column=2, sticky="w", padx=5)
            ent_email = customtkinter.CTkEntry(frame4, **estilo_entry_padrao, width=340)
            ent_email.grid(row=3, column=2, padx=5)


            frame4.grid_columnconfigure(0, weight=1)
            frame4.grid_columnconfigure(3, weight=1)
            
            #/////////FRAME5 LINHA HORIZONTAL

            #/////////FRAME6
            lbl=Label(frame6, text='Área da Solicitação: ', font=fonte_padrao, bg='#ffffff', fg='#800000')
            lbl.grid(row=2, column=1, sticky="w", padx=5)
            ent_area_pedido = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=340)
            ent_area_pedido.grid(row=3, column=1, padx=(0,5))
            
            lbl=Label(frame6, text='Centro de Custo: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=2, column=2, sticky="w", padx=5)
            ent_cc = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=340)
            ent_cc.grid(row=3, column=2, padx=(5,0))
            
            frame6.grid_columnconfigure(0, weight=1)
            frame6.grid_columnconfigure(4, weight=1)

            #/////////FRAME7
            lbl=Label(frame7, text='Refeição: ', font=fonte_padrao, bg='#ffffff', fg='#800000')
            lbl.grid(row=0, column=1, sticky="w", padx=(0,3))
            ent_refeicao = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=170)
            ent_refeicao.grid(row=1, column=1, padx=3)

            lbl=Label(frame7, text='Quantidade:', font=fonte_padrao, bg='#ffffff', fg='#800000')
            lbl.grid(row=0, column=2, sticky="w", padx=3)
            ent_quant = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=170)
            ent_quant.grid(row=1, column=2, padx=3)

            lbl=Label(frame7, text='Valor Total R$:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=0, column=3, sticky="w", padx=3)
            ent_total = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=106)
            ent_total.grid(row=1, column=3, padx=3)

            lbl=Label(frame7, text='Data|Entrega:', font=fonte_padrao, bg='#ffffff', fg='#800000')
            lbl.grid(row=0, column=4, sticky="w", padx=3)
            ent_dt_entrega = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=106)
            ent_dt_entrega.grid(row=1, column=4, padx=3)

            lbl=Label(frame7, text='Hora|Entrega:', font=fonte_padrao, bg='#ffffff', fg='#800000')
            lbl.grid(row=0, column=5, sticky="w", padx=3)
            ent_hora = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=106)
            ent_hora.grid(row=1, column=5, padx=(3,0))


            frame7.grid_columnconfigure(0, weight=1)
            frame7.grid_columnconfigure(6, weight=1)

            #/////////FRAME8 LINHA HORIZONTAL

            #/////////FRAME9
            lbl=Label(frame9, text='Motivo: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=0, column=1, sticky="w")
            txt_mot = scrolledtext.ScrolledText(frame9, **estilo_scrolledtext_padrão, width=82, height=4)
            txt_mot.grid(row=1, column=1)


            lbl=Label(frame9, text='Observações: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=2, column=1, sticky="w")
            txt_obs = scrolledtext.ScrolledText(frame9, **estilo_scrolledtext_padrão, width=82, height=4)
            txt_obs.grid(row=3, column=1)

            frame9.grid_columnconfigure(0, weight=1)
            frame9.grid_columnconfigure(3, weight=1)

            #/////////FRAME10 LINHA HORIZONTAL

            #/////////FRAME11
            lbl1=Label(frame11, text='Funcionário do Refeitório:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=0, column=1, sticky="w", padx=5)
            ent_refeitorio = customtkinter.CTkEntry(frame11, **estilo_entry_padrao, width=230)
            ent_refeitorio.grid(row=1, column=1, padx=5)

            lbl1=Label(frame11, text='Status:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=0, column=2, sticky="w", padx=5)
            ent_status = customtkinter.CTkEntry(frame11, **estilo_entry_padrao, width=180)
            ent_status.grid(row=1, column=2, padx=5)

            clique_status = StringVar()
            lista_area = ['Em andamento','Encerrado','Cancelado']
            lbl=Label(frame11, text='Alterar Status: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=0, column=3, sticky="w", padx=5)
            opt_area = customtkinter.CTkOptionMenu(frame11, variable=clique_status, values=lista_area, width=238, **estilo_optionmenu, command=opt_status_clique)
            opt_area.grid(row=1, column=3, padx=5)

            btn_confirm = customtkinter.CTkButton(frame11, text='Confirmar', **estilo_botao_padrao_form, command=confirmar, width=200)
            btn_confirm.grid(row=2, column=1, columnspan=3, pady=20)

            frame11.grid_columnconfigure(0, weight=1)
            frame11.grid_columnconfigure(4, weight=1)

           
            '''root2.update()
            largura = frame0.winfo_width()
            altura = frame0.winfo_height()
            print(largura, altura)'''
            setup_atendimento()
            root2.wm_protocol("WM_DELETE_WINDOW", lambda: [ativa_loop(0), atualizar_lista_principal(), root2.destroy()])
            root2.mainloop()

def editar_pedido():
    ativa_loop(0)    
    lista_select = tree_principal.focus()
    if lista_select == "":
        messagebox.showwarning('Atendimento:', 'Selecione um pedido na lista!', parent=root)
    else:
        valor_lista = tree_principal.item(lista_select, "values")[0]
        try:
            cursor.execute("select \
            pedidos.id,\
            pedidos.data_pedido,\
            usuarios.nome,\
            usuarios.email,\
            ccUser.descricao_cc,\
            ccPedido.descricao_cc,\
            ccNumPedido.nome_cc,\
            refeicoes.refeicoes,\
            refeicoes.descricao,\
            refeicoes.preco,\
            pedidos.quantidade,\
            pedidos.observacoes,\
            pedidos.data_entrega_prevista,\
			pedidos.atendente,\
            pedidos.data_entrega_realizada,\
            pedidos.status_pedido,\
            pedidos.hora,\
            pedidos.motivo,\
            pedidos.custo_total,\
            pedidos.hora_pedido\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto ccUser on usuarios.id_cc = ccUser.id\
            inner join centrocusto ccPedido on pedidos.id_cc = ccPedido.id\
            inner join centrocusto ccNumPedido on pedidos.id_cc = ccNumPedido.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            WHERE pedidos.id = %s ORDER BY pedidos.id DESC",(valor_lista,))
            result2 = cursor.fetchone()
            #print(result2)
        except:
            messagebox.showerror('Editar|Pedido:', 'Erro de conexão com o Banco de Dados.', parent=root)
            return False
        if result2[15] == 'Em andamento':
            messagebox.showerror('Editar|Pedido:', 'Pedidos com o status "Em andamento", não podem ser editados.', parent=root)

        elif result2[15] == 'Encerrado' or result2[15] == 'Cancelado':
            messagebox.showerror('Editar|Pedido:', 'Este pedido foi "Encerrado" ou "Cancelado".', parent=root)
        else:
            root2 = Toplevel(root)
            root2.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
            root2.unbind_class("Button", "<Key-space>")
            root2.focus_force()
            root2.grab_set()

            window_width = 762
            window_height = 682
            screen_width = root2.winfo_screenwidth()
            screen_height = root2.winfo_screenheight() - 70
            x_cordinate = int((screen_width / 2) - (window_width / 2))
            y_cordinate = int((screen_height / 2) - (window_height / 2))
            root2.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
            #root2.resizable(0, 0)
            root2.configure(bg='#ffffff')
            root2.title(titulos)
            root2.iconbitmap('img\\icone.ico')


            #///////////////////////// FUNÇÕES
            def excluir():
                db.cmd_reset_connection()
                cursor.execute('select status_pedido from pedidos where id =%s', (result2[0],))
                if (cursor.fetchone()[0]) == 'Aberto':
                    pergunta = messagebox.askyesno('Excluir Pedido', 'Confirma a exclusão deste pedido?', parent=root2)
                    if pergunta:
                        try:
                            cursor.execute('delete from pedidos where id =%s', (result2[0],))
                            db.commit()
                        except:
                            messagebox.showerror('Editar|Pedido:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                            return False
                        messagebox.showinfo('Editar|Pedido:', 'Pedido excluído com sucesso.', parent=root2)
                        root2.destroy()
                        atualizar_lista_principal()
                else:
                    messagebox.showwarning('Editar|Pedido:', 'Este pedido já está sendo atendido.', parent=root2)        
            
            def salvar():
                db.cmd_reset_connection()
                cursor.execute('select status_pedido from pedidos where id =%s', (result2[0],))
                if (cursor.fetchone()[0]) == 'Aberto':
                    pergunta = messagebox.askyesno('Editar|Pedido', 'Confirma a edição deste pedido?', parent=root2)
                    if pergunta:
                        cursor.execute('select id from refeicoes where refeicoes = %s', (opt_refeicoes.get(),))
                        refeicao = cursor.fetchone()[0]
                        cursor.execute('select id from centrocusto where nome_cc = %s', (ent_cc.get(),))
                        cc = cursor.fetchone()[0]
                        data = ent_data.get()
                        hora_pedido = ent_hora.get()
                        data_entrega = ent_dt_entrega.get()
                        refeicao_escolhida = refeicao
                        quantidade = ent_quant.get()
                        total = ent_total.get()
                        hora_entrega = clique_horario.get()
                        cc_escolhido = cc
                        mot = txt_mot.get("1.0", 'end-1c')
                        obs = txt_obs.get("1.0", 'end-1c')
                        #print(data, hora_pedido, data_entrega, refeicao_escolhida,quantidade, total, hora_entrega, cc_escolhido, mot, obs)

                        if data_entrega == '' or  refeicao_escolhida == '' or quantidade == '' or hora_entrega == '' or cc_escolhido == '' or mot == '' or total == '':
                            messagebox.showwarning('Editar|Pedido:', 'Todos os campos devem ser preenchidos.', parent=root2)
                        else:
                            try:
                                cursor.execute("UPDATE pedidos SET\
                                    data_pedido = %s,\
                                    id_cc = %s,\
                                    id_refeicao = %s,\
                                    quantidade = %s,\
                                    observacoes = %s,\
                                    data_entrega_prevista = %s,\
                                    hora = %s,\
                                    motivo = %s,\
                                    custo_total = %s,\
                                    hora_pedido = %s\
                                    WHERE id = %s", (data, cc_escolhido, refeicao_escolhida, quantidade, obs, data_entrega, hora_entrega, mot, total, hora_pedido, result2[0]))
                                db.commit()
                            except:
                                messagebox.showerror('Editar|Pedido:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                                return False
                            messagebox.showinfo('Editar|Pedido:', 'Pedido alterado com sucesso.', parent=root2)
                            global controla_loop
                            controla_loop = 0
                            root2.destroy()
                            atualizar_lista_principal()
                else:
                    messagebox.showwarning('Editar|Pedido:', 'Este pedido já está sendo atendido.', parent=root2)        

            def setup_sm():
                ent_data.insert(0, data)
                ent_data.configure(state='readonly')
                ent_hora.insert(0, hora)
                ent_hora.configure(state='readonly')
                ent_solicitante.insert(0,usuario_logado[1])
                ent_solicitante.configure(state='readonly')
                ent_area_solic.insert(0,usuario_logado[5])
                ent_area_solic.configure(state='readonly')
                ent_email.insert(0,usuario_logado[3])
                ent_email.configure(state='readonly')
                ent_dt_entrega.configure(state='readonly')
                ent_preco.configure(state='readonly')
                txt_descricao.configure(state='disabled')
                ent_total.configure(state='readonly')
                ent_desc_cc.configure(state='readonly')
                '''
                pedidos.id,\ 0
                pedidos.data_pedido,\ 1
                usuarios.nome,\2
                usuarios.email,\3
                ccUser.descricao_cc,\4
                ccPedido.descricao_cc,\5
                ccNumPedido.nome_cc,\6
                refeicoes.refeicoes,\7
                refeicoes.descricao,\8
                refeicoes.preco,\9
                pedidos.quantidade,\10
                pedidos.observacoes,\11
                pedidos.data_entrega_prevista,\12
                pedidos.atendente,\13
                pedidos.data_entrega_realizada,\14
                pedidos.status_pedido,\15
                pedidos.hora,\16
                pedidos.motivo,\17
                pedidos.custo_total,\18
                pedidos.hora_pedido\19
                '''
                ent_dt_entrega.configure(state='normal')
                ent_dt_entrega.insert(0,result2[12])
                ent_dt_entrega.configure(state='readonly')

                opt_refeicoes.set(result2[7])
                
                txt_descricao.configure(state='normal')
                txt_descricao.insert(END,result2[8])
                txt_descricao.configure(state='disabled')
                
                ent_preco.configure(state='normal')
                ent_preco.insert(0,result2[9])
                ent_preco.configure(state='readonly')

                ent_quant.insert(0,result2[10])

                ent_total.configure(state='normal')
                ent_total.insert(0,result2[18])
                ent_total.configure(state='readonly')

                opt_horario.set(result2[16])

                ent_cc.insert(0,result2[6])

                ent_desc_cc.configure(state='normal')
                ent_desc_cc.insert(0,result2[5])
                ent_desc_cc.configure(state='readonly')


                txt_mot.insert(END,result2[17])

                txt_obs.insert(END,result2[11])

            def calculo_total():
                valor = float(ent_preco.get())
                qtd = int(ent_quant.get())
                ent_total.configure(state='normal')
                ent_total.delete(0, END)
                ent_total.insert(0, f'{valor*qtd:.2f}')
                ent_total.configure(state='readonly')

            def opt_refeicoes_clique(event):       
                cursor.execute("SELECT * FROM refeicoes WHERE refeicoes=%s", (clique_refeicoes.get(),))
                result_clique = cursor.fetchone()
                global refeicoes
                refeicoes = result_clique[0]
                ent_preco.configure(state='normal')
                ent_preco.delete(0, END)
                ent_preco.insert(0, result_clique[3])
                ent_preco.configure(state='readonly')
                txt_descricao.configure(state='normal')
                txt_descricao.delete('1.0', END)
                txt_descricao.insert(END,result_clique[2])
                txt_descricao.configure(state='disabled')
                ent_quant.delete(0, END)
                ent_total.configure(state='normal')
                ent_total.delete(0, END)
                ent_total.configure(state='disabled')
                clique_horario.set('')

            def opt_horario_clique(event):
                if ent_dt_entrega.get() == '' or clique_refeicoes.get() == '':
                    messagebox.showinfo('+Novo Pedido:', 'Selecione a Data de Entrega e a Refeição.', parent=root2)
                    clique_horario.set('')

                else:
                    hora_selecionada = clique_horario.get()
                    data_escolhida = ent_dt_entrega.get()
                    hora_final = data_escolhida +' '+ hora_selecionada

                    tempo = timedelta()
                    time_1 = datetime.strptime(str(hora_calculo_pedido),"%d/%m/%Y %H:%M:%S")
                    time_2 = datetime.strptime(str(hora_final),"%d/%m/%Y %H:%M:%S")

                    tempo += time_2 - time_1
                    tempo_horas = round((tempo.total_seconds()/3600),2)

                    cursor.execute("SELECT * FROM refeicoes WHERE refeicoes=%s", (clique_refeicoes.get(),))
                    resultado = cursor.fetchone()[4]
                    if time_2 < time_1:
                        messagebox.showinfo('+Novo Pedido:', 'Horário inválido, escolha outro!', parent=root2)
                        clique_horario.set('')
                    elif tempo_horas < float(resultado):
                        messagebox.showinfo('+Novo Pedido:', f'Esta solicitação deve respeitar o tempo de preparo mínimo\nde {resultado} horas.', parent=root2)
                        clique_horario.set('')

            def verifica_preco(event):
                preco = ent_preco.get()
                if preco == '':
                    root2.focus_force()
                    messagebox.showinfo('+Novo Pedido:', 'Selecione a Refeição primeiramente.', parent=root2)

            def campo_quantidade(event):
                numero = ent_quant.get()
                if numero.isdigit() == False and numero != '':
                    messagebox.showinfo('+Novo Pedido:', 'Somente números inteiros são permitidos.', parent=root2)
                    ent_quant.focus_force()
                else:
                    if numero != '':
                        calculo_total()
                    else:
                        pass

            def calendario():
                root3 = Toplevel(root2)
                window_width = 360
                window_height = 258
                screen_width = root3.winfo_screenwidth()
                screen_height = root3.winfo_screenheight() - 70
                x_cordinate = int((screen_width / 2) - (window_width / 2))
                y_cordinate = int((screen_height / 2) - (window_height / 2))
                root3.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
                root3.resizable(0, 0)
                root3.configure(bg='#ffffff')
                root3.title(titulos)
                root3.overrideredirect(True)
                root3.focus_force()
                root3.grab_set()

                def escolher_data_bind(event):
                    escolher_data()
                def escolher_data():
                    ent_dt_entrega.configure(state='normal')
                    ent_dt_entrega.delete(0, END)
                    ent_dt_entrega.insert(0, cal.get_date())
                    ent_dt_entrega.configure(state='readonly')
                    clique_horario.set('')
                    root3.destroy()
                    root2.focus_force()
                    root2.grab_set()
                
                hoje = date.today()
                cal = Calendar(root3, font=fonte_padrao, selectmode='day', locale='pt_BR',
                        mindate=hoje, disabledforeground='red', cursor="hand1")
                
                cal.pack(fill="both", expand=True)
            
                root3.bind('<Double-1>',escolher_data_bind) # Escolhe a data ao clicar 2x com o mouse
                root3,mainloop()

            def verifica_cc(event):
                cc = ent_cc.get()
                if cc != '':
                    cc = ent_cc.get()
                    cursor.execute("SELECT * FROM centrocusto WHERE nome_cc = %s",(cc,))
                    centro = cursor.fetchone()
                    if centro != None:
                        ent_desc_cc.configure(state='normal')
                        ent_desc_cc.delete(0, END)
                        ent_desc_cc.insert(0, centro[2])
                        ent_desc_cc.configure(state='readonly')
                        global centro_custo
                        centro_custo = centro[0]
                    else:
                        messagebox.showinfo('+Novo Pedido:', 'Centro de Custo não encontrado.', parent=root2)
                        ent_cc.delete(0, END)
                        ent_desc_cc.configure(state='normal')
                        ent_desc_cc.delete(0, END)
                        ent_desc_cc.configure(state='readonly')
                        ent_cc.focus_force()

            #/////////////////////////SCROLLBAR
            def on_mousewheel(event):
                my_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

            def FrameWidth(event):
                canvas_width = event.width
                my_canvas.itemconfig(my_canvas_frame, width = canvas_width)

            def OnFrameConfigure(event):
                    my_canvas.configure(scrollregion=my_canvas.bbox("all"))

            frame = customtkinter.CTkFrame(root2, fg_color='#ffffff')
            frame.pack(fill = BOTH, expand = TRUE, padx = 0, pady = 0)

            my_canvas = customtkinter.CTkCanvas(frame, bg= '#ffffff')
            my_canvas.pack(side = LEFT, fill = BOTH, expand = TRUE)
            #my_canvas.bind_all("<MouseWheel>", on_mousewheel) // bind toda area do canvas
            my_canvas.bind("<MouseWheel>", on_mousewheel) # // bind somente a área do scrool

            mailbox_frame = customtkinter.CTkFrame(my_canvas, fg_color='#ffffff')

            my_canvas_frame = my_canvas.create_window((0,0), window=mailbox_frame, anchor = NW)
            #mailbox_frame.pack(side = LEFT, fill = BOTH, expand = True)

            mail_scroll = customtkinter.CTkScrollbar(my_canvas, orientation = "vertical", command = my_canvas.yview, scrollbar_color='#D3D3D3', scrollbar_hover_color='#C0C0C0', fg_color='#ffffff' )
            mail_scroll.pack(side = RIGHT, fill = Y)

            my_canvas.config(yscrollcommand = mail_scroll.set)

            mailbox_frame.bind("<Configure>", OnFrameConfigure)
            my_canvas.bind('<Configure>', FrameWidth)

            #///////////////////////// LAYOUT
            frame0 = customtkinter.CTkFrame(mailbox_frame, corner_radius=10, fg_color='#ffffff', border_width=4, border_color='#2a2d2e')
            frame0.pack(padx=20, pady=10, fill="both", expand=True)

            frame1 = Frame(frame0, bg='#ffffff')
            frame1.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame2 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame2.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
            frame3 = Frame(frame0, bg='#ffffff')
            frame3.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame4 = Frame(frame0, bg='#ffffff')
            frame4.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame5 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame5.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
            frame6 = Frame(frame0, bg='#ffffff')
            frame6.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame7 = Frame(frame0, bg='#ffffff')
            frame7.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame8 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame8.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame9 = Frame(frame0, bg='#ffffff')
            frame9.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame10 = Frame(frame0, bg='#2a2d2e') #/// LINHA
            frame10.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
            frame11 = Frame(frame0, bg='#ffffff')
            frame11.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)


            lbl_titulo = Label(frame1, text=f'Editar Pedido: {result2[0]}', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#1d366c')
            lbl_titulo.grid(row=0, column=1)
            frame1.grid_columnconfigure(0, weight=1)
            frame1.grid_columnconfigure(2, weight=1)

            #/////////FRAME2 LINHA HORIZONTAL
            
            #/////////FRAME3
            lbl2=Label(frame3, text='Data:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl2.grid(row=0, column=1, sticky="w", padx=3)
            ent_data = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=170)
            ent_data.grid(row=1, column=1, padx=3)

            lbl1=Label(frame3, text='Hora:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=0, column=2, sticky="w", padx=3)
            ent_hora = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=170)
            ent_hora.grid(row=1, column=2, padx=3)

            lbl1=Label(frame3, text='Solicitante:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=0, column=3, sticky="w", padx=3)
            ent_solicitante = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=340)
            ent_solicitante.grid(row=1, column=3, padx=3)

            frame3.grid_columnconfigure(0, weight=1)
            frame3.grid_columnconfigure(4, weight=1)

            #/////////FRAME4
            lbl1=Label(frame4, text='Área do Solicitante:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=2, column=1, sticky="w", padx=5)
            ent_area_solic = customtkinter.CTkEntry(frame4, **estilo_entry_padrao, width=340)
            ent_area_solic.grid(row=3, column=1, padx=5)

            lbl1=Label(frame4, text='E-mail:', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl1.grid(row=2, column=2, sticky="w", padx=5)
            ent_email = customtkinter.CTkEntry(frame4, **estilo_entry_padrao, width=340)
            ent_email.grid(row=3, column=2, padx=5)

            frame4.grid_columnconfigure(0, weight=1)
            frame4.grid_columnconfigure(4, weight=1)

            #/////////FRAME5 LINHA HORIZONTAL

            #/////////FRAME6
            img_logo = Image.open('img\\calendario.png')
            resize_logo = img_logo.resize((26, 26))
            nova_img_logo = ImageTk.PhotoImage(resize_logo)

            lbl=Button(frame6, text='Data de Entrega: ', image=nova_img_logo, compound=RIGHT, font=fonte_padrao_bold, fg='#880000',borderwidth=0, relief=RIDGE, bg=cor_branca, activebackground=cor_branca, cursor="hand2", command=calendario)
            lbl.grid(row=0, column=1, sticky="w", padx=6)
            
            ent_dt_entrega = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=180)
            ent_dt_entrega.grid(row=1, column=1, sticky="w", padx=6)

            clique_refeicoes = StringVar()
            lista_refeicoes = []
            cursor.execute("SELECT * FROM refeicoes LIMIT 0,1")
            result = cursor.fetchone()
            if result == None:
                lista_refeicoes.append('')
            else:
                cursor.execute("SELECT * FROM refeicoes ORDER BY refeicoes")
                for i in cursor:
                    lista_refeicoes.append(i[1])
            
            lbl=Label(frame6, text='Refeição: ', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
            lbl.grid(row=2, column=1, sticky="w", padx=6)
            opt_refeicoes = ttk.Combobox(frame6, textvariable=clique_refeicoes, values=lista_refeicoes, width=32, height=20, font=fonte_padrao, state='readonly')
            opt_refeicoes.grid(row=3, column=1)
            opt_refeicoes.bind("<<ComboboxSelected>>", opt_refeicoes_clique)

            lbl=Label(frame6, text='Preço(R$):', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=2, column=2, sticky="w")
            ent_preco = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=110, textvariable=campo_quantidade)
            ent_preco.grid(row=3, column=2, sticky="w")

            lbl=Label(frame6, text='Quantidade:', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
            lbl.grid(row=2, column=3, sticky="w")
            ent_quant = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=110, textvariable=campo_quantidade)
            ent_quant.grid(row=3, column=3, sticky="w")
            ent_quant.bind("<FocusIn>", verifica_preco)
            ent_quant.bind("<FocusOut>", campo_quantidade)
            
            lbl=Label(frame6, text='Total(R$):', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=2, column=4, sticky="w")
            ent_total = customtkinter.CTkEntry(frame6, **estilo_entry_padrao, width=110, textvariable=campo_quantidade)
            ent_total.grid(row=3, column=4, sticky="w")

            lbl=Label(frame6, text='Detalhes: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=4, column=1, sticky="w", padx=6)
            txt_descricao = scrolledtext.ScrolledText(frame6, **estilo_scrolledtext_padrão, width=82, height=2)
            txt_descricao.grid(row=5, column=1, columnspan=4, padx=6)

            frame6.grid_columnconfigure(0, weight=1)
            frame6.grid_columnconfigure(6, weight=1)

            #/////////FRAME7
            clique_horario = StringVar()
            lista_horario = [
                '00:00:00',
                '00:30:00',
                '01:00:00',
                '01:30:00',
                '02:00:00',
                '02:30:00',
                '03:00:00',
                '03:30:00',
                '04:00:00',
                '04:30:00',
                '05:00:00',
                '05:30:00',
                '06:00:00',
                '06:30:00',
                '07:00:00',
                '07:30:00',
                '08:00:00',
                '08:30:00',
                '09:00:00',
                '09:30:00',
                '10:00:00',
                '10:30:00',
                '11:00:00',
                '11:30:00',
                '12:00:00',
                '12:30:00',
                '13:00:00',
                '13:30:00',
                '14:00:00',
                '14:30:00',
                '15:00:00',
                '15:30:00',
                '16:00:00',
                '16:30:00',
                '17:00:00',
                '17:30:00',
                '18:00:00',
                '18:30:00',
                '19:00:00',
                '19:30:00',
                '20:00:00',
                '20:30:00',
                '21:00:00',
                '21:30:00',
                '22:00:00',
                '22:30:00',
                '23:00:00',
                '23:30:00']
            

            lbl=Label(frame7, text='Horário para Entrega: ', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
            lbl.grid(row=2, column=1, sticky="w")
            opt_horario = ttk.Combobox(frame7, textvariable=clique_horario, values=lista_horario, width=22, state='readonly')
            opt_horario.grid(row=3, column=1, sticky="w")
            opt_horario.bind("<<ComboboxSelected>>", opt_horario_clique)
            
            lbl=Label(frame7, text='Centro de Custo:', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
            lbl.grid(row=2, column=2, sticky="w", padx=12)
            ent_cc = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=170, textvariable=campo_quantidade)
            ent_cc.grid(row=3, column=2, sticky="w", padx=12)
            ent_cc.bind("<FocusOut>", verifica_cc)   
            
            lbl=Label(frame7, text='Descrição|Centro de Custo: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=2, column=3, sticky="w")
            ent_desc_cc = customtkinter.CTkEntry(frame7, **estilo_entry_padrao, width=320, textvariable=campo_quantidade)
            ent_desc_cc.grid(row=3, column=3, sticky="w")

            frame7.grid_columnconfigure(0, weight=1)
            frame7.grid_columnconfigure(4, weight=1)

            
            #/////////FRAME8 LINHA HORIZONTAL

            #/////////FRAME9
            lbl=Label(frame9, text='Motivo:', font=fonte_padrao_bold, bg='#ffffff', fg='#880000')
            lbl.grid(row=0, column=1, sticky="w")
            txt_mot = scrolledtext.ScrolledText(frame9, **estilo_scrolledtext_padrão, width=82, height=2)
            txt_mot.grid(row=1, column=1)
            
            lbl=Label(frame9, text='Observações: ', font=fonte_padrao, bg='#ffffff', fg='#000000')
            lbl.grid(row=2, column=1, sticky="w")
            txt_obs = scrolledtext.ScrolledText(frame9, **estilo_scrolledtext_padrão, width=82, height=2)
            txt_obs.grid(row=3, column=1)

            frame9.grid_columnconfigure(0, weight=1)
            frame9.grid_columnconfigure(3, weight=1)

            #/////////FRAME10 LINHA HORIZONTAL

            #/////////FRAME11
            bt1 = customtkinter.CTkButton(frame11, text='Confirmar|Edição', **estilo_botao_padrao_form, command=salvar)
            bt1.grid(row=0, column=1, pady=2, padx=30)
            
            bt2 = customtkinter.CTkButton(frame11, text='Excluir', **estilo_botao_excluir, command=excluir, )
            bt2.grid(row=0, column=2, pady=2, padx=30)

            frame11.grid_columnconfigure(0, weight=1)
            frame11.grid_columnconfigure(3, weight=1)

            '''root2.update()
            largura = root2.winfo_width()
            altura = root2.winfo_height()
            print(largura, altura)'''

            setup_sm()
            root2.wm_protocol("WM_DELETE_WINDOW", lambda: [ativa_loop(0), atualizar_lista_principal(), root2.destroy()])
            root2.mainloop()

def imprimir_pedido():
    lista_select = tree_principal.focus()
    if lista_select == "":
        messagebox.showwarning('Atendimento:', 'Selecione um pedido.', parent=root)
    else:
        valor_lista = tree_principal.item(lista_select, "values")[0]
        try:
            cursor.execute("select \
            pedidos.id,\
            pedidos.data_pedido,\
            usuarios.nome,\
            usuarios.email,\
            ccUser.descricao_cc,\
            ccPedido.descricao_cc,\
            ccNumPedido.nome_cc,\
            refeicoes.refeicoes,\
            pedidos.quantidade,\
            pedidos.custo_total,\
            pedidos.motivo,\
            pedidos.observacoes,\
            pedidos.data_entrega_prevista,\
            pedidos.hora,\
			pedidos.atendente,\
            pedidos.data_entrega_realizada,\
            pedidos.status_pedido,\
            pedidos.hora_pedido\
            from pedidos\
            inner join usuarios on pedidos.id_solicitante = usuarios.id\
            inner join centrocusto ccUser on usuarios.id_cc = ccUser.id\
            inner join centrocusto ccPedido on pedidos.id_cc = ccPedido.id\
            inner join centrocusto ccNumPedido on pedidos.id_cc = ccNumPedido.id\
            inner join refeicoes on pedidos.id_refeicao = refeicoes.id\
            WHERE pedidos.id = %s ORDER BY pedidos.id DESC",(valor_lista,))
            result2 = cursor.fetchone()
        except:
            messagebox.showerror('Atendimento:', 'Erro de conexão com o Banco de Dados.', parent=root)
            return False
        
        if result2[16] != 'Aberto':
            messagebox.showerror('Atendimento:', 'Este pedido já está sendo verificado ou encontra-se "Encerrado" ou "Cancelado".\
            \nNão há necessidade de imprimi-lo.', parent=root)

        else:
            pdfmetrics.registerFont(TTFont('Calibri Bold', 'Calibrib.ttf'))
            pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))
            
            c = canvas.Canvas("img\\temp.pdf", pagesize=A4)
            width, height = A4

            c.rect(10, 10, width-20, height-20, stroke=1, fill=0)

            c.rect(198.42, 740, 198.42, 92, stroke=1, fill=0)

            c.drawImage('img\\logo.jpg',40,746, width=120,height=80,mask=None)

            c.setFont("Calibri Bold",18, leading = None)
            c.drawString(234.93, 788, 'SIMEC REFEIÇÃO')

            c.setFont("Calibri Bold",16, leading = None)
            c.drawString(444.93, 790, 'Nº do Pedido')
            c.drawString(464.93, 775, '{:0>5}'.format(result2[0]))
            c.setFont("Calibri Bold",12, leading = None)
            c.drawString(443.93, 745, f'Hora: {result2[17]}')
            c.drawString(443.93, 760, f'Data: {result2[1]}')
            c.line(10, 740, 585.27, 740)

            c.line(10, 668, 585.27, 668)

            c.drawString(20, 720, f'Solicitante: {result2[2]}')
            c.drawString(20, 700, f'E-mail: {result2[3]}')
            c.drawString(20, 680, f'Área do Solicitante: {result2[4]}')


            c.drawString(20, 650, f'Área da Solicitação: {result2[5]}')
            c.drawString(20, 630, f'Centro de Custo: {result2[6]}')
            c.drawString(20, 610, f'Refeição: {result2[7]}')
            c.drawString(20, 590, f'Quantidade: {result2[8]}')
            c.drawString(20, 570, f'Data|Entrega: {result2[12]}')
            c.drawString(20, 550, f'Hora|Entrega: {result2[13]}')

            c.line(10, 530, 585.27, 530)

            c.drawString(20, 510, 'Motivo:')
            text_mot = c.beginText(20,498)
            text_mot.textLines(f'{result2[10]}')
            c.drawText(text_mot)

            c.line(10, 430, 585.27, 430)

            c.drawString(20, 410, 'Observações:')
            text_obs = c.beginText(20, 398)
            text_obs.textLines(f'{result2[11]}')
            c.drawText(text_obs)
            
            c.line(10, 320, 585.27, 320)


            c.line(30, 130, 160, 130)
            c.setFont("Calibri Bold",10, leading = None)
            c.drawString(50, 120, f'{result2[2]}')


            c.showPage()
            try:
                c.save()
            except:
                messagebox.showerror('Imprimir Pedido:', 'Acesso negado.\nPossivelmente o arquivo PDF está aberto em outra aplicação.', parent=root)

            os.startfile('img\\temp.pdf', 'open')

def configuracao():
    ativa_loop(1)
    root2 = Toplevel(root)
    root2.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    root2.unbind_class("Button", "<Key-space>")
    root2.focus_force()
    root2.grab_set()

    def cadastro_usuarios():
        
        def atualizar_lista_usuarios():
            db.cmd_reset_connection()
            tree_configuracao.delete(*tree_configuracao.get_children())
            cursor.execute("SELECT\
            usuarios.id,\
            usuarios.nome,\
            usuarios.email,\
            centrocusto.descricao_cc\
            FROM usuarios\
            inner join centrocusto on usuarios.id_cc = centrocusto.id\
            ORDER BY usuarios.nome")
            cont = 0
            for row in cursor:
                if cont % 2 == 0:
                    tree_configuracao.insert('', 'end', text=" ",
                                            values=(
                                            row[0], row[1], row[2], row[3]),
                                            tags=('par',))
                else:
                    tree_configuracao.insert('', 'end', text=" ",
                                            values=(
                                            row[0], row[1], row[2], row[3]),
                                            tags=('impar',))
                cont += 1

        def salvar():
            nome = ent_nome.get().upper()
            usuario = ent_user.get()
            email = ent_email.get().upper()
            senha = ent_senha.get()
            cc_escolhido = ent_cc.get()
            gestor = chk_var2.get()
            refeitorio = chk_var1.get()

            if nome == '' or usuario == '' or email == ''or senha == ''or cc_escolhido == '':
                messagebox.showwarning('Cadastro de Usuários:', 'Todos os campos devem ser preenchidos.', parent=root2)
            else:
                cursor.execute("SELECT * FROM centrocusto WHERE nome_cc=%s", (cc_escolhido,))
                verifica_cc = cursor.fetchone()
                id_cc = verifica_cc[0]
                
                cursor.execute("SELECT * FROM usuarios WHERE usuario=%s", (usuario,))
                verifica_usuario = cursor.fetchone()
                
                if verifica_usuario == None:
                    try:
                        cursor.execute(
                            "INSERT INTO usuarios (nome, usuario, email, senha, id_cc, gestor, refeitorio) values(%s,%s,%s,%s,%s,%s,%s)", (nome,usuario,email,senha,id_cc,gestor,refeitorio,))
                        db.commit()
                    except:
                        messagebox.showerror('Cadastro de Usuários:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False

                    messagebox.showinfo('Cadastro de Usuários:', 'Cadastro efetuado com sucesso.', parent=root2)
                    cancelar()
                else:
                    messagebox.showerror('Cadastro de Usuários', 'Usuário já cadastrado:', parent=root2)
        
        def cancelar():
            ent_nome.focus_force()
            ent_nome.delete(0, END)
            ent_user.delete(0, END)
            ent_email.delete(0, END)
            ent_senha.delete(0, END)
            ent_cc.delete(0, END)
            ent_desc_cc.configure(state='normal')
            ent_desc_cc.delete(0, END)
            ent_desc_cc.configure(state='readonly')
            chk_var1.set(0)
            chk_var2.set(0)

            bt_salvar = customtkinter.CTkButton(fr6, text='Salvar', **estilo_botao_padrao_form, command=salvar)
            bt_salvar.grid(row=0, column=1, padx=5)
            bt_editar = customtkinter.CTkButton(fr6, text='Editar', **estilo_botao_padrao_form, command=editar)
            bt_editar.grid(row=0, column=2, padx=5)
            atualizar_lista_usuarios()
            
        def editar():
            def setup_interno():
                ent_nome.insert(0, result2[1])
                ent_user.insert(0, result2[2])
                ent_email.insert(0,result2[3])
                ent_cc.insert(0,result2[4])
                if result2[6] == '1':
                    chk_var1.set(1)
                if result2[5] == '1':
                    chk_var2.set(1)

            def confirmar():
                nome = ent_nome.get().upper()
                usuario = ent_user.get()
                email = ent_email.get().upper()
                senha = ent_senha.get()
                cc_escolhido = ent_cc.get()
                gestor = chk_var2.get()
                refeitorio = chk_var1.get()

                if nome == '' or usuario == '' or email == ''or senha == ''or cc_escolhido == '':
                    messagebox.showwarning('Editar Usuário:', 'Todos os campos devem ser preenchidos.', parent=root2)
                else:
                    cursor.execute("SELECT * FROM centrocusto WHERE nome_cc=%s", (cc_escolhido,))
                    verifica_cc = cursor.fetchone()
                    id_cc = verifica_cc[0]
                    try:
                        cursor.execute(
                            "UPDATE usuarios SET\
                            nome = %s,\
                            usuario = %s,\
                            email = %s,\
                            senha = %s,\
                            id_cc = %s,\
                            gestor = %s,\
                            refeitorio = %s\
                            WHERE id = %s", (nome,usuario,email,senha,id_cc,gestor,refeitorio,result2[0],))
                        db.commit()
                    except:
                        messagebox.showerror('Editar Usuário:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False

                    messagebox.showinfo('Editar Usuário:', 'Edição realizada com sucesso.', parent=root2)
                    cancelar()
                    atualizar_lista_usuarios()
            
            lista_select = tree_configuracao.focus()
            if lista_select == "":
                messagebox.showwarning('Configurações | Usuário:', 'Selecione um usuário na lista!', parent=root2)
            else:
                valor_lista = tree_configuracao.item(lista_select, "values")[0]
                try:
                    cursor.execute("SELECT\
                    usuarios.id,\
                    usuarios.nome,\
                    usuarios.usuario,\
                    usuarios.email,\
                    centrocusto.nome_cc,\
                    usuarios.gestor,\
                    usuarios.refeitorio\
                    FROM usuarios\
                    inner join centrocusto on usuarios.id_cc = centrocusto.id\
                    WHERE usuarios.id = %s\
                    ORDER BY usuarios.nome",(valor_lista,))
                    result2 = cursor.fetchone()
                    #print(result2)
                except:
                    messagebox.showerror('Configurações | Usuário:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                    return False
                bt_salvar.grid_remove()
                bt_editar.grid_remove()
                bt_confirmar = customtkinter.CTkButton(fr6, text='Confirmar', **estilo_botao_padrao_form, command=confirmar)
                bt_confirmar.grid(row=0, column=1, padx=5)
                bt_cancelar = customtkinter.CTkButton(fr6, text='Cancelar', **estilo_botao_padrao_form, command=cancelar)
                bt_cancelar.grid(row=0, column=2, padx=5)
                setup_interno()
        
        def verifica_cc(event):
                cc = ent_cc.get()
                if cc != '':
                    cc = ent_cc.get()
                    cursor.execute("SELECT * FROM centrocusto WHERE nome_cc = %s",(cc,))
                    centro = cursor.fetchone()
                    if centro != None:
                        ent_desc_cc.configure(state='normal')
                        ent_desc_cc.delete(0, END)
                        ent_desc_cc.insert(0, centro[2])
                        ent_desc_cc.configure(state='readonly')
                    else:
                        messagebox.showinfo('+Novo Pedido:', 'Centro de Custo não encontrado.', parent=root2)
                        ent_cc.delete(0, END)
                        ent_desc_cc.configure(state='normal')
                        ent_desc_cc.delete(0, END)
                        ent_desc_cc.configure(state='readonly')
                        ent_cc.focus_force()

        #/////////APAGA O CONTEUDO DO FRAME5
        for widget in frame5.winfo_children():
            widget.destroy()
        #/////////ESTRUTURA DO LAYOUT
        fr0 = Frame(frame5, bg='#ffffff')
        fr0.pack(side=TOP, fill=BOTH, expand=True)
        fr1 = Frame(fr0, bg='#ffffff')
        fr1.pack(side=TOP, fill=X)
        fr2 = Frame(fr0, bg='#ffffff')
        fr2.pack(side=TOP, fill=X)
        fr3 = Frame(fr0, bg='#ffffff')
        fr3.pack(side=TOP, fill=X)
        fr4 = Frame(fr0, bg='#2a2d2e') #/// LINHA
        fr4.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
        fr5 = Frame(fr0, bg='#ffffff')
        fr5.pack(side=TOP, fill=BOTH, expand=True)
        fr6 = Frame(fr0, bg='#ffffff')
        fr6.pack(side=TOP, fill=X, pady=6)
        
        #/////////FRAME1
        lbl_titulo = Label(fr1, text='Cadastro de Usuários', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#2a2d2e')
        lbl_titulo.grid(row=0, column=1, columnspan=2)
        
        lbl_nome=Label(fr1, text='Nome:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl_nome.grid(row=1, column=1, sticky="w")
        ent_nome = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_nome.grid(row=1, column=2, pady=3)        
        ent_nome.focus_force()
        
        lbl_user=Label(fr1, text='Usuário:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl_user.grid(row=2, column=1, sticky="w")
        ent_user = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_user.grid(row=2, column=2, pady=3)        

        lbl_email=Label(fr1, text='E-mail:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl_email.grid(row=3, column=1, sticky="w")
        ent_email = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_email.grid(row=3, column=2, pady=3)        

        lbl_senha=Label(fr1, text='Senha:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl_senha.grid(row=4, column=1, sticky="w")
        ent_senha = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_senha.grid(row=4, column=2, pady=3)        
        
        fr1.grid_columnconfigure(0, weight=1)
        fr1.grid_columnconfigure(3, weight=1)

        #/////////FRAME2
        lbl=Label(fr1, text='C.Custo:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl.grid(row=5, column=1, sticky="w")
        ent_cc = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_cc.grid(row=5, column=2, pady=3)
        ent_cc.bind("<FocusOut>", verifica_cc)   

        lbl=Label(fr1, text='Desc. :', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl.grid(row=6, column=1, sticky="w")
        ent_desc_cc = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_desc_cc.grid(row=6, column=2, pady=3)
        ent_desc_cc.configure(state='readonly')
        def teste():
            print(lbl_nome.cget("text"))

        #/////////FRAME3
        chk_var1 = IntVar()
        chk_var2 = IntVar()
        chk_1 = customtkinter.CTkCheckBox(fr3, text='Funcionário do Refeitório?', variable=chk_var1, onvalue=1, offvalue=0, text_font=fonte_padrao, bg_color='#ffffff', fg_color='#2a2d2e', hover_color='#2a2d2e', text_color='#2a2d2e', border_color='#2a2d2e')
        chk_1.grid(row=4, column=1, padx=6)
        chk_2 = customtkinter.CTkCheckBox(fr3, text='Gestor\Líder?', variable=chk_var2, onvalue=1, offvalue=0, text_font=fonte_padrao, bg_color='#ffffff', fg_color='#2a2d2e', hover_color='#2a2d2e', text_color='#2a2d2e', border_color='#2a2d2e', command=teste)
        chk_2.grid(row=4, column=2, padx=6)
        
        fr3.grid_columnconfigure(0, weight=1)
        fr3.grid_columnconfigure(3, weight=1)

        #/////////FRAME4 LINHA

        #/////////FRAME5
        tree_configuracao = ttk.Style()
        #style.theme_use('default')
        style.configure('Treeview',
                        background='#ffffff',
                        rowheight=24,
                        fieldbackground='#ffffff',
                        font=fonte_padrao)
        style.configure("Treeview.Heading",
                        foreground='#1d366c',
                        background="#ffffff",
                        height=200,
                        font=fonte_padrao_bold)
        style.map('Treeview', background=[('selected', cor_cinza)])

        tree_configuracao = ttk.Treeview(fr5, selectmode='browse')
        vsb = ttk.Scrollbar(fr5, orient="vertical", command=tree_configuracao.yview)
        vsb.pack(side=RIGHT, fill='y')
        tree_configuracao.configure(yscrollcommand=vsb.set)
        vsbx = ttk.Scrollbar(fr5, orient="horizontal", command=tree_configuracao.xview)
        vsbx.pack(side=BOTTOM, fill='x')
        tree_configuracao.configure(xscrollcommand=vsbx.set)
        tree_configuracao.pack(side=LEFT, fill=BOTH, expand=True, anchor='n')
        tree_configuracao["columns"] = ("1", "2", "3", "4")
        tree_configuracao['show'] = 'headings'
        tree_configuracao.column("1", anchor='c', width=80)
        tree_configuracao.column("2", anchor='c')
        tree_configuracao.column("3", anchor='c')
        tree_configuracao.column("4", anchor='c')
        tree_configuracao.heading("1", text="ID Usuário")
        tree_configuracao.heading("2", text="Nome")
        tree_configuracao.heading("3", text="E-mail")
        tree_configuracao.heading("4", text="Área")
        tree_configuracao.tag_configure('par', background='#e9e9e9')
        tree_configuracao.tag_configure('impar', background='#ffffff')
        #tree_configuracao.bind("<Double-1>", duploclique_tree_configuracao)
        frame4.grid_columnconfigure(0, weight=1)
        frame4.grid_columnconfigure(3, weight=1)

        #/////////FRAME6
        bt_salvar = customtkinter.CTkButton(fr6, text='Salvar', **estilo_botao_padrao_form, command=salvar)
        bt_salvar.grid(row=0, column=1, padx=5)
        bt_editar = customtkinter.CTkButton(fr6, text='Editar', **estilo_botao_padrao_form, command=editar)
        bt_editar.grid(row=0, column=2, padx=5)

        fr6.grid_columnconfigure(0, weight=1)
        fr6.grid_columnconfigure(3, weight=1)

        atualizar_lista_usuarios()

    def cadastro_centrocusto():
        def atualizar_lista_cc():
            db.cmd_reset_connection()
            tree_configuracao.delete(*tree_configuracao.get_children())
            cursor.execute("SELECT * FROM centrocusto ORDER BY nome_cc")
            cont = 0
            for row in cursor:
                if cont % 2 == 0:
                    tree_configuracao.insert('', 'end', text=" ",
                                            values=(
                                            row[0], row[1], row[2]),
                                            tags=('par',))
                else:
                    tree_configuracao.insert('', 'end', text=" ",
                                            values=(
                                            row[0], row[1], row[2]),
                                            tags=('impar',))
                cont += 1

        def salvar():
            cc = ent_cc.get().upper()
            desc_cc = ent_desc_cc.get().upper()
            if cc == '' or desc_cc == '':
                messagebox.showwarning('Cadastro de Centro de Custo:', 'Todos os campos devem ser preenchidos.', parent=root2)
            else:
                cursor.execute("SELECT * FROM centrocusto WHERE nome_cc=%s", (cc,))
                verifica = cursor.fetchone()
                if verifica == None:
                    try:
                        cursor.execute(
                            "INSERT INTO centrocusto (nome_cc, descricao_cc) values(%s, %s)", (cc,desc_cc,))
                        db.commit()
                    except:
                        messagebox.showerror('Cadastro de Centro de Custo:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False

                    messagebox.showinfo('Cadastro de Centro de Custo:', 'Cadastro efetuado com sucesso.', parent=root2)
                    cadastro_centrocusto()
                else:
                    messagebox.showerror('Cadastro de Centro de Custo', 'Centro de Custo já cadastrado:', parent=root2)
        
        def cancelar_cc():
            ent_cc.focus_force()
            ent_cc.delete(0, END)
            ent_desc_cc.delete(0, END)
            bt_salvar = customtkinter.CTkButton(fr4, text='Salvar', **estilo_botao_padrao_form, command=salvar)
            bt_salvar.grid(row=0, column=1, padx=5)
            bt_editar = customtkinter.CTkButton(fr4, text='Editar', **estilo_botao_padrao_form, command=editar)
            bt_editar.grid(row=0, column=2, padx=5)
            atualizar_lista_cc()
       
        def editar():
            def setup_interno():
                ent_cc.insert(0, result2[1])
                ent_desc_cc.insert(0, result2[2])

            def confirmar_cc():
                cc = ent_cc.get().upper()
                desc_cc = ent_desc_cc.get().upper()

                if ent_cc == '' :
                    messagebox.showwarning('Editar Centro de Custo:', 'Todos os campos devem ser preenchidos.', parent=root2)
                else:
                    try:
                        cursor.execute(
                            "UPDATE centrocusto SET\
                            nome_cc = %s,\
                            descricao_cc = %s\
                            WHERE id = %s", (cc,desc_cc,result2[0],))
                        db.commit()
                    except:
                        messagebox.showerror('Editar Centro de Custo:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False
                    messagebox.showinfo('Editar Centro de Custo:', 'Edição realizada com sucesso.', parent=root2)
                    cancelar_cc()
                    atualizar_lista_cc()

            lista_select = tree_configuracao.focus()
            if lista_select == "":
                messagebox.showwarning('Configurações | Centro de Custo:', 'Selecione um centro de custo na lista!', parent=root2)
            else:
                valor_lista = tree_configuracao.item(lista_select, "values")[0]
                try:
                    cursor.execute("SELECT * FROM centrocusto WHERE id= %s;",(valor_lista,))
                    result2 = cursor.fetchone()
                    #print(result2)
                except:
                    messagebox.showerror('Configurações | Centro de Custo:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                    return False
                bt_salvar.grid_remove()
                bt_editar.grid_remove()
                bt_confirmar = customtkinter.CTkButton(fr4, text='Confirmar', **estilo_botao_padrao_form, command=confirmar_cc)
                bt_confirmar.grid(row=0, column=1, padx=5)
                bt_cancelar = customtkinter.CTkButton(fr4, text='Cancelar', **estilo_botao_padrao_form, command=cancelar_cc)
                bt_cancelar.grid(row=0, column=2, padx=5)
                setup_interno()

        for widget in frame5.winfo_children():
            widget.destroy()

        fr0 = Frame(frame5, bg='#ffffff')
        fr0.pack(side=TOP, fill=BOTH, expand=True)
        
        fr1 = Frame(fr0, bg='#ffffff')
        fr1.pack(side=TOP, fill=X)
        fr2 = Frame(fr0, bg='#2a2d2e') #/// LINHA
        fr2.pack(padx=10, pady=10, fill="x", expand=False, side=TOP)
        fr3 = Frame(fr0, bg='#ffffff')
        fr3.pack(side=TOP, fill=BOTH, expand=True, pady=6)
        fr4 = Frame(fr0, bg='#ffffff')
        fr4.pack(side=TOP, fill=X, pady=6)
        
        #/////////FRAME1
        lbl_titulo = Label(fr1, text='Cadastro de Centro de Custo', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#2a2d2e')
        lbl_titulo.grid(row=0, column=1, columnspan=2)
        
        lbl1=Label(fr1, text='Centro de Custo:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl1.grid(row=1, column=1, sticky="w")
        ent_cc = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_cc.grid(row=1, column=2, pady=10)        
        ent_cc.focus_force()

        lbl1=Label(fr1, text='Desc. Centro de Custo:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl1.grid(row=2, column=1, sticky="w")
        ent_desc_cc = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_desc_cc.grid(row=2, column=2, pady=10, sticky="w")        

        fr1.grid_columnconfigure(0, weight=1)
        fr1.grid_columnconfigure(3, weight=1)
        #/////////FRAME2 LINHA
        
        #/////////FRAME3
        tree_configuracao = ttk.Style()
        #style.theme_use('default')
        style.configure('Treeview',
                        background='#ffffff',
                        rowheight=24,
                        fieldbackground='#ffffff',
                        font=fonte_padrao)
        style.configure("Treeview.Heading",
                        foreground='#1d366c',
                        background="#ffffff",
                        font=fonte_padrao_bold)
        style.map('Treeview', background=[('selected', cor_cinza)])

        tree_configuracao = ttk.Treeview(fr3, selectmode='browse')
        vsb = ttk.Scrollbar(fr3, orient="vertical", command=tree_configuracao.yview)
        vsb.pack(side=RIGHT, fill='y')
        tree_configuracao.configure(yscrollcommand=vsb.set)
        vsbx = ttk.Scrollbar(fr3, orient="horizontal", command=tree_configuracao.xview)
        vsbx.pack(side=BOTTOM, fill='x')
        tree_configuracao.configure(xscrollcommand=vsbx.set)
        tree_configuracao.pack(side=LEFT, fill=BOTH, expand=True, anchor='n')
        tree_configuracao["columns"] = ("1", "2", "3")
        tree_configuracao['show'] = 'headings'
        tree_configuracao.column("1", anchor='c', width=80)
        tree_configuracao.column("2", anchor='c')
        tree_configuracao.column("3", anchor='c')
        tree_configuracao.heading("1", text="ID Centro de Custo")
        tree_configuracao.heading("2", text="Centro de Custo")
        tree_configuracao.heading("3", text="Desc. Centro de Custo")

        tree_configuracao.tag_configure('par', background='#e9e9e9')
        tree_configuracao.tag_configure('impar', background='#ffffff')
        #tree_configuracao.bind("<Double-1>", duploclique_tree_configuracao)

        #/////////FRAME4
        bt_salvar = customtkinter.CTkButton(fr4, text='Salvar', **estilo_botao_padrao_form, command=salvar)
        bt_salvar.grid(row=0, column=1, padx=5)
        bt_editar = customtkinter.CTkButton(fr4, text='Editar', **estilo_botao_padrao_form, command=editar)
        bt_editar.grid(row=0, column=2, padx=5)
        fr4.grid_columnconfigure(0, weight=1)
        fr4.grid_columnconfigure(3, weight=1)

        atualizar_lista_cc()
    
    def cadastro_refeicoes():
        def atualizar_lista_refeicoes():
            db.cmd_reset_connection()
            tree_configuracao.delete(*tree_configuracao.get_children())
            cursor.execute("SELECT * FROM refeicoes ORDER BY refeicoes")
            cont = 0
            for row in cursor:
                if cont % 2 == 0:
                    tree_configuracao.insert('', 'end', text=" ",
                                            values=(
                                            row[0], row[1], row[2], row[4], row[3]),
                                            tags=('par',))
                else:
                    tree_configuracao.insert('', 'end', text=" ",
                                            values=(
                                            row[0], row[1], row[2], row[4], row[3]),
                                            tags=('impar',))
                cont += 1

        def cancelar_refeicoes():
            ent_refeicao.focus_force()
            ent_refeicao.delete(0, END)
            txt_descricao.delete('1.0', END)
            ent_preco.delete(0, END)
            ent_prep.delete(0, END)
            bt_salvar = customtkinter.CTkButton(fr4, text='Salvar', **estilo_botao_padrao_form, command=salvar)
            bt_salvar.grid(row=0, column=1, padx=5)
            bt_editar = customtkinter.CTkButton(fr4, text='Editar', **estilo_botao_padrao_form, command=editar)
            bt_editar.grid(row=0, column=2, padx=5)
            atualizar_lista_refeicoes()
       
        def editar():
            def setup_interno():
                ent_refeicao.insert(0, result2[1])
                txt_descricao.insert(END,result2[2])
                ent_preco.insert(0, result2[3])
                ent_prep.insert(0, result2[4])

            def confirmar_refeicoes():
                refeicao = ent_refeicao.get().upper()
                descricao = txt_descricao.get("1.0", 'end-1c').upper()
                preco = ent_preco.get().replace(',', '.')
                preparo = ent_prep.get()
                if refeicao == '' :
                    messagebox.showwarning('Editar | Refeições:', 'Todos os campos devem ser preenchidos.', parent=root2)
                else:
                    try:
                        cursor.execute(
                            "UPDATE refeicoes SET\
                            refeicoes = %s,\
                            descricao = %s,\
                            preco = %s,\
                            preparo = %s\
                            WHERE id = %s", (refeicao,descricao,preco,preparo,result2[0],))
                        db.commit()
                    except:
                        messagebox.showerror('Editar | Refeições:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False
                    messagebox.showinfo('Editar | Refeiçoes:', 'Edição realizada com sucesso.', parent=root2)
                    cancelar_refeicoes()
                    atualizar_lista_refeicoes()

            lista_select = tree_configuracao.focus()
            if lista_select == "":
                messagebox.showwarning('Configurações | Refeições:', 'Selecione uma refeição na lista!', parent=root2)
            else:
                valor_lista = tree_configuracao.item(lista_select, "values")[0]
                try:
                    cursor.execute("SELECT * FROM refeicoes WHERE id= %s;",(valor_lista,))
                    result2 = cursor.fetchone()
                    #print(result2)
                except:
                    messagebox.showerror('Configurações | Refeições:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                    return False
                bt_salvar.grid_remove()
                bt_editar.grid_remove()
                bt_confirmar = customtkinter.CTkButton(fr4, text='Confirmar', **estilo_botao_padrao_form, command=confirmar_refeicoes)
                bt_confirmar.grid(row=0, column=1, padx=5)
                bt_cancelar = customtkinter.CTkButton(fr4, text='Cancelar', **estilo_botao_padrao_form, command=cancelar_refeicoes)
                bt_cancelar.grid(row=0, column=2, padx=5)
                setup_interno()

        def salvar():
            refeicao = ent_refeicao.get().upper()
            descricao = txt_descricao.get("1.0", 'end-1c').upper()
            preco = ent_preco.get().replace(',', '.')
            preparo = ent_prep.get()

            if refeicao == '' or descricao == '' or preco == '':
                messagebox.showwarning('Cadastro de Tipos de Mudança', 'Todos os campos devem ser preenchidos.', parent=root2)
            else:
                cursor.execute("SELECT * FROM refeicoes WHERE refeicoes=%s LIMIT 0,1", (refeicao,))
                verifica = cursor.fetchone()
                if verifica == None:
                    try:
                        cursor.execute(
                            "INSERT INTO refeicoes (refeicoes, descricao, preco, preparo) values(%s, %s, %s, %s)", (refeicao,descricao,preco,preparo,))
                        db.commit()
                    except:
                        messagebox.showerror('Cadastro de Refeições', 'Erro de conexão com o Banco de Dados.', parent=root2)
                        return False

                    messagebox.showinfo('Cadastro de Refeições', 'Cadastro efetuado com sucesso.', parent=root2)
                    cadastro_refeicoes()
                else:
                    messagebox.showerror('Cadastro de Refeições', 'Refeição já cadastrada:', parent=root2)
        
        for widget in frame5.winfo_children():
            widget.destroy()

        fr0 = Frame(frame5, bg='#ffffff')
        fr0.pack(side=TOP, fill=BOTH, expand=True)
        
        fr1 = Frame(fr0, bg='#ffffff')
        fr1.pack(side=TOP, fill=X)
        fr1_1 = Frame(fr0, bg='#ffffff')
        fr1_1.pack(side=TOP, fill=X)        
        fr2 = Frame(fr0, bg='#2a2d2e') #/// LINHA
        fr2.pack(padx=10, pady=10, fill="x", expand=False, side=TOP)
        fr3 = Frame(fr0, bg='#ffffff')
        fr3.pack(side=TOP, fill=BOTH, expand=True)
        fr4 = Frame(fr0, bg='#ffffff')
        fr4.pack(side=TOP, fill=X, pady=6)

        lbl_titulo = Label(fr1, text='Cadastro de Refeições', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#2a2d2e')
        lbl_titulo.grid(row=0, column=1, columnspan=2)
        
        lbl1=Label(fr1, text='Nome da Refeição:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl1.grid(row=2, column=1, sticky="w")
        ent_refeicao = customtkinter.CTkEntry(fr1, **estilo_entry_padrao, width=340)
        ent_refeicao.grid(row=2, column=2, pady=5)        
        ent_refeicao.focus_force()

        lbl1=Label(fr1, text='Descrição:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl1.grid(row=3, column=1, sticky="w")
        txt_descricao = scrolledtext.ScrolledText(fr1, **estilo_scrolledtext_padrão, width=39, height=2)
        txt_descricao.grid(row=3, column=2, pady=5)

        fr1.grid_columnconfigure(0, weight=1)
        fr1.grid_columnconfigure(3, weight=1)


        lbl1=Label(fr1_1, text='Tempo de Preparo(Hora):', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl1.grid(row=0, column=1, sticky="w")
        ent_prep = customtkinter.CTkEntry(fr1_1, **estilo_entry_padrao, width=120)
        ent_prep.grid(row=0, column=2, pady=5)        
        
        lbl1=Label(fr1_1, text='Preço:', font=fonte_padrao, bg='#ffffff', fg='#000000')
        lbl1.grid(row=0, column=3, sticky="w", padx=(20,0))
        ent_preco = customtkinter.CTkEntry(fr1_1, **estilo_entry_padrao, width=120)
        ent_preco.grid(row=0, column=4, pady=5)        

        fr1_1.grid_columnconfigure(0, weight=1)
        fr1_1.grid_columnconfigure(5, weight=1)

        #/////////FRAME2 LINHA

        #/////////FRAME3
        tree_configuracao = ttk.Style()
        #style.theme_use('default')
        style.configure('Treeview',
                        background='#ffffff',
                        rowheight=24,
                        fieldbackground='#ffffff',
                        font=fonte_padrao)
        style.configure("Treeview.Heading",
                        foreground='#1d366c',
                        background="#ffffff",
                        font=fonte_padrao_bold)
        style.map('Treeview', background=[('selected', cor_cinza)])

        tree_configuracao = ttk.Treeview(fr3, selectmode='browse')
        vsb = ttk.Scrollbar(fr3, orient="vertical", command=tree_configuracao.yview)
        vsb.pack(side=RIGHT, fill='y')
        tree_configuracao.configure(yscrollcommand=vsb.set)
        vsbx = ttk.Scrollbar(fr3, orient="horizontal", command=tree_configuracao.xview)
        vsbx.pack(side=BOTTOM, fill='x')
        tree_configuracao.configure(xscrollcommand=vsbx.set)
        tree_configuracao.pack(side=LEFT, fill=BOTH, expand=True, anchor='n')
        tree_configuracao["columns"] = ("1", "2", "3", "4", "5")
        tree_configuracao['show'] = 'headings'
        tree_configuracao.column("1", anchor='c', width=80)
        tree_configuracao.column("2", anchor='c')
        tree_configuracao.column("3", anchor='c')
        tree_configuracao.column("4", anchor='c')
        tree_configuracao.column("5", anchor='c')        
        tree_configuracao.heading("1", text="ID Refeição")
        tree_configuracao.heading("2", text="Nome da Refeição")
        tree_configuracao.heading("3", text="Descrição")        
        tree_configuracao.heading("4", text="Preparo|Horas")
        tree_configuracao.heading("5", text="Preço")
        tree_configuracao.tag_configure('par', background='#e9e9e9')
        tree_configuracao.tag_configure('impar', background='#ffffff')
        #tree_configuracao.bind("<Double-1>", duploclique_tree_configuracao)

        #/////////FRAME4
        bt_salvar = customtkinter.CTkButton(fr4, text='Salvar', **estilo_botao_padrao_form, command=salvar)
        bt_salvar.grid(row=0, column=1, padx=5)
        bt_editar = customtkinter.CTkButton(fr4, text='Editar', **estilo_botao_padrao_form, command=editar)
        bt_editar.grid(row=0, column=2, padx=5)
        fr4.grid_columnconfigure(0, weight=1)
        fr4.grid_columnconfigure(3, weight=1)

        atualizar_lista_refeicoes()    
    
    #///////////////////////// LAYOUT
    frame0 = customtkinter.CTkFrame(root2, corner_radius=10, fg_color='#ffffff', border_width=4, border_color='#2a2d2e')
    frame0.pack(padx=4, pady=10, fill="both", expand=True)

    frame1 = Frame(frame0, bg='#ffffff')
    frame1.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame2 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame2.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
    frame3 = Frame(frame0, bg='#ffffff')
    frame3.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame4 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame4.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
    frame5 = Frame(frame0, bg='#ffffff')
    frame5.pack(padx=10, pady=5, fill="both", expand=True, side=TOP)


    #/////////FRAME1
    lbl_titulo = Label(frame1, text='Configurações', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#1d366c')
    lbl_titulo.grid(row=0, column=1)
    frame1.grid_columnconfigure(0, weight=1)
    frame1.grid_columnconfigure(2, weight=1)

    #/////////FRAME2 LINHA HORIZONTAL
    
    #/////////FRAME3
    bt1=customtkinter.CTkButton(frame3, text='+ Usuários', **estilo_botao_padrao_form, command=cadastro_usuarios)
    bt1.grid(row=0, column=1, padx=5)

    bt1=customtkinter.CTkButton(frame3, text='+ Refeições', **estilo_botao_padrao_form, command=cadastro_refeicoes)
    bt1.grid(row=0, column=2, padx=5)

    bt1=customtkinter.CTkButton(frame3, text='+ Centro de Custo', **estilo_botao_padrao_form, command=cadastro_centrocusto)
    bt1.grid(row=0, column=3, padx=5)

    frame3.grid_columnconfigure(0, weight=1)
    frame3.grid_columnconfigure(4, weight=1)

    #/////////FRAME4 LINHA HORIZONTAL
    
    #/////////FRAME5
    root2.configure(bg='#ffffff')
    root2.title(titulos)
    root2.iconbitmap('img\\icone.ico')
    cadastro_usuarios()
    root2.state('zoomed')
    root2.wm_protocol("WM_DELETE_WINDOW", lambda: [ativa_loop(0), atualizar_lista_principal(), root2.destroy()])
    root2.mainloop()

def sair():
    root.quit()
    root.destroy()

def cc_protheus():
    cursor2.execute("SELECT CTT_CUSTO, CTT_DESC01\
                    FROM CTT010\
                    WHERE   CTT_FILIAL  = ' '\
                        AND CTT_BLOQ   <> '1'\
                        AND CTT_CLASSE  = '2'\
                        AND D_E_L_E_T_  = ' '\
                    ORDER BY CTT_CUSTO, CTT_DESC01")
    for teste in cursor2:
        cursor.execute("INSERT INTO centrocusto (\
                    nome_cc,\
                    descricao_cc)\
                    values(%s,%s)", (teste[0].strip(), teste[1].strip()))
        db.commit()
        print(teste[0], teste[1])

def alterar_senha():
    root2 = Toplevel(root)
    root2.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    root2.unbind_class("Button", "<Key-space>")
    root2.focus_force()
    root2.grab_set()

    window_width = 530
    window_height = 350
    screen_width = root2.winfo_screenwidth()
    screen_height = root2.winfo_screenheight() - 70
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    root2.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
    root2.resizable(0, 0)
    root2.configure(bg='#ffffff')
    root2.title(titulos)
    root2.iconbitmap('img\\icone.ico')

    #///////////////////////// FUNÇÕES
    def salvar_bind(event):
        salvar()
    def salvar():
        senha_atual = ent_senha_atual.get()
        senha_nova = ent_senha_nova.get()

        if senha_atual == '' or senha_nova == '':
            messagebox.showwarning('Alterar Senha:', 'Todos os campos devem ser preenchidos.', parent=root2)
        else:
            try:
                cursor.execute("SELECT usuario, senha from usuarios where id = %s and senha = %s", (usuario_logado[0], senha_atual,))
                verifica_senha_atual = cursor.fetchone()
            except:
                messagebox.showerror('Alterar Senha:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                return False
            
            #print(verifica_senha_atual)
            if verifica_senha_atual == None:
                messagebox.showerror('Alterar Senha:', 'Senha atual incorreta.', parent=root2)
            else:
                try:
                    cursor.execute("update usuarios set senha = %s where id = %s", (senha_nova, usuario_logado[0],))
                    db.commit()
                except:
                    messagebox.showerror('Alterar Senha:', 'Erro de conexão com o Banco de Dados.', parent=root2)
                    return False
                messagebox.showinfo('Alterar Senha:', 'Senha alterada com sucesso.', parent=root2)
                root2.destroy()

    def setup():
        ent_usuario.insert(0, usuario_logado[2])
        ent_usuario.configure(state='readonly')

    #///////////////////////// LAYOUT
    frame0 = customtkinter.CTkFrame(root2, corner_radius=10, fg_color='#ffffff', border_width=4, border_color='#2a2d2e')
    frame0.pack(padx=4, pady=10, fill="both", expand=True)

    frame1 = Frame(frame0, bg='#ffffff')
    frame1.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame2 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame2.pack(padx=10, pady=0, fill="x", expand=False, side=TOP)
    frame3 = Frame(frame0, bg='#ffffff')
    frame3.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)
    frame4 = Frame(frame0, bg='#2a2d2e') #/// LINHA
    frame4.pack(padx=10, pady=10, fill="x", expand=False, side=TOP)
    frame5 = Frame(frame0, bg='#ffffff')
    frame5.pack(padx=10, pady=5, fill="x", expand=False, side=TOP)


    lbl_titulo = Label(frame1, text='Alterar minha Senha', font=fonte_padrao_titulo_janelas, bg='#ffffff', fg='#1d366c')
    lbl_titulo.grid(row=0, column=1)
    frame1.grid_columnconfigure(0, weight=1)
    frame1.grid_columnconfigure(2, weight=1)

    #/////////FRAME2 LINHA HORIZONTAL
    
    #/////////FRAME3
    lbl2=Label(frame3, text='Usuário:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl2.grid(row=0, column=1, sticky="w", padx=5)
    ent_usuario = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=340)
    ent_usuario.grid(row=1, column=1, padx=5)

    lbl1=Label(frame3, text='Senha atual:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl1.grid(row=2, column=1, sticky="w", padx=5)
    ent_senha_atual = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=340, show='*')
    ent_senha_atual.grid(row=3, column=1, padx=5)
    ent_senha_atual.bind("<Return>", salvar_bind)

    lbl1=Label(frame3, text='Nova senha:', font=fonte_padrao, bg='#ffffff', fg='#000000')
    lbl1.grid(row=4, column=1, sticky="w", padx=5)
    ent_senha_nova = customtkinter.CTkEntry(frame3, **estilo_entry_padrao, width=340, show='*')
    ent_senha_nova.grid(row=5, column=1, padx=5)
    ent_senha_nova.bind("<Return>", salvar_bind)

    frame3.grid_columnconfigure(0, weight=1)
    frame3.grid_columnconfigure(3, weight=1)

    #/////////FRAME4 LINHA HORIZONTAL
    
    #/////////FRAME5 
    bt1 = customtkinter.CTkButton(frame5, text='Confirmar', **estilo_botao_padrao_form, command=salvar)
    bt1.grid(row=0, column=1, pady=0)
    
    frame5.grid_columnconfigure(0, weight=1)
    frame5.grid_columnconfigure(3, weight=1)

    '''root2.update()
    largura = frame0.winfo_width()
    altura = frame0.winfo_height()
    print(largura, altura)'''
    setup()
    root2.wm_protocol("WM_DELETE_WINDOW", lambda: [ativa_loop(0), atualizar_lista_principal(), root2.destroy()])
    root2.mainloop()

#///////////////////////// FIM FUNÇÕES

#///////////////////////// LAYOUT
root = customtkinter.CTk()
root.state('zoomed')
root.title(titulos)
root.iconbitmap('img\\icone.ico')
root.after(0, login)

# // Tema
style = ttk.Style()
style.theme_use('clam')
style.theme_settings('clam', {
    'TCombobox':{
        'configure' : {
            'padding' : 4,
            'arrowcolor' : '#ffffff',
            'arrowsize' : 15,
        }
    },
    'Vertical.TScrollbar' : {
        'configure' : {
            'background' : '#dedede',
            'troughcolor' : '#f1f1f1',
            'bordercolor' : '#dedede',
            'arrowcolor' : '#2a2d2e',
            'lightcolor' : '#dedede',
            'arrowsize' : 15,
        }
    },
    'Horizontal.TScrollbar' : {
        'configure' : {
            'background' : '#dedede',
            'troughcolor' : '#f1f1f1',
            'bordercolor' : '#dedede',
            'arrowcolor' : '#2a2d2e',
            'lightcolor' : '#dedede',
            'arrowsize' : 15,
        }
    },
    'Treeview' : {
        'configure' : {
            'background' : '#ffffff',
            'rowheight' : 24,
            'fieldbackground' : '#ffffff',
            'font' : fonte_padrao,
        }
    },
    'Treeview.Heading' : {
        'configure' : {
            'background' : '#ffffff',
            'foreground' : '#1d366c',
            'font' : fonte_padrao_bold,
            'borderwidth' : 0,
            'relief' : 'flat',
        }
    },
    })
root.option_add('*TCombobox*Listbox.background', '#2a2d2e')
root.option_add('*TCombobox*Listbox.foreground', '#ffffff')
root.option_add('*TCombobox*Listbox.selectBackground', '#4F4F4F')
root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')

style.map('Treeview', background=[('selected', cor_cinza)])
style.map('Treeview.Heading', background=[('active', '#ffffff')])

style.map('TCombobox', background=[('readonly','#1c1c1c')])
style.map('TCombobox', fieldbackground=[('readonly','#2a2d2e')])
style.map('TCombobox', selectbackground=[('readonly', '#2a2d2e')])
style.map('TCombobox', foreground=[('readonly', '#ffffff')])
# Frame Principal
frame0 = customtkinter.CTkFrame(root, corner_radius=10, fg_color='#ffffff', border_width=4, border_color=cor_branca)
frame0.pack(padx=20, pady=20, fill="both", expand=True)

# Layout de Frames
frame1 = Frame(frame0, bg=cor_branca)
frame1.pack(padx=10, pady=10, fill="x", expand=False, side=TOP)
frame2 = Frame(frame0, bg=cor_branca)
frame2.pack(padx=10, pady=4, fill="x", expand=False, side=TOP)

frame3 = Frame(frame0, bg=cor_branca)
frame3.pack(padx=10, pady=2, fill="y", expand=False, side=LEFT)

frame4 = Frame(frame0, bg='#cccccc')
frame4.pack(padx=(0,10), pady=2, fill="both", expand=True, side=RIGHT)
# Fim Layout de Frames

#// FRAME1 TITULO
img_logo = Image.open('img\\logo.png')
resize_logo = img_logo.resize((120, 90))
nova_img_logo = ImageTk.PhotoImage(resize_logo)
lbl_logo = Label(frame1, image=nova_img_logo, background=cor_branca)
lbl_logo.photo = nova_img_logo
lbl_logo.grid(row=0, column=1, padx=6)

lbl_titulo = Label(frame1, text='Simec Refeição', font=fonte_padrao_titulo, background=cor_branca, foreground=cor_azul)
lbl_titulo.grid(row=0, column=2)

frame1.grid_columnconfigure(0, weight=1)
frame1.grid_columnconfigure(3, weight=1)

#// FRAME2 MENU TOPO

lbl_user = Label(frame2, text='', font=fonte_padrao_bold, background=cor_branca, foreground=cor_azul)
lbl_user.grid(row=0, column=1)

frame2.grid_columnconfigure(0, weight=1)
frame2.grid_columnconfigure(2, weight=1)


#// FRAME3 MENU ESQUERDA
btn_login = customtkinter.CTkButton(frame3, text='Login', command=login, **estilo_botao_padrao_form)
btn_login.grid(row=0, column=1, pady=(0,5))

btn_solicit = customtkinter.CTkButton(frame3, text='+Solicitação', command=pedidos, **estilo_botao_padrao_form)
btn_solicit.grid(row=1, column=1, pady=5)
btn_solicit.configure(state='disabled')

btn_aprov = customtkinter.CTkButton(frame3, text='Atender Pedido', command=atender_pedido, **estilo_botao_padrao_form)
btn_aprov.grid(row=2, column=1, pady=5)
btn_aprov.configure(state='disabled')

btn_editar = customtkinter.CTkButton(frame3, text='Editar Pedido', command=editar_pedido, **estilo_botao_padrao_form)
btn_editar.grid(row=3, column=1, pady=5)
btn_editar.configure(state='disabled')

btn_print = customtkinter.CTkButton(frame3, text='Imprimir Pedido', command=imprimir_pedido, **estilo_botao_padrao_form)
btn_print.grid(row=4, column=1, pady=5)
#btn_print.configure(state='disabled')

frame3.grid_rowconfigure(6, weight=1)
frame3.grid_rowconfigure(6, weight=1)

btn_rel = customtkinter.CTkButton(frame3, text='Relatório', command=relatorio, **estilo_botao_padrao_form)
btn_rel.grid(row=7, column=1, pady=5)
btn_rel.configure(state='disabled')

btn_senha = customtkinter.CTkButton(frame3, text='Alterar|Senha', command=alterar_senha, **estilo_botao_padrao_form)
btn_senha.grid(row=8, column=1, pady=5)

btn_config = customtkinter.CTkButton(frame3, text='Configurações', command=configuracao, **estilo_botao_padrao_form)
btn_config.grid(row=9, column=1, pady=5)
btn_config.configure(state='disabled')

btn_sair = customtkinter.CTkButton(frame3, text='Sair', command=sair, **estilo_botao_padrao_form)
btn_sair.grid(row=10, column=1, pady=5)

frame3.grid_columnconfigure(0, weight=1)
frame3.grid_columnconfigure(2, weight=1)

#// FRAME4 CONTEUDO
tree_principal = ttk.Treeview(frame4, selectmode='browse')
vsb = ttk.Scrollbar(frame4, orient="vertical", command=tree_principal.yview)
vsb.pack(side=RIGHT, fill='y')
tree_principal.configure(yscrollcommand=vsb.set)
vsbx = ttk.Scrollbar(frame4, orient="horizontal", command=tree_principal.xview)
vsbx.pack(side=BOTTOM, fill='x')
tree_principal.configure(xscrollcommand=vsbx.set)
tree_principal.pack(side=LEFT, fill=BOTH, expand=True, anchor='n')
tree_principal["columns"] = ("1", "2", "3", "4", "5", "6", "7", "8")
tree_principal['show'] = 'headings'
tree_principal.column("1", anchor='c')
tree_principal.column("2", anchor='c')
tree_principal.column("3", anchor='c')
tree_principal.column("4", anchor='c')
tree_principal.column("5", anchor='c')
tree_principal.column("6", anchor='c')
tree_principal.column("7", anchor='c')
tree_principal.column("8", anchor='c')
tree_principal.heading("1", text="Nº Pedido")
tree_principal.heading("2", text="Data (Abertura)")
tree_principal.heading("3", text="Solicitante")
tree_principal.heading("4", text="Área")
tree_principal.heading("5", text="Tipo de Refeição")
tree_principal.heading("6", text="Entrega (Prevista)")
tree_principal.heading("7", text="Status")
tree_principal.heading("8", text="Data (Encerrado)")
tree_principal.tag_configure('par', background='#e9e9e9')
tree_principal.tag_configure('impar', background='#ffffff')
#tree_principal.bind("<Double-1>", duploclique_tree_principal)
frame4.grid_columnconfigure(0, weight=1)
frame4.grid_columnconfigure(3, weight=1)

#/////////////////////////////BANCO DE DADOS/////////////////////////////
db = mysql.connector.connect(
    #host="localhost",
    host="192.168.1.16",
    #user="root",
    user="acesso_rede",
    passwd="senha",
    database="simec_refeicoes",
)
cursor = db.cursor()
#/////////////////////////////FIM BANCO DE DADOS/////////////////////////////
root.mainloop()
