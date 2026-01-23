# 🚀 Pipeline de Dados FHIR 

**Date:** Novembro 2025

---

## 🎯 Objetivo

Este repositório contém a solução completa para o Desafio Técnico de Engenheiro de Dados (Especialista em HL7 FHIR), demonstrando um pipeline de dados ponta-a-ponta, desde a ingestão de dados legados (CSV) até a carga em um servidor FHIR R4, com enriquecimento semântico (RNDS e SNOMED CT).


O objetivo principal é simular um cenário real de interoperabilidade em saúde, onde dados de pacientes de um sistema legado (arquivo `patients.csv`) precisam ser:

- Extraídos e limpos  
- Transformados para o padrão internacional (FHIR R4)  
- Enriquecidos com padrões nacionais (RNDS – BRIndividuo) e terminologias clínicas (SNOMED CT)  
- Carregados (Load) de forma resiliente em um servidor FHIR

---

## 🏛️ Solução e Arquitetura

A solução utiliza uma arquitetura moderna, containerizada e assíncrona, garantindo desacoplamento, resiliência e escalabilidade.

### 🔄 Data Flow Overview

O fluxo de dados é o seguinte:

1. **Orquestração (Airflow)**  
   A DAG `indra_fhir_pipeline` inicia o processo.

2. **Extração (Python / Pandas)**  
   A tarefa `ler_csv_enviar_kafka` lê o arquivo `patients.csv`, realiza o ETL inicial (limpeza de CPF, datas, gêneros) e produz uma mensagem JSON por paciente.

3. **Mensageria (Kafka)**  
   As mensagens são enviadas para o tópico `patient_data`.  
   O Kafka atua como buffer resiliente caso o servidor FHIR esteja offline.

4. **Carga (Python / FHIR)**  
   A tarefa `ler_kafka_gravar_fhir` consome mensagens do Kafka, realiza o enriquecimento semântico (perfis RNDS + SNOMED CT) e carrega os dados no HAPI FHIR Server.

---

## 🛠️ Tech Stack

- **Containerização:** Docker & Docker Compose  
- **Orquestração de Pipeline:** Apache Airflow  
- **Mensageria/Streaming:** Apache Kafka  
- **Servidor Clínico (CDR):** HAPI FHIR (R4)  
- **ETL e Scripts:** Python (Pandas, kafka-python, requests)  
- **Interoperabilidade:** HL7 FHIR R4, RNDS (BRIndividuo), SNOMED CT

---

## 🔬 Destaques Técnicos & Enriquecimento Semântico

Este pipeline vai além de uma simples carga, implementando interoperabilidade clínica avançada:

---

### **1. Padrão RNDS (BRIndividuo)**

O recurso **Patient** segue estritamente o perfil oficial BRIndividuo da RNDS.

- `meta.profile`: cada paciente é carimbado com o perfil canônico  
- CPF usando o OID oficial:  
  `http://www.saude.gov.br/fhir/rnds/StructureDefinition/cpf-usuario`  
- Nome estruturado em `family` e `given`

```json
"meta": {
  "profile": [
    "https://fhir.rnds.saude.gov.br/StructureDefinition/BRIndividuo-1.0"
  ]
}
```

---

### **2. Condições Clínicas com SNOMED CT**

A coluna **Observação** (ex: "Diabético", "Hipertenso") é mapeada semanticamente usando SNOMED CT.

- Criado um recurso **Condition** para cada condição clínica  
- Mapeamento via `CONDICOES_MAP`  
- Exemplo:  
  - "diabetico" → **44054006 – Diabetes mellitus**

➡️ Isso garante **interoperabilidade semântica total**, compreendida mundialmente.

---

## 🚀 Rodando o Projeto

### ✅ Pré-requisitos

- Docker  
- Docker Compose

---

### **1. Limpar ambiente (para execução do zero)**

```bash
docker compose down -v
```

Remove volumes, limpando banco do HAPI e logs do Kafka.

---

### **2. Subir toda a infraestrutura**

```bash
docker compose up -d
```

Aguarde **2–3 min** para Kafka e HAPI FHIR ficarem prontos.

---

### **3. Acessar os serviços**

- **HAPI FHIR Server:** http://localhost:8080  
- **Apache Airflow:** http://localhost:8081  
  - Login: `admin`  
  - Senha: `admin`

---

### **4. Executar o Pipeline**

1. Acesse o Airflow  
2. Encontre a DAG `indra_fhir_pipeline`  
3. Despause  
4. Clique em **Trigger DAG** (▶️)

---

## ✅ Validação dos Dados

### **1. Pacientes (BRIndividuo)**  
http://localhost:8080/fhir/Patient

<img width="953" height="650" alt="json_pac" src="https://github.com/user-attachments/assets/0267b2c1-3edf-4267-a4c3-510e8c38265c" />


---

### **2. Condições (SNOMED CT)**  
http://localhost:8080/fhir/Condition

<img width="1003" height="683" alt="json_cond" src="https://github.com/user-attachments/assets/c81a5d48-d333-427f-b051-4d955bd6af50" />


---

### **3. Visualização opcional**  
Use o **Vanya Client** apontando para:  
http://localhost:8080/fhir

<img width="1028" height="830" alt="pacientes" src="https://github.com/user-attachments/assets/80bc3eb6-761c-40ab-a50b-dd91ddb305d2" />

<img width="1029" height="832" alt="Cond" src="https://github.com/user-attachments/assets/d530980a-1df0-4fa1-a452-dd055a6790ff" />


---

## 🎉 Finalizado!


