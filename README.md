🚀 Desafio Técnico: Pipeline de Dados FHIR (Indra Group)
Este repositório contém a solução completa para o Desafio Técnico de Engenheiro de Dados (Especialista em HL7 FHIR), demonstrando um pipeline de dados ponta-a-ponta, desde a ingestão de dados legados (CSV) até a carga em um servidor FHIR R4, com enriquecimento semântico (RNDS e SNOMED CT).

Status: 🏆 Concluído!

🎯 Objetivo do Projeto
O objetivo principal é simular um cenário real de interoperabilidade em saúde, onde dados de pacientes de um sistema legado (arquivo patients.csv) precisam ser:

Extraídos e limpos.

Transformados para o padrão internacional (FHIR R4).

Enriquecidos com padrões nacionais (RNDS - BRIndividuo) e terminologias clínicas (SNOMED CT).

Carregados (Load) de forma resiliente em um servidor FHIR.

🏛️ Arquitetura da Solução
A solução utiliza uma arquitetura moderna, containerizada e assíncrona, garantindo desacoplamento, resiliência e escalabilidade.

``

O fluxo de dados é o seguinte:

Orquestração (Airflow): A DAG indra_fhir_pipeline inicia o processo.

Extração (Python/Pandas): A primeira tarefa (ler_csv_enviar_kafka) lê o patients.csv, realiza um ETL (Extract, Transform, Load) inicial (limpando CPFs, datas, gêneros) e produz uma mensagem JSON para cada paciente.

Mensageria (Kafka): As mensagens são publicadas no tópico patient_data. O Kafka atua como um buffer resiliente, garantindo que os dados não sejam perdidos se o servidor FHIR estiver offline.

Carga (Python/FHIR): A segunda tarefa (ler_kafka_gravar_fhir) consome as mensagens do Kafka, realiza o Enriquecimento Semântico (aplicando os perfis) e carrega os dados no HAPI FHIR Server via API REST.

🛠️ Stack de Tecnologias
Containerização: Docker e Docker Compose

Orquestração de Pipeline: Apache Airflow

Mensageria e Streaming: Apache Kafka

Servidor Clínico (CDR): HAPI FHIR (R4)

Linguagem de ETL e Scripts: Python (Pandas, kafka-python, requests)

Padrões de Interoperabilidade: HL7 FHIR R4, RNDS (BRIndividuo), SNOMED CT

🔬 Destaques Técnicos e Enriquecimento Semântico
Este pipeline vai além de uma simples carga de dados, implementando dois níveis de interoperabilidade avançada que foram solicitados como bônus.

1. Padrão RNDS (BRIndividuo)
O Resource Patient não é genérico. Ele é estruturado para seguir o perfil BRIndividuo da RNDS (Rede Nacional de Dados em Saúde).

meta.profile: O JSON de cada paciente é "carimbado" com a URL canônica do perfil.

Identificador Oficial: O CPF não é salvo de forma genérica, mas sim usando o OID oficial do Ministério da Saúde (http://www.saude.gov.br/fhir/rnds/StructureDefinition/cpf-usuario).

Nome Estruturado: O nome é quebrado em family (sobrenome) e given (nomes próprios) para maior qualidade de dados.

JSON

"meta": {
  "profile": [
    "https://fhir.rnds.saude.gov.br/StructureDefinition/BRIndividuo-1.0"
  ]
}
2. Condições Clínicas com SNOMED CT
A coluna "Observação" (ex: "Diabético", "Hipertenso") não é salva como texto livre.

Recurso Condition: Para cada condição clínica, um recurso Condition separado é criado, permitindo que o histórico de saúde do paciente seja estruturado.

Mapeamento Semântico: Através do dicionário CONDICOES_MAP, o texto "sujo" (ex: "diabetico") é traduzido para o código universal SNOMED CT (ex: 44054006 - Diabetes mellitus).

Isso é interoperabilidade semântica: qualquer sistema no mundo que entenda SNOMED agora entende o dado deste paciente, mesmo sem entender português.

``

🚀 Como Executar o Projeto
Siga estes passos para subir toda a infraestrutura e executar o pipeline.

Pré-requisitos
Docker

Docker Compose

1. Garantindo uma Execução Limpa
Como o Kafka e o HAPI FHIR (em modo de desenvolvimento) persistem dados em volumes, é crucial limpar o ambiente antes de um novo teste completo.

Bash

docker compose down -v
(O -v remove os volumes, limpando o banco do HAPI e os logs do Kafka).

2. Subindo a Infraestrutura
Com o Docker em execução, suba todos os serviços em modo "detached" (-d):

Bash

docker compose up -d
(Aguarde cerca de 2 a 3 minutos para que o Kafka e o HAPI FHIR, que são pesados, estejam totalmente prontos).

3. Acessando os Serviços
HAPI FHIR Server: http://localhost:8080

Apache Airflow: http://localhost:8081 (Login: admin / Senha: admin)

4. Executando o Pipeline
Acesse o Airflow (http://localhost:8081).

Encontre a DAG indra_fhir_pipeline.

Despause a DAG (clicando no botão "toggle" à esquerda).

Clique no botão "Play" (▶️) à direita e selecione "Trigger DAG".

``

✅ Como Validar o Sucesso
Após a DAG ficar verde (Success) no Airflow, você pode validar os dados:

1. Validação do Paciente (BRIndividuo)
Acesse o endpoint de busca de Pacientes. Você verá os dados carregados e o "total" de pacientes.

URL: http://localhost:8080/fhir/Patient

``

2. Validação das Condições (SNOMED)
Acesse o endpoint de Condições para ver os dados de diabetes, hipertensão e gestação com os códigos SNOMED.

URL: http://localhost:8080/fhir/Condition

``

3. Visualização (Opcional)
Para uma visualização mais amigável, você pode usar um cliente FHIR como o Vanya Client e apontá-lo para http://localhost:8080/fhir.

``