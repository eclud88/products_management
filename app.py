from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3 as sql
from flask_sqlalchemy import SQLAlchemy
import datetime
from datetime import timedelta, datetime
import calendar
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///../database/gestaodeprodutos.db"
db = SQLAlchemy(app)  # Cursor para a base de dados SQLite

       
########## PÁGINA LOGIN ##########


@app.route("/", methods=['GET', 'POST'])
def login():
    return render_template('login.html')


########## SISTEMA LOGIN ##########


@app.route("/login_validation", methods=['POST'])
def login_validation():
    # Conectar à base de dados
    data = 'database/logindata.db'
    con = sql.connect(data)
    cur = con.cursor()
    cur.execute('SELECT * FROM logindata')
    con.commit()
    allregistos = cur.fetchall()

    usernamelogin = request.form.get('username')
    passwordlogin = request.form.get('password')

    if usernamelogin == allregistos[0][0] and passwordlogin == allregistos[0][1]:
        return redirect(url_for('profileadmin'))
    elif usernamelogin == allregistos[1][0] and passwordlogin == allregistos[1][1]:
        return redirect(url_for('profilefornecedor'))
    elif usernamelogin == allregistos[2][0] and passwordlogin == allregistos[2][1]:
        return redirect(url_for('profilecliente'))

    # Se nenhuma das condições acima for atendida, significa que o 'login' está incorreto
    error_statement = "Login incorreto!"

    # Fechar a conexão com a base de dados
    cur.close()
    con.close()

    return render_template('login.html', error_statement=error_statement)


########## FORNECEDOR ##########


@app.route('/profilefornecedor', methods=['GET'])
def profilefornecedor():
    # Conectar às bases de dados
    gestao = 'database/gestaodeprodutos.db'
    con = sql.connect(gestao)
    cur = con.cursor()
    cur.execute('SELECT * FROM gestaodeprodutos')
    rows = cur.fetchall()

    compras = 'database/comprasadmin.db'
    con_compras = sql.connect(compras)
    cur_compras = con_compras.cursor()

    produtos = []

    for row in rows:
        produto = {
            "id": row[0],
            "nome": row[1],
            "marca": row[2],
            "preco": row[3],
            "quantidade": row[4],
            "fornecedor": row[5],
            "url_imagem": row[6],
        }
        produtos.append(produto)

    # Criar a tabela comprasadmin, se ela não existir
    cur_compras.execute('''
        CREATE TABLE IF NOT EXISTS comprasadmin (
            nome TEXT,
            marca TEXT,
            preco INTEGER,
            quantidade INTEGER,
            fornecedor TEXT,
            data_compra TEXT,
            url_imagem TEXT
        ) 
    ''')

    con_compras.commit()

    # Lógica para agrupar os produtos por fornecedor
    produtos_por_fornecedor = {}

    for produto in produtos:
        fornecedor = produto["fornecedor"]

        if fornecedor not in produtos_por_fornecedor:
            produtos_por_fornecedor[fornecedor] = []

        produtos_por_fornecedor[fornecedor].append(produto)

    # Cálculo do valor total das vendas por fornecedor
    cur_compras.execute('SELECT fornecedor, SUM(preco * quantidade) FROM comprasadmin GROUP BY fornecedor')
    valor_vendas_por_fornecedor = cur_compras.fetchall()

    # Produto mais vendido em quantidade
    cur_compras.execute(
        'SELECT nome, SUM(quantidade) FROM comprasadmin GROUP BY nome ORDER BY SUM(quantidade) DESC LIMIT 1')
    produto_mais_vendido = cur_compras.fetchone()

    # Produto menos vendido em quantidade
    cur_compras.execute(
        'SELECT nome, SUM(quantidade) FROM comprasadmin GROUP BY nome ORDER BY SUM(quantidade) ASC LIMIT 1')
    produto_menos_vendido = cur_compras.fetchone()

    # Produto que gera mais vendas
    cur_compras.execute(
        'SELECT nome, SUM(preco * quantidade) FROM comprasadmin GROUP BY nome ORDER BY SUM(preco * quantidade)'
        'DESC LIMIT 1')
    produto_mais_vendas = cur_compras.fetchone()

    # Fechar a conexão com a base de dados
    con_compras.close()
    con.close()

    return render_template('profilefornecedor.html', produtos_por_fornecedor=produtos_por_fornecedor,
                           valor_vendas_por_fornecedor=valor_vendas_por_fornecedor,
                           produto_mais_vendido=produto_mais_vendido, produto_menos_vendido=produto_menos_vendido,
                           produto_mais_vendas=produto_mais_vendas)


# Função para atualizar a quantidade e o preço de um produto na base de dados
@app.route('/profilefornecedor/atualizar_produto', methods=['POST'])
def atualizar_produto():
    data = request.json
    produto_id = data['productId']
    quantidade = data['newQuantity']
    preco = data['newPrice']

    # Conectar à base de dados
    connection = sql.connect('database/gestaodeprodutos.db')
    cursor = connection.cursor()

    cursor.execute('UPDATE gestaodeprodutos SET quantidade = ?, preco = ? WHERE id = ?',
                    (quantidade, preco, produto_id))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'Produto atualizado com sucesso'})


