FROM apache/airflow:2.7.1

#Copiando o arquivo de requisitos para dentro da imagem
COPY requirements.txt /requirements.txt

#Instala as dependências (Java é necessário para o Spark/PySpark se formos usar, mas para este teste simples focado em Kafka/FHIR, apenas o Python basta)
USER airflow
RUN pip install --no-cache-dir -r /requirements.txt