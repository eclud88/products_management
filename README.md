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

- Python 3.x
- Flask
- SQLite para base de dados

## 📁 Estrutura do Projeto

```bash
meu-projeto/
│
├── main.py               # Arquivo principal para execução
├── admin.py              # Lógica do admin
├── fornecedor.py         # Lógica dos fornecedores
├── cliente.py            # Lógica dos clientes
├── produtos.py           # Gestão de produtos
├── database.py           # Simulação ou ligação à base de dados
└── README.md             # Este arquivo
