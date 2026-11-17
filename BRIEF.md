# Projeto 2 — Pipeline de Limpeza, Validação e Automação de Dados

## Contexto do Portfólio
Este projeto faz parte do portfólio profissional de **Luis Henriques Figueiredo** (Desenvolvedor Backend/Full Stack & Dados/Automação, formado em ADS, 2 anos de experiência na Bradesco Seguros, inglês fluente).
Ele traduz em código Python puro o principal case da experiência na Bradesco Seguros: automatizar o tratamento, limpeza e validação de dados que antes levava horas para rodar em segundos.

## Stack Obrigatória
- **Linguagem:** Python 3
- **API:** FastAPI + Uvicorn + Pydantic
- **Processamento de Dados:** Pandas
- **Banco de Dados:** SQLite / PostgreSQL (SQLAlchemy ou SQL direto)
- **Testes:** Pytest
- **Empacotamento:** Dockerfile + `README.md` completo em inglês (com benchmark e instruções de execução)

## Funcionalidades Principais
1. Upload/ingestão de arquivos CSV/planilhas com dados sujos (duplicatas, datas inconsistentes, nulos, formatação errada).
2. Motor de validação e limpeza com relatório de linhas aceitas, corrigidas e rejeitadas.
3. Persistência dos dados limpos e logs de auditoria em banco SQL.
4. Endpoints REST no FastAPI (com Swagger em `/docs`) para processar arquivos, consultar logs e exportar dados limpos (que também servirão de base para o Projeto 4 de Power BI).
5. Suíte de testes automatizados com Pytest.
