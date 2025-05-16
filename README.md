# 🛒 Sistema de Gestão de Produtos

Este é um projeto Python para gestão de produtos com diferentes tipos de utilizadores: **Admin**, **Fornecedores** e **Clientes**.
O sistema permite a administração de produtos, bem como interações específicas para cada tipo de utilizador.

## ✨ Funcionalidades

### 👤 Admin
- Gerir todos os produtos;
- Gerir contas de fornecedores e clientes;
- Visualizar estatísticas gerais do sistema.

### 🚚 Fornecedor
- Adicionar novos produtos;
- Atualizar ou remover produtos próprios;
- Ver lista de produtos ativos.

### 🛍️ Cliente
- Consultar catálogo de produtos;
- Realizar pedidos;
- Ver histórico de compras.

## ⚙️ Tecnologias utilizadas

- Python 3.13
- Flask
- SQLite para base de dados

## 📁 Estrutura do Projeto

```bash
products_management/
│
├── app.py                           # Arquivo principal para execução
├── comprasadmin.db                  # Base de dados das compras do admin
├── comprascliente.db                # Base de dados das compras do cliente
├── estatisticas_admin.html          # Arquivo das estatísticas do admin
├── estatisticas_cliente.html        # Arquivo das estatísticas do cliente
├── estatisticas_fornecedor.html     # Arquivo principal para execução
├── profileadmin.py                  # Lógica do admin
├── profilefornecedor.py             # Lógica dos fornecedores
├── profilecliente.py                # Lógica dos clientes
├── login.html                       # Página de login
├── logindata.db                     # Base de dados do login
├── profilecliente.py                # Lógica dos clientes
├── gestaodeprodutos.db              # Gestão de produtos
├── stockadmin.db                    # Base de dados do stock do admin
├── style.css                        # Arquivo de estilos do projeto
├── sobre_nos_fornecedores.html      # Página sobre os fornecedores
└── README.md                        # Este arquivo