# Função para excluir um produto da base de dados
@app.route('/profilefornecedor/excluir_produto', methods=['POST'])
def excluir_produto():
    produto_id = request.form.get('productId')

    # Conectar à base de dados
    connection = sql.connect('database/gestaodeprodutos.db')
    cursor = connection.cursor()

    cursor.execute('DELETE FROM gestaodeprodutos WHERE id = ?', (produto_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return 'Produto excluído com sucesso!'


@app.route('/profilefornecedor/notificacoes_fornecedor', methods=['GET'])
def obter_notificacoes_fornecedor():
    # Conectar à base de dados
    connection = sql.connect('database/gestaodeprodutos.db')
    cursor = connection.cursor()

    # Consultar a tabela gestaodeprodutos
    query_gestaodeprodutos = '''
        SELECT nome, quantidade, fornecedor FROM gestaodeprodutos
    '''
    cursor.execute(query_gestaodeprodutos)
    resultados_gestaodeprodutos = cursor.fetchall()

    notificacoes = []
    for produto in resultados_gestaodeprodutos:
        nome_produto = produto[0]
        quantidade_atual = produto[1]
        fornecedor = produto[2]

        if quantidade_atual <= 5:
            notificacao = {
                'produto': nome_produto,
                'quantidade': quantidade_atual,
                'fornecedor': fornecedor,
            }
            notificacoes.append(notificacao)

    cursor.close()
    connection.close()

    return jsonify({'notificacoes': notificacoes})


@app.route('/profilefornecedor/estatisticas_fornecedor', methods=['GET'])
def estatisticas_fornecedor():
    return render_template('estatisticas_fornecedor.html')


@app.route('/profilefornecedor/vendas_do_mes_atual', methods=['GET'])
def vendas_do_mes_atual():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Obter a data e mês atual
    current_date = datetime.now().date()
    mes_atual = datetime.now().strftime('%B-%Y')

    # Obter o primeiro dia do mês atual
    first_day = current_date.replace(day=1)

    # Converter as datas para o formato correto
    first_day_str = first_day.strftime('%d-%m-%Y')
    last_day_str = current_date.strftime('%d-%m-%Y')

    # Consultar a tabela comprasadmin para obter os dados das vendas do mês atual por fornecedor
    query_vendas_atual = '''
        SELECT data_compra, fornecedor, SUM(preco * quantidade) AS total_vendas
        FROM comprasadmin
        WHERE data_compra BETWEEN ? AND ?
        GROUP BY data_compra, fornecedor
    '''

    cursor.execute(query_vendas_atual, (first_day_str, last_day_str))
    resultados_vendas = cursor.fetchall()

    # criar um dicionário para armazenar as vendas por fornecedor
    vendas_por_fornecedor = {}

    # Extrair as datas, fornecedores e o total de vendas
    for venda in resultados_vendas:
        data_venda = venda[0]
        fornecedor = venda[1]
        total_vendas = venda[2]

        if fornecedor not in vendas_por_fornecedor:
            vendas_por_fornecedor[fornecedor] = {'datas': [], 'vendas': []}

        vendas_por_fornecedor[fornecedor]['datas'].append(data_venda)
        vendas_por_fornecedor[fornecedor]['vendas'].append(total_vendas)

    # Criar uma lista de todas as datas até a data atual
    todas_datas = [first_day + timedelta(days=x) for x in range((current_date - first_day).days + 1)]
    todas_datas_str = [data.strftime('%d-%m-%Y') for data in todas_datas]

    # Preencher com zero os dias sem vendas para cada fornecedor
    for fornecedor, vendas in vendas_por_fornecedor.items():
        datas_vendas = vendas['datas']
        vendas_do_fornecedor = vendas['vendas']

        for data in todas_datas_str:
            if data not in datas_vendas:
                datas_vendas.append(data)
                vendas_do_fornecedor.append(0)

    # Ordenar as datas em ordem crescente
    for fornecedor, vendas in vendas_por_fornecedor.items():
        datas_vendas_sorted, vendas_do_fornecedor_sorted = zip(*sorted(zip(vendas['datas'], vendas['vendas'])))
        vendas['datas'] = datas_vendas_sorted
        vendas['vendas'] = vendas_do_fornecedor_sorted

    if len(vendas_por_fornecedor) == 0:
        graphJSON = None
        print("Ainda não houve vendas para importar dados.")
    else:
        # Gerar um gráfico de linhas para a evolução das vendas do mês atual por fornecedor
        fig = go.Figure()

        for fornecedor, vendas in vendas_por_fornecedor.items():
            fig.add_trace(go.Scatter(
                x=vendas['datas'],
                y=vendas['vendas'],
                mode='lines',
                name=fornecedor
            ))

        # Personalizar o layout do gráfico
        fig.update_layout(
            title=f'Evolução das Vendas por Fornecedor, {mes_atual}',
            xaxis_title='Data',
            yaxis_title='Total de Vendas (€)',
            yaxis=dict(range=[-max(max(vendas['vendas']) for vendas in vendas_por_fornecedor.values()) * 0.1,
                               max(max(vendas['vendas']) for vendas in vendas_por_fornecedor.values()) * 1.1])
        )

        # Converter o gráfico em formato JSON
        graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/vendas_mes_anterior', methods=['GET'])
def vendas_mes_anterior():
    # Conectar às bases de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()
    connection_gestao = sql.connect('database/gestaodeprodutos.db')
    cursor_gestao = connection_gestao.cursor()

    # Obter a data atual e o mês anterior
    current_date = datetime.now().date()
    mes_anterior = (current_date.replace(day=1) - timedelta(days=1)).strftime('%B-%Y')
    mes_anterior_strf = (current_date.replace(day=1) - timedelta(days=1)).strftime('%d-%m-%Y')

    # Consultar a tabela comprasadmin para obter os dados das vendas do mês anterior por fornecedor
    query_vendas_mes_anterior = '''
        SELECT fornecedor, data_compra, SUM(preco * quantidade) AS total_vendas
        FROM comprasadmin
        WHERE strftime('%m-%Y', data_compra) = ?
        GROUP BY fornecedor, data_compra
    '''

    cursor.execute(query_vendas_mes_anterior, (mes_anterior_strf,))
    resultados_vendas_mes_anterior = cursor.fetchall()

    # criar um dicionário para armazenar os dados de vendas por fornecedor
    vendas_fornecedores = {}

    # Processar os resultados das vendas por fornecedor
    for venda in resultados_vendas_mes_anterior:
        fornecedor = venda[0]
        data_compra = venda[1]
        total_vendas = venda[2]

        # Verificar se o fornecedor já está no dicionário de vendas
        if fornecedor not in vendas_fornecedores:
            vendas_fornecedores[fornecedor] = {'datas': [], 'vendas': []}

        # Adicionar os dados da venda ao dicionário de vendas do fornecedor
        vendas_fornecedores[fornecedor]['datas'].append(data_compra)
        vendas_fornecedores[fornecedor]['vendas'].append(total_vendas)

    # Criar uma lista de todas as datas do mês anterior
    primeiro_dia_mes_anterior = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes_anterior = current_date.replace(day=1) - timedelta(days=1)
    todas_datas_mes_anterior = [primeiro_dia_mes_anterior + timedelta(days=x) for x in range(
        (ultimo_dia_mes_anterior - primeiro_dia_mes_anterior).days + 1)]
    todas_datas_mes_anterior_str = [data.strftime('%d-%m-%Y') for data in todas_datas_mes_anterior]

    # Verificar se não há dados de vendas para nenhum fornecedor
    if len(vendas_fornecedores) == 0:
        # Consultar a tabela gestaodeprodutos para obter a lista de fornecedores
        query_fornecedores = '''
            SELECT DISTINCT fornecedor
            FROM gestaodeprodutos
        '''

        cursor_gestao.execute(query_fornecedores)
        fornecedores = cursor_gestao.fetchall()

        # Adicionar uma entrada para cada fornecedor com vendas zero
        for fornecedor in fornecedores:
            fornecedor = fornecedor[0]
            vendas_fornecedores[fornecedor] = {'datas': todas_datas_mes_anterior_str,
                                               'vendas': [0] * len(todas_datas_mes_anterior_str)}

    # Gerar o gráfico de linhas para a evolução das vendas do mês anterior por fornecedor
    fig = go.Figure()

    for fornecedor in vendas_fornecedores.keys():
        datas_fornecedor = vendas_fornecedores[fornecedor]['datas']
        vendas_do_fornecedor = vendas_fornecedores[fornecedor]['vendas']

        fig.add_trace(go.Scatter(
            x=datas_fornecedor,
            y=vendas_do_fornecedor,
            mode='lines',
            name=fornecedor,
        ))

        # Personalizar o layout do gráfico
        fig.update_layout(
            title=f'Evolução das Vendas por Fornecedor, {mes_anterior}',
            xaxis_title='Data',
            yaxis_title='Total de Vendas (€)',
            yaxis=dict(range=[-0.05, max(max(vendas_do_fornecedor), 1) * 1.1])  # Define o intervalo do eixo y
        )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()
    cursor_gestao.close()
    connection_gestao.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/vendas_anuais', methods=['GET'])
def vendas_anuais():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()
    connection_gestao = sql.connect('database/gestaodeprodutos.db')
    cursor_gestao = connection_gestao.cursor()

    # Obter o ano atual e o mês atual
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Criar uma lista com todos os meses até o mês atual
    months = [datetime(current_year, month, 1).strftime('%m-%Y') for month in range(1, current_month + 1)]
    nomes_meses = [datetime.strptime(month, '%m-%Y').strftime('%b') for month in months]

    # Consultar a tabela de compras para obter os totais de vendas mensais por fornecedor
    query_vendas = '''
            SELECT fornecedor, data_compra, SUM(preco * quantidade) AS total_vendas
            FROM comprasadmin
            WHERE strftime('%Y', 'now')
            GROUP BY fornecedor
        '''

    # Executar a consulta e obter os resultados
    cursor.execute(query_vendas)
    resultados_vendas = cursor.fetchall()

    # criar um dicionário para armazenar os valores de vendas por fornecedor e por mês
    vendas_por_fornecedor = {}

    for resultado in resultados_vendas:
        fornecedor = resultado[0]
        datas_vendas = resultado[1]
        vendas = resultado[2]

        # Listas para armazenar as datas e valores de vendas atualizados
        datas_vendas_atualizadas = []
        valores_vendas_atualizados = []
        datas_vendas_formatadas = [datetime.strptime(datas_vendas, '%d-%m-%Y').strftime('%m-%Y')]

        # Percorrer todos os meses e atualizar as datas e valores de vendas
        for mes_ano in months:
            if mes_ano in datas_vendas_formatadas:
                # O mês está presente nas datas de vendas, então obter o valor correspondente
                valor_vendas = vendas
            else:
                # O mês não está presente nas datas de vendas, então atribuir zero para as vendas
                valor_vendas = 0

            datas_vendas_atualizadas.append(mes_ano)
            valores_vendas_atualizados.append(valor_vendas)

        if fornecedor not in vendas_por_fornecedor:
            vendas_por_fornecedor[fornecedor] = {month: 0 for month in months}

        for month, valor_vendas in zip(datas_vendas_atualizadas, valores_vendas_atualizados):
            vendas_por_fornecedor[fornecedor][month] = valor_vendas

    # Consultar a tabela gestaodeprodutos para obter os nomes dos fornecedores
    query_fornecedores = '''
        SELECT fornecedor
        FROM gestaodeprodutos
    '''

    # Executar a consulta e obter os resultados
    cursor_gestao.execute(query_fornecedores)
    resultados_fornecedores = cursor_gestao.fetchall()

    # Extrair os nomes dos fornecedores
    nomes_fornecedores_todos = [fornecedor[0] for fornecedor in resultados_fornecedores]

    # Remover valores duplicados
    nomes_fornecedores = list(set(nomes_fornecedores_todos))

    # Gerar um gráfico de linhas para representar a evolução mensal das vendas por fornecedor
    fig = go.Figure()

    # Adicionar os traços para cada fornecedor
    for fornecedor in nomes_fornecedores:
        if fornecedor in vendas_por_fornecedor:
            vendas_do_fornecedor = [vendas_por_fornecedor[fornecedor].get(month, 0) for month in months]
        else:
            vendas_do_fornecedor = [0] * len(months)

        fig.add_trace(go.Scatter(
            x=months,
            y=vendas_do_fornecedor,
            mode='lines',
            name=fornecedor
        ))

        # Personalizar o layout do gráfico
        fig.update_layout(
            title=f'Evolução Mensal das Vendas , {current_year}',
            xaxis_title='Mês',
            yaxis_title='Total de Vendas (€)',
            yaxis=dict(rangemode='nonnegative'),
            xaxis=dict(
                tickmode='array',
                tickvals=months,
                ticktext=nomes_meses,
            )
        )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()
    cursor_gestao.close()
    connection_gestao.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/top3_vendidos_fornecedor', methods=['GET'])
def top3_vendidos_fornecedor():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela de compras para obter os dados dos produtos mais vendidos por fornecedor
    query_vendas = '''
        SELECT fornecedor, nome, SUM(quantidade) AS total_quantidades
        FROM comprasadmin
        GROUP BY fornecedor, nome
        ORDER BY fornecedor, total_quantidades DESC
    '''
    cursor.execute(query_vendas)
    resultados_vendas = cursor.fetchall()

    # criar um dicionário para armazenar os 3 produtos mais vendidos por fornecedor
    top3_vendidos_por_fornecedor = {}

    for fornecedor, produto, total_quantidades in resultados_vendas:
        if fornecedor not in top3_vendidos_por_fornecedor:
            top3_vendidos_por_fornecedor[fornecedor] = []

        top3_vendidos_por_fornecedor[fornecedor].append((produto, total_quantidades))

    # Criar listas para armazenar os nomes dos fornecedores, produtos e quantidades
    fornecedores = []
    produtos = []
    quantidades = []

    # Ordenar os produtos pelo total das quantidades vendidas
    produtos_vendidos = []
    for fornecedor in top3_vendidos_por_fornecedor:
        produtos_vendidos.extend(top3_vendidos_por_fornecedor[fornecedor])

    produtos_vendidos.sort(key=lambda x: x[1], reverse=True)
    top_produtos = produtos_vendidos[:3]

    for produto, quantidade in top_produtos:
        for fornecedor, produtos_fornecedor in top3_vendidos_por_fornecedor.items():
            for prod, quant in produtos_fornecedor:
                if prod == produto:
                    fornecedores.append(fornecedor)
                    produtos.append(produto)
                    quantidades.append(quantidade)
                    break

    # Criar o gráfico de rosca com os 3 produtos mais vendidos
    fig = go.Figure(data=[go.Pie(
        labels=[f'Produto: {produto}<br>Fornecedor: {fornecedor}<br>Quantidade: {quantidade}'
                for produto, fornecedor, quantidade in zip(produtos, fornecedores, quantidades)],
        values=quantidades,
        hoverinfo='label',

        hole=0.5
    )])

    # Adicionar a quantidade na legenda acima do gráfico
    fig.add_annotation(
        x=0.5,
        y=1.1,
        text=f'Total de Quantidades Vendidas: {sum(quantidades)}',
        showarrow=False,
        font=dict(size=12)
    )

    # Personalizar o layout do gráfico
    fig.update_layout(
        title='3 Produtos Mais Vendidos',
    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/menos_vendidos_fornecedor', methods=['GET'])
def menos_vendidos_fornecedor():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela de compras para obter os dados dos produtos mais vendidos por fornecedor
    query_vendas = '''
        SELECT fornecedor, nome, SUM(quantidade) AS total_quantidades
        FROM comprasadmin
        GROUP BY fornecedor, nome
        ORDER BY fornecedor, total_quantidades DESC
    '''
    cursor.execute(query_vendas)
    resultados_vendas = cursor.fetchall()

    # criar um dicionário para armazenar os 3 produtos mais vendidos por fornecedor
    top3_vendidos_por_fornecedor = {}

    for fornecedor, produto, total_quantidades in resultados_vendas:
        if fornecedor not in top3_vendidos_por_fornecedor:
            top3_vendidos_por_fornecedor[fornecedor] = []

        top3_vendidos_por_fornecedor[fornecedor].append((produto, total_quantidades))

    # Criar listas para armazenar os nomes dos fornecedores, produtos e quantidades
    fornecedores = []
    produtos = []
    quantidades = []

    # Ordenar os produtos pelo total das quantidades vendidas
    produtos_vendidos = []
    for fornecedor in top3_vendidos_por_fornecedor:
        produtos_vendidos.extend(top3_vendidos_por_fornecedor[fornecedor])

    produtos_vendidos.sort(key=lambda x: x[1], reverse=True)
    top_produtos = produtos_vendidos[-3:]

    for produto, quantidade in top_produtos:
        for fornecedor, produtos_fornecedor in top3_vendidos_por_fornecedor.items():
            for prod, quant in produtos_fornecedor:
                if prod == produto:
                    fornecedores.append(fornecedor)
                    produtos.append(produto)
                    quantidades.append(quantidade)
                    break

    # Criar o gráfico de rosca com os 3 produtos mais vendidos
    fig = go.Figure(data=[go.Pie(
        labels=[f'Produto: {produto}<br>Fornecedor: {fornecedor}<br>Quantidade: {quantidade}'
                for produto, fornecedor, quantidade in zip(produtos, fornecedores, quantidades)],
        values=quantidades,
        hoverinfo='label',

        hole=0.5
    )])

    # Adicionar a quantidade na legenda acima do gráfico
    fig.add_annotation(
        x=0.5,
        y=1.1,
        text=f'Total de Quantidades Vendidas: {sum(quantidades)}',
        showarrow=False,
        font=dict(size=12)
    )

    # Personalizar o layout do gráfico
    fig.update_layout(
        title='3 Produtos Menos Vendidos',
    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/quantidades_vendidas_fornecedor', methods=['GET'])
def quantidades_vendidas_fornecedor():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela de compras para obter os dados das quantidades de produtos por fornecedor
    query_quantidades = '''
            SELECT fornecedor, nome, SUM(quantidade) AS total_quantidades
            FROM comprasadmin
            GROUP BY fornecedor, nome
            ORDER BY total_quantidades DESC
        '''
    cursor.execute(query_quantidades)
    resultados_quantidades = cursor.fetchall()

    # Criar listas para armazenar os nomes dos fornecedores, produtos e quantidades
    fornecedores = []
    produtos = []
    quantidades = []

    for fornecedor, produto, total_quantidades in resultados_quantidades:
        fornecedores.append(fornecedor)
        produtos.append(produto)
        quantidades.append(total_quantidades)

    # Criar o gráfico de barras com as quantidades de todos os produtos
    fig = go.Figure()

    # Utilizar a paleta de cores predefinida do Plotly Express
    colors = px.colors.qualitative.Plotly

    for i, produto in enumerate(produtos):
        fig.add_trace(go.Bar(
            x=[produto],
            y=[quantidades[i]],
            hovertext=[f'{produto}<br>Fornecedor: {fornecedores[i]}<br>Quantidade: {quantidades[i]}'],
            hoverinfo='text',
            marker=dict(color=colors[i % len(colors)]),
            legendgroup=produto,
            name=produto
        ))

    # Definir as configurações da legenda
    fig.update_layout(
        title='Quantidades Vendidas por Produtos por Fornecedor',
        xaxis_title='Produtos',
        yaxis_title='Quantidade',
        showlegend=True,
        legend=dict(
            title='Produtos',
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='right',
            x=1,
            traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.5)'
        )
    )

    # Remover a legenda do eixo x
    fig.update_xaxes(showticklabels=False)

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/vendas_fornecedor', methods=['GET'])
def vendas_fornecedor():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela de compras para obter os dados das quantidades de produtos por fornecedor
    query_vendas = '''
            SELECT fornecedor, nome, SUM(quantidade * preco) AS total_vendas
            FROM comprasadmin
            GROUP BY fornecedor, nome
            ORDER BY total_vendas DESC
        '''
    cursor.execute(query_vendas)
    resultados_vendas = cursor.fetchall()

    # Criar listas para armazenar os nomes dos fornecedores, produtos e quantidades
    fornecedores = []
    produtos = []
    vendas = []

    for fornecedor, produto, total_vendas in resultados_vendas:
        fornecedores.append(fornecedor)
        produtos.append(produto)
        vendas.append(total_vendas)

    # Criar o gráfico de barras com as quantidades de todos os produtos
    fig = go.Figure()

    # Utilizar a paleta de cores predefinida do Plotly Express
    colors = px.colors.qualitative.Plotly

    for i, produto in enumerate(produtos):
        fig.add_trace(go.Bar(
            x=[produto],
            y=[vendas[i]],
            hovertext=[f'{produto}<br>Fornecedor: {fornecedores[i]}<br>Vendas: €{vendas[i]}'],
            hoverinfo='text',
            marker=dict(color=colors[i % len(colors)]),
            legendgroup=produto,
            name=produto
        ))

    # Definir as configurações da legenda
    fig.update_layout(
        title='Vendas por Produtos por Fornecedor',
        xaxis_title='Produtos',
        yaxis_title='Vendas (€)',
        showlegend=True,
        legend=dict(
            title='Produtos',
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='right',
            x=1,
            traceorder='normal',
            bgcolor='rgba(255, 255, 255, 0.5)'
        )
    )

    # Remover a legenda do eixo x
    fig.update_xaxes(showticklabels=False)

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/ranking_fornecedores', methods=['GET'])
def ranking_fornecedores():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela de compras para obter os dados das quantidades de produtos por fornecedor
    query_quantidades = '''
        SELECT fornecedor, SUM(quantidade) AS total_quantidades
        FROM comprasadmin
        GROUP BY fornecedor
        ORDER BY total_quantidades DESC
    '''
    cursor.execute(query_quantidades)
    resultados_quantidades = cursor.fetchall()

    # Extrair as quantidades
    quantidades = [quantidade for fornecedor, quantidade in resultados_quantidades]

    # Verificar se existem pelo menos três valores na lista
    if len(quantidades) >= 3:
        terceira_maior_quantidade = quantidades[2]
    else:
        terceira_maior_quantidade = None

    # Manter os fornecedores com quantidades iguais ou maiores que a do terceiro colocado
    top_fornecedores = [(fornecedor, quantidade) for fornecedor, quantidade in resultados_quantidades if
                        quantidade >= terceira_maior_quantidade]

    fornecedores_top3 = [fornecedor for fornecedor, _ in top_fornecedores]
    quantidades_top3 = [quantidade for _, quantidade in top_fornecedores]

    medalhas_top = ['🥇', '🥈', '🥉'][:len(fornecedores_top3)]

    # Criar um gráfico de barras com os fornecedores e quantidades vendidas
    fig = go.Figure(data=[
        go.Bar(
            x=fornecedores_top3,
            y=quantidades_top3,
            marker=dict(color=[
                'gold' if fornecedor == fornecedores_top3[0] else 'silver' if fornecedor == fornecedores_top3[1]
                else 'saddlebrown'
                for fornecedor in fornecedores_top3]),
            text=[f'{medalha} {fornecedor}<br>Quantidade Vendida: {quantidade}' for (medalha, fornecedor, quantidade)
                  in zip(medalhas_top, fornecedores_top3, quantidades_top3)],
            hoverinfo='text',
            textposition='outside'
        )
    ])

    # Definir as configurações do 'layout'
    fig.update_layout(
        title='Ranking dos Principais Fornecedores por Quantidades Vendidas',
        xaxis_title='Fornecedores',
        yaxis_title='Quantidades Vendidas',
        showlegend=False,
        hoverlabel=dict(bgcolor='white')
    )

    # Ajustar os valores da escala do eixo y
    fig.update_yaxes(range=[0, max(quantidades_top3) * 1.2])  # Ajuste o fator de ampliação conforme necessário

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilefornecedor/sobre_nos_fornecedores', methods=['GET'])
def sobre_nos_fornecedores():
    return render_template('sobre_nos_fornecedores.html')


########## ADMINISTRADOR ##########


# Função para obter os produtos do fornecedor
def obter_produtos_do_fornecedor():
    # Conectar à base de dados do fornecedor
    connection = sql.connect('database/gestaodeprodutos.db')
    cursor = connection.cursor()

    # Executar uma consulta SQL para obter os produtos do fornecedor
    query = "SELECT * FROM gestaodeprodutos"
    cursor.execute(query)
    produtos = cursor.fetchall()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return produtos


@app.route('/profileadmin', methods=['GET', 'POST'])
def profileadmin():
    # Conectar à base de dados
    connection = sql.connect('database/stockadmin.db')
    cursor_admin = connection.cursor()

    connection_cliente = sql.connect('database/comprascliente.db')
    cursor_cliente = connection_cliente.cursor()

    connection_compras_admin = sql.connect('database/comprasadmin.db')
    cursor_compras = connection_compras_admin.cursor()

    # Criar a tabela stockadmin, se ela não existir
    cursor_admin.execute('''
        CREATE TABLE IF NOT EXISTS stockadmin (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            marca TEXT,
            preco INTEGER,
            quantidade INTEGER,
            fornecedor TEXT,
            data_compra TEXT,
            url_imagem TEXT
        )
    ''')

    # Criar a tabela comprasadmin, se ela não existir
    cursor_compras.execute('''
        CREATE TABLE IF NOT EXISTS comprasadmin (
            nome TEXT,
            marca TEXT,
            preco INTEGER,
            quantidade INTEGER,
            fornecedor TEXT,
            data_compra TEXT,
            url_imagem TEXT
        ) 
    ''')

    # Criar a tabela comprascliente, se ela não existir
    cursor_cliente.execute('''
                CREATE TABLE IF NOT EXISTS comprascliente (            
                    nome TEXT,
                    marca TEXT,
                    preco INTEGER,
                    quantidade INTEGER,
                    total INTEGER,
                    data_compra TEXT,
                    url_imagem TEXT
                )
            ''')

    # Recuperar o valor total das compras
    query_total_compras = '''
    SELECT SUM(preco * quantidade) AS total_compras
    FROM comprasadmin
    '''
    cursor_compras.execute(query_total_compras)
    total_compras = cursor_compras.fetchone()[0] or 0

    # Recuperar o valor total das vendas
    query_total_vendas = '''
    SELECT SUM(preco * quantidade) AS total_vendas
    FROM comprascliente
    '''
    cursor_cliente.execute(query_total_vendas)
    total_vendas = cursor_cliente.fetchone()[0] or 0

    # Calcular o valor do lucro
    valor_vendas = total_vendas
    valor_compras = total_compras
    valor_lucro = valor_vendas - valor_compras

    # Recuperar os dados da tabela stockadmin
    cursor_admin.execute('SELECT * FROM stockadmin')
    stock_admin = cursor_admin.fetchall()

    # Recuperar o valor total das quantidades
    query_total_quantidades = '''
    SELECT SUM(quantidade) AS total_quantidades
    FROM stockadmin
    '''
    cursor_admin.execute(query_total_quantidades)
    total_quantidades = cursor_admin.fetchone()[0] or 0

    # Fechar a conexão com as bases de dados
    cursor_admin.close()
    connection.close()
    cursor_cliente.close()
    connection_cliente.close()
    cursor_compras.close()
    connection_compras_admin.close()

    return render_template('profileadmin.html', produtos=obter_produtos_do_fornecedor(),
                            total_vendas=total_vendas, total_compras=total_compras,
                            valor_lucro=valor_lucro, total_quantidades=total_quantidades, stock_admin=stock_admin)


def obter_quantidade_disponivel(produto_id):
    # Conectar à base de dados
    connection = sql.connect('database/gestaodeprodutos.db')
    cursor = connection.cursor()

    # Obter a quantidade disponível para um determinado produto
    query = '''
    SELECT quantidade FROM gestaodeprodutos WHERE id = ?
    '''
    cursor.execute(query, (produto_id,))
    result = cursor.fetchone()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    if result:
        quantidade_disponivel = int(result[0])
        return quantidade_disponivel
    else:
        return 0


@app.route('/profileadmin/comprar_produto', methods=['POST'])
def comprar_produto():
    data = request.get_json()
    produto_id = data.get('produto_id')
    quantidade = int(data.get('quantidade'))
    fornecedor = data.get('fornecedor')
    data_compra = datetime.now().strftime('%d-%m-%Y')
    url_imagem = data.get('url_imagem')

    # Conectar às bases de dados
    connection_historico = sql.connect('database/stockadmin.db')
    cursor_historico = connection_historico.cursor()

    connection_cliente = sql.connect('database/comprascliente.db')
    cursor_cliente = connection_cliente.cursor()

    connection_compras = sql.connect('database/comprasadmin.db')
    cursor_compras = connection_compras.cursor()

    # Criar a tabela stockadmin, se ela não existir
    cursor_historico.execute('''
            CREATE TABLE IF NOT EXISTS stockadmin (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                marca TEXT,
                preco INTEGER,
                quantidade INTEGER,
                fornecedor TEXT,
                data_compra TEXT,
                url_imagem TEXT
            )
        ''')

    # Criar a tabela comprascliente, se ela não existir
    cursor_cliente.execute('''
        CREATE TABLE IF NOT EXISTS comprascliente (
            nome TEXT,
            marca TEXT,
            preco INTEGER,
            quantidade INTEGER,
            total INTEGER,
            data_compra TEXT,
            url_imagem TEXT
        )
    ''')

    # Criar a tabela comprasadmin, se ela não existir
    cursor_compras.execute('''
        CREATE TABLE IF NOT EXISTS comprasadmin (
            nome TEXT,
            marca TEXT,
            preco INTEGER,
            quantidade INTEGER,
            fornecedor TEXT,
            data_compra TEXT,
            url_imagem TEXT
        )
    ''')

    # Conectar à base de dados
    connection_produtos = sql.connect('database/gestaodeprodutos.db')
    cursor_produtos = connection_produtos.cursor()

    # Obter os dados do produto com base no produto_id
    query_produtos = '''
        SELECT nome, marca, preco FROM gestaodeprodutos WHERE id = ?
    '''
    cursor_produtos.execute(query_produtos, (produto_id,))
    result = cursor_produtos.fetchone()

    if result:
        nome = result[0]
        marca = result[1]
        preco = result[2]

        # Verificar se o produto já existe no stock do admin
        query_verificar_produto_historico = '''
            SELECT * FROM stockadmin WHERE id = ?
        '''
        cursor_historico.execute(query_verificar_produto_historico, (produto_id,))
        produto_existente_historico = cursor_historico.fetchone()

        if produto_existente_historico:
            # Produto já existe no histórico, atualizar a quantidade e data da compra
            quantidade_existente_historico = produto_existente_historico[4]
            nova_quantidade_historico = quantidade_existente_historico + quantidade

            query_atualizar_quantidadedata_historico = '''
                UPDATE stockadmin SET quantidade = ?,  data_compra = ? WHERE id = ?
            '''
            cursor_historico.execute(query_atualizar_quantidadedata_historico,
                                     (nova_quantidade_historico, data_compra, produto_id))
            connection_historico.commit()

        else:
            # Produto não existe no histórico, inserir um novo registo
            query_inserir_produto_historico = '''
                INSERT INTO stockadmin (id, nome, marca, preco, quantidade, fornecedor, data_compra, url_imagem)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor_historico.execute(query_inserir_produto_historico,
                                     (produto_id, nome, marca, preco, quantidade, fornecedor, data_compra, url_imagem))
            connection_historico.commit()

        # Verificar se o produto já existe nas compras do admin
        query_verificar_produto_compras = '''
            SELECT * FROM comprasadmin WHERE nome = ? AND marca = ? AND preco = ? AND quantidade = ? AND fornecedor = ?
            AND data_compra = ? AND url_imagem = ?
        '''
        cursor_compras.execute(query_verificar_produto_compras, (nome, marca, preco, quantidade, fornecedor,
                                                                 data_compra, url_imagem))
        produto_existente_compras = cursor_compras.fetchone()

        if produto_existente_compras:
            # Produto já existe com a mesma data de compra, atualizar a quantidade
            quantidade_existente_compras = int(produto_existente_compras[2])
            nova_quantidade_compras = quantidade_existente_compras + quantidade

            query_atualizar_quantidade_compras = '''
                UPDATE comprasadmin SET quantidade = ? WHERE nome = ? AND marca = ? AND preco = ? AND
                fornecedor = ? AND data_compra = ? AND url_imagem = ?
            '''
            cursor_compras.execute(query_atualizar_quantidade_compras,
                                   (nova_quantidade_compras, nome, marca, preco, fornecedor, data_compra, url_imagem))
            connection_compras.commit()

        else:
            # Produto não existe com a mesma data de compra, inserir um novo registo
            query_inserir_produto_compras = '''
                INSERT INTO comprasadmin (nome, marca, preco, quantidade, fornecedor, data_compra, url_imagem)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            cursor_compras.execute(query_inserir_produto_compras,
                                   (nome, marca, preco, quantidade, fornecedor, data_compra, url_imagem))
            connection_compras.commit()

        # Atualizar a quantidade disponível no stock
        quantidade_disponivel = obter_quantidade_disponivel(produto_id)
        nova_quantidade_stock = quantidade_disponivel - quantidade

        query_atualizar_quantidade_stock = '''
            UPDATE gestaodeprodutos SET quantidade = ? WHERE id = ?
        '''
        cursor_produtos.execute(query_atualizar_quantidade_stock, (nova_quantidade_stock, produto_id))
        connection_produtos.commit()

        # Fechar a conexão com as bases de dados
        cursor_historico.close()
        connection_historico.close()

        cursor_cliente.close()
        connection_cliente.close()

        cursor_compras.close()
        connection_compras.close()

        cursor_produtos.close()
        connection_produtos.close()

        # Verificar notificações de "stock" baixo
        obter_notificacoes()

        return jsonify({'status': 'success', 'message': 'Compra realizada com sucesso!'})

    else:
        # Fechar a conexão com as bases de dados
        cursor_historico.close()
        connection_historico.close()

        cursor_cliente.close()
        connection_cliente.close()

        cursor_compras.close()
        connection_compras.close()

        cursor_produtos.close()
        connection_produtos.close()

        return jsonify({'status': 'error', 'message': 'Produto não encontrado.'})


# Função para excluir um produto da base de dados
@app.route('/profileadmin/excluir_produto', methods=['POST'])
def excluir_produto_admin():
    data = request.get_json()
    produto_id = data.get('productId')

    # Conectar à base de dados
    connection = sql.connect('database/stockadmin.db')
    cursor = connection.cursor()

    cursor.execute('DELETE FROM stockadmin WHERE id = ?', (produto_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({'message': 'Produto excluído com sucesso!'})


@app.route('/profileadmin/atualizar_stock_admin', methods=['POST'])
def atualizar_stock_admin():
    # Obter os dados enviados na solicitação POST
    dados = request.get_json()
    produtoId = dados.get('produtoId')
    nome = dados.get('nome')
    marca = dados.get('marca')
    preco = dados.get('preco')
    quantidade = dados.get('quantidade')
    fornecedor = dados.get('fornecedor')
    dataCompra = dados.get('dataCompra')
    urlImagem = dados.get('urlImagem')

    # Conectar à base de dados
    connection = sql.connect('database/stockadmin.db')
    cursor = connection.cursor()

    cursor.execute(
        'UPDATE stockadmin SET nome = ?, marca = ?, preco = ?, quantidade = ?, fornecedor = ?, data_compra = ?,'
        'url_imagem = ? WHERE id = ?',
        (nome, marca, preco, quantidade, fornecedor, dataCompra, urlImagem, produtoId))

    connection.commit()

    cursor.close()
    connection.close()

    # Retornar uma resposta JSON indicando sucesso ou erro
    return jsonify(message='Stock do administrador atualizado com sucesso')


@app.route('/profileadmin/notificacoes', methods=['GET'])
def obter_notificacoes():
    # Conectar às bases de dados
    connection = sql.connect('database/stockadmin.db')
    cursor = connection.cursor()

    connection_compras = sql.connect('database/comprasadmin.db')
    cursor_compras = connection_compras.cursor()

    # Criar a tabela comprasadmin, se ela não existir
    cursor_compras.execute('''
            CREATE TABLE IF NOT EXISTS comprasadmin (
                nome TEXT,
                marca TEXT,
                preco INTEGER,
                quantidade INTEGER,
                fornecedor TEXT,
                data_compra TEXT,
                url_imagem TEXT
            )
        ''')

    # Consultar a tabela comprasadmin para obter as informações de quantidade e data de compra
    query_compras = '''
        SELECT nome, quantidade, data_compra FROM comprasadmin
    '''
    cursor_compras.execute(query_compras)
    resultados_compras = cursor_compras.fetchall()

    # Consultar a tabela stockadmin para obter as informações de quantidade atual
    query_stockadmin = '''
        SELECT nome, SUM(quantidade) FROM stockadmin GROUP BY nome
    '''
    cursor.execute(query_stockadmin)
    resultados_stockadmin = cursor.fetchall()

    notificacoes = []
    for compra in resultados_compras:
        nome_produto = compra[0]
        quantidade_compra = compra[1]

        for stock in resultados_stockadmin:
            if stock[0] == nome_produto:
                quantidade_atual = stock[1]
                percentual_atual = (quantidade_atual / quantidade_compra) * 100

                if percentual_atual <= 10:
                    notificacao = {
                        'produto': nome_produto,
                        'quantidade': quantidade_atual,
                        'percentual': percentual_atual
                    }
                    notificacoes.append(notificacao)
                break

    cursor.close()
    connection.close()
    cursor_compras.close()
    connection_compras.close()

    return jsonify({'notificacoes': notificacoes})


@app.route('/profileadmin/historico_compras_admin', methods=['GET'])
def historico_compras_admin():
    # Conectar à base de dados
    connection = sql.connect('database/stockadmin.db')
    cursor = connection.cursor()

    # Recuperar os dados do stock do admin
    query = '''
    SELECT * FROM stockadmin
    '''
    cursor.execute(query)
    stock_admin = cursor.fetchall()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return render_template('profileadmin.html', stock_admin=stock_admin)


@app.route('/profileadmin/estatisticas_admin', methods=['GET'])
def estatisticas_admin():
    return render_template('estatisticas_admin.html')


@app.route('/profileadmin/top3_comprados_admin', methods=['GET'])
def top3_comprados_admin():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela comprasadmin para obter os dados das compras
    query_compras = '''
            SELECT nome, SUM(quantidade) AS total_quantidade
            FROM comprasadmin
            GROUP BY nome
        '''
    cursor.execute(query_compras)
    resultados_compras = cursor.fetchall()

    nomes_produtos = [compras[0] for compras in resultados_compras]
    total_quantidade = [vendas[1] for vendas in resultados_compras]

    # Criar um DataFrame com os dados
    data = pd.DataFrame({
        'nome': nomes_produtos,
        'quantidade': total_quantidade,
    })

    # Agrupar as compras por nome do produto e somar as quantidades e valores
    data_grouped = data.groupby('nome').agg({'quantidade': 'sum'}).reset_index()

    # Ordenar os dados pelo valor da quantidade em ordem decrescente
    data_grouped_sorted = data_grouped.sort_values('quantidade', ascending=False)

    # Selecionar apenas os três primeiros produtos mais comprados
    top_3_produtos = data_grouped_sorted.head(3)

    # Definir as cores para cada barra
    colors = {
        top_3_produtos['nome'].iloc[0]: 'indigo',
        top_3_produtos['nome'].iloc[1]: 'mediumturquoise',
        top_3_produtos['nome'].iloc[2]: 'magenta'
    }

    # Gerar um gráfico de barras agrupado por produto e quantidade
    fig = go.Figure(data=go.Bar(
        x=top_3_produtos['quantidade'],
        y=top_3_produtos['nome'],
        orientation='h',
        marker=dict(
            color=[colors.get(nome, 'blue') for nome in top_3_produtos['nome']]
            # Atribuir as cores corretas às barras
        )
    ))

    # Personalizar o layout do gráfico
    fig.update_layout(
        title='3 Produtos Mais Comprados',
        xaxis_title='Quantidade',
        yaxis_title='Produtos',
        yaxis=dict(autorange="reversed"),  # Inverter a ordem dos produtos no eixo y

    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/menos_comprados_admin', methods=['GET'])
def menos_comprados_admin():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela comprasadmin para obter os dados das compras
    query_compras = '''
            SELECT nome, SUM(quantidade) AS total_quantidade
            FROM comprasadmin
            GROUP BY nome
        '''
    cursor.execute(query_compras)
    resultados_compras = cursor.fetchall()

    nomes_produtos = [compras[0] for compras in resultados_compras]
    total_quantidade = [compras[1] for compras in resultados_compras]

    # Criar um DataFrame com os dados
    data = pd.DataFrame({
        'nome': nomes_produtos,
        'quantidade': total_quantidade,
    })

    # Agrupar as vendas por nome do produto e somar as quantidades e valores
    data_grouped = data.groupby('nome').agg({'quantidade': 'sum'}).reset_index()

    # Ordenar os dados pelo valor da quantidade em ordem decrescente
    data_grouped_sorted = data_grouped.sort_values('quantidade', ascending=False)

    # Selecionar apenas os três primeiros produtos menos comprados
    menos_comprados = data_grouped_sorted.tail(3)

    # Definir as cores para cada barra
    colors = {
        menos_comprados['nome'].iloc[0]: 'darkviolet',
        menos_comprados['nome'].iloc[1]: 'yellowgreen',
        menos_comprados['nome'].iloc[2]: 'tomato'
    }

    # Gerar um gráfico de barras agrupado por produto e quantidade
    fig = go.Figure(data=go.Bar(
        x=menos_comprados['quantidade'],
        y=menos_comprados['nome'],
        orientation='h',
        marker=dict(
            color=[colors.get(nome, 'blue') for nome in menos_comprados['nome']]
            # Atribuir as cores corretas às barras
        )
    ))

    # Personalizar o layout do gráfico
    fig.update_layout(
        title='3 Produtos Menos Comprados',
        xaxis_title='Quantidade',
        yaxis_title='Produtos',
        yaxis=dict(autorange="reversed"),  # Inverter a ordem dos produtos no eixo y

    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/grafico_compras_produto_admin', methods=['GET'])
def grafico_compras_produto_admin():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela comprasadmin para obter os dados das compras
    query_compras = '''
        SELECT nome, marca, preco, quantidade, data_compra
        FROM comprasadmin
    '''
    cursor.execute(query_compras)
    resultados_compras = cursor.fetchall()

    # Extrair os nomes dos produtos, quantidades compradas, preços e datas de compra
    nomes_produtos = [compra[0] for compra in resultados_compras]
    quantidades_compradas = [compra[3] for compra in resultados_compras]
    precos = [compra[2] for compra in resultados_compras]
    datas_compra = [pd.to_datetime(compra[4], format='%d-%m-%Y') for compra in resultados_compras]  # Extrair as datas

    # Calcular o valor das compras (preco * quantidade)
    valores_compras = [preco * quantidade for preco, quantidade in zip(precos, quantidades_compradas)]

    if len(nomes_produtos) == 0:
        graphJSON = None
        print("Ainda não houve compras para importar dados.")
    else:
        # Criar um DataFrame com os dados
        data = pd.DataFrame({
            'nome': nomes_produtos,
            'quantidade': quantidades_compradas,
            'valor_compra': valores_compras,
            'data_compra': datas_compra
        })

        # Extrair o mês e ano da coluna 'data_compra'
        data['mes_ano'] = data['data_compra'].dt.strftime('%B/%Y')

        # Agrupar as compras por mês, ano, nome do produto e somar as quantidades e valores
        data_grouped = data.groupby(['mes_ano', 'nome']).agg(
            {'quantidade': 'sum', 'valor_compra': 'sum'}).reset_index()

        # Ordenar os resultados das compras por valor compra em ordem decrescente
        data_grouped = data_grouped.sort_values('valor_compra', ascending=False)

        # Gerar um gráfico de barras agrupado por produto e mês
        fig = px.bar(data_grouped, x='nome', y='valor_compra', color='nome',
                      labels={'valor_compra': 'Valor das Compras', 'nome': 'Produto'},
                      title=f'Compras Mensais por Produto (ordem decrescente),'
                            f'{data_grouped["mes_ano"].iloc[0]}')

        # Atualizar o layout do gráfico
        fig.update_layout(
            xaxis=dict(
                title='Produtos',
                showticklabels=False
            ),
            yaxis_title='Valor das Compras (€)',
            title={
                'x': 0.5,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            barmode='group',
            bargap=0.1,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )

        # Atualizar o layout do gráfico
        fig.update_layout(
            yaxis=dict(
                range=[0, max(valores_compras) * 1.1]  # Ajusta o limite superior do eixo y
            ),
        )

        # Legenda de cores das barras
        fig.update_traces(showlegend=True)

        # Remover a anotação dos nomes dos produtos
        fig.update_layout(annotations=[])

        # Converter o gráfico em formato JSON
        graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/grafico_vendas_produto_admin', methods=['GET'])
def grafico_vendas_produto_admin():
    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Consultar a tabela comprascliente para obter os dados das compras
    query_vendas = '''
        SELECT nome, marca, preco, quantidade, data_compra
        FROM comprascliente
    '''
    cursor.execute(query_vendas)
    resultados_vendas = cursor.fetchall()

    # Extrair os nomes dos produtos, quantidades vendidas, preços e datas de compra
    nomes_produtos = [venda[0] for venda in resultados_vendas]
    quantidades_vendidas = [venda[3] for venda in resultados_vendas]
    precos = [venda[2] for venda in resultados_vendas]
    datas_venda = [pd.to_datetime(venda[4], format='%d-%m-%Y') for venda in resultados_vendas]  # Extrair as datas

    # Calcular o valor das vendas (preco * quantidade)
    valores_vendas = [preco * quantidade for preco, quantidade in zip(precos, quantidades_vendidas)]

    if len(nomes_produtos) == 0:
        graphJSON = None
        print("Ainda não houve compras para importar dados.")
    else:
        # Criar um DataFrame com os dados
        data = pd.DataFrame({
            'nome': nomes_produtos,
            'quantidade': quantidades_vendidas,
            'valor_venda': valores_vendas,
            'data_venda': datas_venda
        })

        # Extrair o mês e ano da coluna 'data_venda'
        data['mes_ano'] = data['data_venda'].dt.strftime('%B/%Y')

        # Agrupar as vendas por mês, ano, nome do produto e somar as quantidades e valores
        data_grouped = data.groupby(['mes_ano', 'nome']).agg(
            {'quantidade': 'sum', 'valor_venda': 'sum'}).reset_index()

        # Ordenar os resultados das vendas por valor venda em ordem decrescente
        data_grouped = data_grouped.sort_values('valor_venda', ascending=False)

        # Gerar um gráfico de barras agrupado por produto e mês
        fig = px.bar(data_grouped, x='nome', y='valor_venda', color='nome',
                      labels={'valor_venda': 'Valor das Vendas', 'nome': 'Produto'},
                      title=f'Vendas Mensais por Produto (ordem decrescente),'
                            f'{data_grouped["mes_ano"].iloc[0]}')

        # Atualizar o layout do gráfico
        fig.update_layout(
            xaxis=dict(
                title='Produtos',
                showticklabels=False
            ),
            yaxis_title='Valor das Vendas (€)',
            title={
                'x': 0.5,
                'y': 0.9,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            barmode='group',
            bargap=0.1,
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )

        # Atualizar o layout do gráfico
        fig.update_layout(
            yaxis=dict(
                range=[0, max(valores_vendas) * 1.1]  # Ajusta o limite superior do eixo y
            ),
        )

        # Legenda de cores das barras
        fig.update_traces(showlegend=True)

        # Remover a anotação dos nomes dos produtos
        fig.update_layout(annotations=[])

        # Converter o gráfico em formato JSON
        graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/top3_vendidos_admin', methods=['GET'])
def top3_vendidos_admin():
    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Consultar a tabela comprascliente para obter os dados das compras
    query_vendas = '''
            SELECT nome, SUM(quantidade) AS total_quantidade
            FROM comprascliente
            GROUP BY nome
        '''
    cursor.execute(query_vendas)
    resultados_vendas = cursor.fetchall()

    nomes_produtos = [vendas[0] for vendas in resultados_vendas]
    total_quantidade = [vendas[1] for vendas in resultados_vendas]

    # Criar um DataFrame com os dados
    data = pd.DataFrame({
        'nome': nomes_produtos,
        'quantidade': total_quantidade,
    })

    # Agrupar as compras por nome do produto e somar as quantidades e valores
    data_grouped = data.groupby('nome').agg({'quantidade': 'sum'}).reset_index()

    # Ordenar os dados pelo valor da quantidade em ordem decrescente
    data_grouped_sorted = data_grouped.sort_values('quantidade', ascending=False)

    # Selecionar apenas os três primeiros produtos mais comprados
    top_3_produtos = data_grouped_sorted.head(3)

    # Definir as cores para cada barra
    colors = {
        top_3_produtos['nome'].iloc[0]: 'darkslateblue',
        top_3_produtos['nome'].iloc[1]: 'gold',
        top_3_produtos['nome'].iloc[2]: 'lightpink'
    }

    # Gerar um gráfico de barras agrupado por produto e quantidade
    fig = go.Figure(data=go.Bar(
        x=top_3_produtos['quantidade'],
        y=top_3_produtos['nome'],
        orientation='h',
        marker=dict(
            color=[colors.get(nome, 'blue') for nome in top_3_produtos['nome']]
            # Atribuir as cores corretas às barras
        )
    ))

    # Personalizar o layout do gráfico
    fig.update_layout(
        title='3 Produtos Mais Vendidos',
        xaxis_title='Quantidade',
        yaxis_title='Produtos',
        yaxis=dict(autorange="reversed"),  # Inverter a ordem dos produtos no eixo y

    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/menos_vendidos_admin', methods=['GET'])
def menos_vendidos_admin():
    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Consultar a tabela comprascliente para obter os dados das compras
    query_vendas = '''
            SELECT nome, SUM(quantidade) AS total_quantidade
            FROM comprascliente
            GROUP BY nome
        '''
    cursor.execute(query_vendas)
    resultados_vendas = cursor.fetchall()

    nomes_produtos = [vendas[0] for vendas in resultados_vendas]
    total_quantidade = [vendas[1] for vendas in resultados_vendas]

    # Criar um DataFrame com os dados
    data = pd.DataFrame({
        'nome': nomes_produtos,
        'quantidade': total_quantidade,
    })

    # Agrupar as vendas por nome do produto e somar as quantidades e valores
    data_grouped = data.groupby('nome').agg({'quantidade': 'sum'}).reset_index()

    # Ordenar os dados pelo valor da quantidade em ordem decrescente
    data_grouped_sorted = data_grouped.sort_values('quantidade', ascending=False)

    # Selecionar apenas os três primeiros produtos menos vendidos
    menos_vendidos = data_grouped_sorted.tail(3)

    # Definir as cores para cada barra
    colors = {
        menos_vendidos['nome'].iloc[0]: 'springgreen',
        menos_vendidos['nome'].iloc[1]: 'silver',
        menos_vendidos['nome'].iloc[2]: 'lightsalmon'
    }

    # Gerar um gráfico de barras agrupado por produto e quantidade
    fig = go.Figure(data=go.Bar(
        x=menos_vendidos['quantidade'],
        y=menos_vendidos['nome'],
        orientation='h',
        marker=dict(
            color=[colors.get(nome, 'blue') for nome in menos_vendidos['nome']]
            # Atribuir as cores corretas às barras
        )
    ))

    # Personalizar o layout do gráfico
    fig.update_layout(
        title='3 Produtos Menos Vendidos',
        xaxis_title='Quantidade',
        yaxis_title='Produtos',
        yaxis=dict(autorange="reversed"),  # Inverter a ordem dos produtos no eixo y

    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/vendas_compras', methods=['GET'])
def vendas_compras():
    # Conectar às bases de dados
    connection_admin = sql.connect('database/comprasadmin.db')
    cursor_admin = connection_admin.cursor()

    connection_cliente = sql.connect('database/comprascliente.db')
    cursor_cliente = connection_cliente.cursor()

    current_month = datetime.now().month
    current_year = datetime.now().year

    # Obter os nomes dos meses até o mês atual
    meses_ano = [calendar.month_abbr[i] for i in range(1, current_month + 1)]

    # Consulta para obter os dados de vendas
    query_vendas = '''
        SELECT data_compra, SUM(preco * quantidade) AS total_vendas
        FROM comprascliente
        WHERE strftime('%Y', 'now')
    '''
    cursor_cliente.execute(query_vendas)
    dados_vendas = cursor_cliente.fetchall()

    datas_vendas = [dado[0] for dado in dados_vendas]
    valores_vendas = [dado[1] for dado in dados_vendas]

    # Criar uma lista de todos os meses desde janeiro até ao mês atual em formato numérico
    months = [datetime(current_year, month, 1).strftime('%m-%Y') for month in range(1, current_month + 1)]

    # Listas para armazenar as datas e valores de vendas atualizados
    datas_vendas_atualizadas = []
    valores_vendas_atualizados = []
    datas_vendas_formatadas = [datetime.strptime(data, '%d-%m-%Y').strftime('%m-%Y') for data in datas_vendas]

    # Percorrer todos os meses e atualizar as datas e valores de vendas
    for mes_ano in months:
        if mes_ano in datas_vendas_formatadas:
            # O mês está presente nas datas de vendas, então obter o valor correspondente
            indice = datas_vendas_formatadas.index(mes_ano)
            valor_vendas = valores_vendas[indice]
            datas_vendas_atualizadas.append(mes_ano)
            valores_vendas_atualizados.append(valor_vendas)
        else:
            # O mês não está presente nas datas de vendas, então adicionar zero para as vendas
            datas_vendas_atualizadas.append(mes_ano)
            valores_vendas_atualizados.append(0)

    # Consulta para obter os dados das compras
    query_compras = '''
        SELECT data_compra, SUM(preco * quantidade) AS total_compras
        FROM comprasadmin
        WHERE strftime('%Y', 'now')
    '''
    cursor_admin.execute(query_compras)
    dados_compras = cursor_admin.fetchall()

    datas_compras = [dado[0] for dado in dados_compras]
    valores_compras = [dado[1] for dado in dados_compras]

    # Listas para armazenar as datas e valores de vendas atualizados
    datas_compras_atualizadas = []
    valores_compras_atualizados = []
    datas_compras_formatadas = [datetime.strptime(data, '%d-%m-%Y').strftime('%m-%Y') for data in datas_compras]

    # Percorrer todos os meses e atualizar as datas e valores de vendas
    for mes_ano in months:
        if mes_ano in datas_compras_formatadas:
            # O mês está presente nas datas de vendas, então obter o valor correspondente
            indice = datas_compras_formatadas.index(mes_ano)
            valor_compras = valores_compras[indice]
            datas_compras_atualizadas.append(mes_ano)
            valores_compras_atualizados.append(valor_compras)
        else:
            # O mês não está presente nas datas de vendas, então adicionar zero para as vendas
            datas_compras_atualizadas.append(mes_ano)
            valores_compras_atualizados.append(0)

    # Criar o layout do gráfico
    layout = go.Layout(
        title=f'Evolução Mensal das Vendas e Compras , {current_year}',
        xaxis=dict(title='Mês'),
        yaxis=dict(title='Total (€)'),
    )

    # Criar a figura do gráfico
    fig = go.Figure(layout=layout)

    fig.add_trace(go.Scatter(x=meses_ano, y=valores_vendas_atualizados, name='Vendas',
                               line=dict(color='firebrick', width=4)))
    fig.add_trace(go.Scatter(x=meses_ano, y=valores_compras_atualizados, name='Compras',
                               line=dict(color='royalblue', width=4)))

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com as bases de dados
    cursor_admin.close()
    connection_admin.close()
    cursor_cliente.close()
    connection_cliente.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/grafico_compras_fornecedor_admin', methods=['GET'])
def grafico_compras_fornecedor_admin():
    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela comprasadmin para obter os dados das compras
    query_compras = '''
        SELECT fornecedor, SUM(preco * quantidade) AS valor_compra
        FROM comprasadmin
        GROUP BY fornecedor
    '''
    cursor.execute(query_compras)
    resultados_compras = cursor.fetchall()

    # Extrair os nomes dos fornecedores e valores de compra
    nomes_fornecedores = [compra[0] for compra in resultados_compras]
    valores_compras = [compra[1] for compra in resultados_compras]

    if len(nomes_fornecedores) == 0:
        graphJSON = None
        print("Ainda não houve compras para importar dados.")
    else:
        # Criar um DataFrame com os dados
        data = pd.DataFrame({
            'fornecedor': nomes_fornecedores,
            'valor_compra': valores_compras
        })

        # Ordenar os resultados das compras por valor de compra em ordem decrescente
        data = data.sort_values('valor_compra', ascending=False)

        # Gerar um gráfico de barras para os valores de compra por fornecedor
        fig = px.bar(data, x='fornecedor', y='valor_compra', color='fornecedor',
                     labels={'valor_compra': 'Valor das Compras', 'fornecedor': 'Fornecedor'},
                     title='Compras por Fornecedor (ordem decrescente)')

        # Atualizar o layout do gráfico
        fig.update_layout(
            xaxis=dict(title='Fornecedor'),
            yaxis=dict(title='Valor das Compras (€)'),
            title={'x': 0.5, 'y': 0.9, 'xanchor': 'center', 'yanchor': 'top'},
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )

        # Converter o gráfico em formato JSON
        graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profileadmin/grafico_compras_fornecedor_admin_mes', methods=['GET'])
def grafico_compras_fornecedor_admin_mes():
    # Obter o mês e ano atual
    mes_atual = datetime.now().strftime('%B-%Y')
    data_atual = datetime.now()

    # Obter a data do primeiro dia do mês atual
    primeiro_dia_mes_atual = data_atual.replace(day=1)

    # Criar o intervalo de datas desde o primeiro dia do mês até o dia atual
    datas_mes_atual_dias = pd.date_range(start=primeiro_dia_mes_atual, end=data_atual, freq='D')
    datas_mes_atual = datas_mes_atual_dias.strftime('%d-%m-%Y')

    # Conectar à base de dados
    connection = sql.connect('database/comprasadmin.db')
    cursor = connection.cursor()

    # Consultar a tabela comprasadmin para obter os dados das compras
    query_compras = '''
            SELECT fornecedor, data_compra, SUM(preco * quantidade) AS valor_compra
            FROM comprasadmin
            WHERE strftime('%m-%Y', 'now')
            GROUP BY fornecedor, data_compra
        '''
    cursor.execute(query_compras)
    resultados_compras = cursor.fetchall()

    if len(resultados_compras) == 0:
        print("Ainda não houve compras para importar dados.")
    else:
        nomes_fornecedores = [resultado[0] for resultado in resultados_compras]
        datas_compras = [resultado[1] for resultado in resultados_compras]
        valores_compras = [resultado[2] for resultado in resultados_compras]
        nomes_fornecedores_todos = []
        for elemento in nomes_fornecedores:
            if elemento not in nomes_fornecedores_todos:
                nomes_fornecedores_todos.append(elemento)

        resultados_ordenados = {}
        for fornecedor, data, valor in zip(nomes_fornecedores, datas_compras, valores_compras):
            if fornecedor not in resultados_ordenados:
                resultados_ordenados[fornecedor] = {}
            resultados_ordenados[fornecedor][data] = valor

        # Criar o gráfico de linhas
        fig = px.line()

        # Adicionar os dados de compras para cada fornecedor ao gráfico
        for fornecedor in resultados_ordenados:
            datas_fornecedor = list(resultados_ordenados[fornecedor].keys())
            valores_fornecedor = list(resultados_ordenados[fornecedor].values())

            # Preencher com zeros as datas que não têm valores de compras registrados
            for data in datas_mes_atual:
                if data not in datas_fornecedor:
                    datas_fornecedor.append(data)
                    valores_fornecedor.append(0)

            # Ordenar as datas e valores de compras por ordem crescente de datas
            datas_fornecedor, valores_fornecedor = zip(*sorted(zip(datas_fornecedor, valores_fornecedor)))

            # Adicionar o traço do fornecedor ao gráfico
            fig.add_trace(go.Scatter(x=datas_fornecedor, y=valores_fornecedor, mode='lines+markers', name=fornecedor))

        # Atualizar as configurações do gráfico
        fig.update_layout(
            xaxis_title='Data',
            yaxis_title='Valor das Compras (€)',
            title=f'Evolução Diária das Compras por Fornecedor, {mes_atual}',
            xaxis=dict(tickformat='%d-%m-%Y'),  # Formato das datas no eixo x
            legend_title='Fornecedor',  # Título da legenda
            hovermode='x unified',  # Exibe os valores de todas as linhas quando passa o mouse sobre o gráfico
        )

        # Converter o gráfico em formato JSON
        graphJSON = fig.to_json()

        # Fechar a conexão com a base de dados
        cursor.close()
        connection.close()

        return jsonify(graphJSON=graphJSON)


########## CLIENTE ##########


@app.route('/profilecliente', methods=['GET'])
def profilecliente():
    # Conectar às bases de dados
    connection_admin = sql.connect('database/stockadmin.db')
    cursor_admin = connection_admin.cursor()

    connection_cliente = sql.connect('database/comprascliente.db')
    cursor_cliente = connection_cliente.cursor()

    # Criar a tabela stockadmin, se ela não existir
    cursor_admin.execute('''
            CREATE TABLE IF NOT EXISTS stockadmin (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                marca TEXT,
                preco INTEGER,
                quantidade INTEGER,
                fornecedor TEXT,
                data_compra TEXT,
                url_imagem TEXT
            )
        ''')

    # Recuperar os dados do stock do admin
    query_admin = '''
    SELECT nome, marca, ROUND(preco * 1.3, 2), quantidade, ROUND((preco * 1.3) * quantidade, 2) AS total,
    data_compra, url_imagem FROM stockadmin
    '''
    cursor_admin.execute(query_admin)
    stock_admin = cursor_admin.fetchall()

    # Criar a tabela comprascliente, se ela não existir
    cursor_cliente.execute('''
            CREATE TABLE IF NOT EXISTS comprascliente (
                nome TEXT,
                marca TEXT,
                preco INTEGER,
                quantidade INTEGER,
                total INTEGER,
                data_compra TEXT,
                url_imagem TEXT
            )
        ''')

    # Recuperar os dados das compras do cliente
    query_cliente = '''
    SELECT nome, marca, preco, quantidade, preco * quantidade AS total, data_compra, url_imagem
    FROM comprascliente
    '''
    cursor_cliente.execute(query_cliente)
    compras_cliente = cursor_cliente.fetchall()

    # Calcular o valor total das compras
    valor_compras = sum([compra[4] for compra in compras_cliente])

    # Encontrar o produto em que o cliente gasta mais dinheiro
    if compras_cliente:
        produto_mais_custo = max(compras_cliente, key=lambda x: x[4])
    else:
        produto_mais_custo = 0  # Defina um valor padrão ou trate conforme a sua lógica

    # Consultar a soma das quantidades de cada produto
    query_total_quantidade = '''
    SELECT nome, SUM(quantidade) as total_quantidade
    FROM comprascliente
    GROUP BY nome
    '''
    cursor_cliente.execute(query_total_quantidade)
    quantidades_por_produto = cursor_cliente.fetchall()

    # Encontrar o produto menos comprado (nome e quantidade)
    if quantidades_por_produto:
        produto_menos_comprado_total = min(quantidades_por_produto, key=lambda x: x[1])
    else:
        produto_menos_comprado_total = 0

    # Encontrar o produto mais comprado (nome e quantidade)
    if quantidades_por_produto:
        produto_mais_comprado_total = max(quantidades_por_produto, key=lambda x: x[1])
    else:
        produto_mais_comprado_total = 0

    # Fechar as conexões com as bases de dados
    cursor_admin.close()
    connection_admin.close()
    cursor_cliente.close()
    connection_cliente.close()

    return render_template('profilecliente.html', stock_admin=stock_admin,
                            compras_cliente=compras_cliente,
                            valor_compras=valor_compras,
                            produto_mais_custo=produto_mais_custo,
                           produto_menos_comprado_total=produto_menos_comprado_total,
                           produto_mais_comprado_total=produto_mais_comprado_total)


# Rota para processar a compra
@app.route('/profilecliente/processar_compra', methods=['POST'])
def processar_compra_rota():
    data = request.get_json()  # Obter os dados enviados na requisição

    # Extrair os produtos do objeto de dados
    produtos = data.get('produtos', [])

    # Lógica para processar a compra e atualizar a base de dados
    processar_compra(produtos)

    obter_notificacoes()

    # Responder com uma mensagem de sucesso
    return jsonify({'message': 'Compra processada com sucesso'})


# Função para atualizar a quantidade de um produto na base de dados "stockadmin.db"
def atualizar_quantidade_produto(nome, quantidade):
    # Conectar à base de dados
    connection = sql.connect('database/stockadmin.db')
    cursor = connection.cursor()

    # Atualizar a quantidade do produto
    cursor.execute("UPDATE stockadmin SET quantidade = quantidade - ? WHERE nome = ?", (quantidade, nome))

    # Commit às alterações na base de dados
    connection.commit()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()


# Função para processar a compra
def processar_compra(produtos):
    for produto in produtos:
        nome = produto['nome']
        marca = produto['marca']
        preco = produto['preco']
        quantidade = produto['quantidade']
        total = produto['total']
        data_compra = datetime.now().strftime('%d-%m-%Y')
        url_imagem = produto['url_imagem']

        # Registar a compra na base de dados "comprascliente.db"
        registar_compra_base_dados(nome, marca, preco, quantidade, total, data_compra, url_imagem)
        # Atualizar a quantidade na base de dados "stockadmin.db"
        atualizar_quantidade_produto(nome, quantidade)


# Função para registar a compra na base de dados "comprascliente.db"
def registar_compra_base_dados(nome, marca, preco, quantidade, total, data_compra, url_imagem):
    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Inserir os dados do produto na tabela comprascliente
    cursor.execute('''
        INSERT INTO comprascliente (nome, marca, preco, quantidade, total,
        data_compra, url_imagem)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, marca, preco, quantidade, total, data_compra, url_imagem))

    # Commit às alterações na base de dados
    connection.commit()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()


@app.route('/profilecliente/estatisticas_cliente', methods=['GET'])
def estatisticas_cliente():
    return render_template('estatisticas_cliente.html')


@app.route('/profilecliente/get_graph_products', methods=['GET'])
def get_graph_products():
    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Consultar a tabela comprascliente para obter os dados das compras
    query_compras = '''
        SELECT nome, marca, preco, quantidade, preco * quantidade AS total, data_compra, url_imagem
        FROM comprascliente
    '''
    cursor.execute(query_compras)
    resultados_compras = cursor.fetchall()

    # Extrair os nomes dos produtos, quantidades compradas e valores de compra
    nomes_produtos = [compra[0] for compra in resultados_compras]
    quantidades_compradas = [compra[3] for compra in resultados_compras]
    valores_compras = [compra[4] for compra in resultados_compras]

    # Verificar se há compras antes de criar o DataFrame
    if len(nomes_produtos) == 0:
        graphJSON = None
        print("Ainda não houve compras para importar dados.")
    else:
        # Criar um DataFrame com os dados
        data = pd.DataFrame({
            'nome': nomes_produtos,
            'quantidade': quantidades_compradas,
            'valor_compra': valores_compras
        })

        # Agrupar as compras por nome do produto e somar as quantidades e valores
        data_grouped = data.groupby('nome').agg({'quantidade': 'sum', 'valor_compra': 'sum'}).reset_index()

        # Ordenar os dados pelo valor da quantidade em ordem decrescente
        data_grouped_sorted = data_grouped.sort_values('quantidade', ascending=False)

        # Selecionar apenas os três primeiros produtos mais comprados
        top_3_produtos = data_grouped_sorted.head(3)

        # Definir as cores para cada barra
        colors = {
            top_3_produtos['nome'].iloc[0]: 'green',
            top_3_produtos['nome'].iloc[1]: 'red',
            top_3_produtos['nome'].iloc[2]: 'black'
        }

        # Gerar um gráfico de barras agrupado por produto e quantidade
        fig = go.Figure(data=go.Bar(
            x=top_3_produtos['quantidade'],
            y=top_3_produtos['nome'],
            orientation='h',
            marker=dict(
                color=[colors.get(nome, 'blue') for nome in top_3_produtos['nome']]
                # Atribuir as cores corretas às barras
            )
        ))

        # Personalizar o layout do gráfico
        fig.update_layout(
            title='3 Produtos Mais Comprados',
            xaxis_title='Quantidade',
            yaxis_title='Produtos',
            yaxis=dict(autorange="reversed"),  # Inverter a ordem dos produtos no eixo y

        )

        # Converter o gráfico em formato JSON
        graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilecliente/compras_mensais_produto', methods=['GET'])
def compras_mensais_produto():
    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Consultar a tabela comprascliente para obter os dados das compras
    query_compras = '''
        SELECT nome, marca, preco, quantidade, preco * quantidade AS total, data_compra, url_imagem
        FROM comprascliente
        '''
    cursor.execute(query_compras)
    resultados_compras = cursor.fetchall()

    # Extrair os nomes dos produtos, quantidades compradas, preços e datas de compra
    nomes_produtos = [compra[0] for compra in resultados_compras]
    quantidades_compradas = [compra[3] for compra in resultados_compras]
    precos = [compra[2] for compra in resultados_compras]
    datas_compra = [pd.to_datetime(compra[5], format='%d-%m-%Y') for compra in resultados_compras]  # Extrair as datas

    # Calcular o valor das compras (preco * quantidade)
    valores_compras = [preco * quantidade for preco, quantidade in zip(precos, quantidades_compradas)]

    # Verificar se há compras antes de criar o DataFrame
    if len(nomes_produtos) == 0:
        graphJSON = None
        print("Ainda não houve compras para importar dados.")
    else:
        # Criar um DataFrame com os dados
        data = pd.DataFrame({
            'nome': nomes_produtos,
            'quantidade': quantidades_compradas,
            'valor_compra': valores_compras,
            'data_compra': datas_compra
        })

        # Extrair o ano e mês da coluna 'data_compra'
        data['mes_ano'] = data['data_compra'].dt.strftime('%B/%Y')

        # Extrair o ano e mês da coluna 'data_compra'
        data['mes_ano'] = data['data_compra'].dt.strftime('%B/%Y')

        # Agrupar as compras por ano, mês, nome do produto e somar as quantidades e valores
        data_grouped = data.groupby(['mes_ano', 'nome']).agg({'quantidade': 'sum', 'valor_compra': 'sum'}).reset_index()

        # Gerar um gráfico de barras agrupado por produto, ano e mês
        fig = px.bar(data_grouped, x='nome', y='valor_compra', color='nome',
                            labels={'valor_compra': 'Valor das Compras (€)', 'nome': 'Produtos'},
                            title=f'Compras Mensais por Produto , {data_grouped["mes_ano"].iloc[0]}')

        # Atualizar o layout do gráfico
        fig.update_layout(
            yaxis=dict(
                range=[0, max(valores_compras) * 1.5]  # Ajusta o limite superior do eixo y
            ),
            xaxis=dict(
                showticklabels=False  # Oculta as anotações no eixo x
            )
        )

        # Legenda de cores das barras
        fig.update_traces(showlegend=True)

        # Converter o gráfico em formato JSON
        graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilecliente/get_graph_current_month', methods=['GET'])
def get_graph_current_month():
    # Obter a data atual
    current_date = datetime.now().date()
    mes_atual = datetime.now().strftime('%B-%Y')

    # Obter o primeiro e último dia do mês atual
    first_day = current_date.replace(day=1)
    last_day = first_day + timedelta(days=calendar.monthrange(current_date.year, current_date.month)[1] - 1)

    # Converter as datas para o formato correto
    first_day_str = first_day.strftime('%d-%m-%Y')
    last_day_str = last_day.strftime('%d-%m-%Y')

    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Consultar a tabela comprascliente para obter os dados das compras do mês atual
    query_compras_atual = '''
        SELECT SUM(quantidade) AS total_compras, data_compra
        FROM comprascliente
        WHERE data_compra BETWEEN ? AND ?
        GROUP BY data_compra
    '''
    cursor.execute(query_compras_atual, (first_day_str, last_day_str))
    resultados_compras_atual = cursor.fetchall()

    # Extrair as datas e o total de compras
    datas_compras = [compra[1] for compra in resultados_compras_atual]
    total_compras = [compra[0] for compra in resultados_compras_atual]

    # Criar uma lista de todas as datas até a data atual
    todas_datas = [first_day + timedelta(days=x) for x in range((current_date - first_day).days + 1)]
    todas_datas_str = [data.strftime('%d-%m-%Y') for data in todas_datas]

    # Preencher com zero os dias sem compras
    for data in todas_datas_str:
        if data not in datas_compras:
            datas_compras.append(data)
            total_compras.append(0)

    # Ordenar as datas em ordem crescente
    datas_compras_sorted, total_compras_sorted = zip(*sorted(zip(datas_compras, total_compras)))

    # Remover valores negativos
    total_compras_sorted = [max(compras, 0) for compras in total_compras_sorted]

    # Gerar um gráfico de linhas para representar a evolução das compras do mês atual
    fig = go.Figure(data=go.Scatter(
        x=datas_compras_sorted,
        y=total_compras_sorted,
        mode='lines',
        marker=dict(color='purple')
    ))

    # Personalizar o layout do gráfico
    fig.update_layout(
        title=f'Evolução das Quantidades Compradas , {mes_atual}',
        xaxis_title='Data',
        yaxis_title='Quantidade Total',
        yaxis=dict(range=[-0.5, max(total_compras_sorted) * 1.1])  # Define o intervalo do eixo y
    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilecliente/get_graph_previous_month', methods=['GET'])
def get_graph_previous_month():
    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Obter a data atual
    current_date = datetime.now().date()
    first_day_of_month = current_date.replace (day=1)

    # Obter o mês e o ano do mês anterior
    previous_month = first_day_of_month - timedelta(days=1)
    previous_month_my = previous_month.strftime('%B-%Y')
    previous_month_str = previous_month.strftime('%m-%Y')

    # Obter o primeiro e último dia do mês anterior
    first_day_previous_month = previous_month.replace(day=1)
    last_day_previous_month = previous_month.replace(day=calendar.monthrange(previous_month.year, previous_month.month)[1])

    # Consulta para comparar apenas o mês e o ano do mês anterior
    query_compras = '''
        SELECT SUM(quantidade) AS total_compras, data_compra
        FROM comprascliente
        WHERE strftime('%m-%Y', data_compra) = ? 
        GROUP BY data_compra
    '''

    # Executar a consulta substituindo os parâmetros
    cursor.execute(query_compras, (previous_month_str,))
    resultados_compras = cursor.fetchall()

    # Extrair as datas e o total de compras
    datas_compras = [compra[1] for compra in resultados_compras]
    total_compras = [compra[0] for compra in resultados_compras]

    # Criar uma lista de todas as datas até a data atual
    todas_datas = [first_day_previous_month + timedelta(days=x)
                   for x in range((last_day_previous_month - first_day_previous_month).days + 1)]
    todas_datas_str = [data.strftime('%d-%m-%Y') for data in todas_datas]

    # Preencher com zero os dias sem compras
    for data in todas_datas_str:
        if data not in datas_compras:
            datas_compras.append(data)
            total_compras.append(0)

    # Ordenar as datas em ordem crescente
    datas_compras_sorted, total_compras_sorted = zip(*sorted(zip(datas_compras, total_compras)))

    # Remover valores negativos do eixo y
    total_compras_sorted_nonnegative = [max(compras, 0) for compras in total_compras_sorted]

    # Gerar um gráfico de linhas para representar a evolução das compras do mês anterior
    fig = go.Figure(data=go.Scatter(
        x=datas_compras_sorted,
        y=total_compras_sorted_nonnegative,
        mode='lines',
        marker=dict(color='red')
    ))

    # Encontrar o valor máximo dos totais de compras
    max_compras = max(total_compras_sorted_nonnegative)

    # Definir o máximo do eixo Y com margem
    y_max = max(max_compras, 1)  # Definir o mínimo como 1 se o valor máximo for 0

    # Personalizar o layout do gráfico
    fig.update_layout(
        title=f'Evolução das Quantidades Compradas , {previous_month_my}',
        xaxis_title='Data',
        yaxis_title='Quantidade Total',
        yaxis=dict(rangemode='nonnegative', range=[-0.05, y_max])
    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json()

    # Fechar a conexão com a base de dados
    cursor.close()
    connection.close()

    return jsonify(graphJSON=graphJSON)


@app.route('/profilecliente/get_graph_yearly', methods=['GET'])
def get_graph_yearly():
    # Obter a data atual e o ano correspondente
    current_date = datetime.now().date()
    current_year = current_date.year

    # Construir uma lista de todos os meses até o mês da data atual
    months = [datetime(current_year, month, 1) for month in range(1, current_date.month + 1)]
    print("MONTHS", months)

    # Conectar à base de dados
    connection = sql.connect('database/comprascliente.db')
    cursor = connection.cursor()

    # Consultar a tabela de compras para obter os totais de compras mensais
    query_compras = '''
        SELECT SUM(quantidade) AS total_compras, data_compra
        FROM comprascliente
        WHERE strftime('%Y', 'now')
    '''

    # Executar a consulta e obter os resultados
    cursor.execute (query_compras)
    resultados = cursor.fetchall ( )
    print("RES", resultados)

    # Extrair as datas de compra da lista de resultados
    datas_compras = [resultado[1] for resultado in resultados]

    # Converter as datas de compra para o formato desejado 'MM-YYYY'
    datas_compras_formatadas = [datetime.strptime (data, '%d-%m-%Y').strftime ('%m-%Y') for data in datas_compras]

    # Separar o mês e o ano em duas listas separadas
    meses_compras = [int (data.split ('-')[0]) for data in datas_compras_formatadas]
    anos_compras = [int (data.split ('-')[1]) for data in datas_compras_formatadas]

    # Inicializar uma lista para armazenar os totais de compras para cada mês
    totais_compras = [0] * len (months)

    # Preencher a lista com os totais de compras obtidos da consulta
    for mes, ano, total_compra in zip (meses_compras, anos_compras, resultados) :
        if total_compra is not None :
            idx = (ano - current_year) * 12 + (mes - 1)
            totais_compras[idx] = total_compra[0]
        else :
            idx = (ano - current_year) * 12 + (mes - 1)
            totais_compras[idx] = 0

    print ("RTP", totais_compras)

    # Definir o máximo do eixo Y
    y_max = int (max (totais_compras))

    # Gerar um gráfico de linhas para representar a evolução mensal das compras
    fig = go.Figure (data=go.Scatter (
        x=months,
        y=totais_compras,
        mode='lines',
        marker=dict (color='orange')
    ))

    # Personalizar o layout do gráfico
    fig.update_layout (
        title=f'Evolução Mensal das Quantidades Compradas, {current_year}',
        xaxis_title='Mês',
        yaxis_title='Quantidade Total',
        yaxis=dict (rangemode='nonnegative', range=[-0.1, y_max * 1.2]),
        xaxis=dict (tickformat='%b')  # Formato do rótulo do eixo X para exibir apenas o mês (ex: Jan, Fev, Mar)
    )

    # Converter o gráfico em formato JSON
    graphJSON = fig.to_json ( )

    # Fechar a conexão com a base de dados
    cursor.close ( )
    connection.close ( )

    return jsonify (graphJSON=graphJSON)


if __name__ == '__main__':
    app.run(debug=True)
