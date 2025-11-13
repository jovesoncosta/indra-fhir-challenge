from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import json
import requests
from kafka import KafkaProducer, KafkaConsumer
import re

#CONFIGURAÇÕES GLOBAIS
KAFKA_TOPIC = 'patient_data'
KAFKA_SERVER = 'kafka:29092'
FHIR_SERVER_URL = 'http://hapi-fhir:8080/fhir'
SNOMED_SYSTEM_URL = "http://snomed.info/sct"

default_args = {
    'owner': 'candidato_indra',
    'start_date': datetime(2023, 1, 1),
    'retries': 0
}

#MAPEAMENTO DE CÓDIGOS 
CONDICOES_MAP = {
    "gestante": {
        "code": "77386006",
        "display": "Gestante (achado)"
    },
    "diabético": {
        "code": "44054006",
        "display": "Diabetes mellitus (transtorno)"
    },
    "diabetico": { 
        "code": "44054006",
        "display": "Diabetes mellitus (transtorno)"
    },
    "hipertenso": {
        "code": "38341003",
        "display": "Hipertensão (transtorno)"
    }
}


#LER O CSV, TRANSFORMAR E ENVIAR PARA O KAFKA
def produce_csv_to_kafka():
    print("--- Lendo CSV e Transformando Dados ---")
    
    try:
        df = pd.read_csv('/opt/airflow/data/patients.csv', encoding='latin1', sep=None, engine='python')
    except FileNotFoundError:
        print("ERRO: Arquivo 'patients.csv' não encontrado em /opt/airflow/data/")
        raise
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        raise

    df.columns = df.columns.str.strip().str.lower()
    print(f"Colunas detectadas: {df.columns.tolist()}")

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_SERVER],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )
    
    count = 0
    for _, row in df.iterrows():
        try:
            #1-ID(CPF)
            raw_cpf = str(row.get('cpf', ''))
            clean_id = re.sub(r'\D', '', raw_cpf)
            if not clean_id:
                clean_id = f"gerado_{count}"

            #2-Gênero
            raw_gender = str(row.get('gênero', '')).lower()
            if 'masc' in raw_gender:
                fhir_gender = 'male'
            elif 'fem' in raw_gender:
                fhir_gender = 'female'
            else:
                fhir_gender = 'unknown'

            #3-Data de Nascimento
            raw_dob = str(row.get('data de nascimento', ''))
            try:
                dt_obj = pd.to_datetime(raw_dob, dayfirst=True)
                fhir_dob = dt_obj.strftime('%Y-%m-%d')
            except:
                fhir_dob = None

            #4-Monta o JSON
            patient_data = {
                "id": clean_id,
                "nome": row.get('nome', 'Sem Nome'),
                "genero": fhir_gender,
                "nascimento": fhir_dob,
                "observacao": row.get('observação', None) 
            }
            
            if pd.isna(patient_data['observacao']):
                patient_data['observacao'] = None

            producer.send(KAFKA_TOPIC, value=patient_data)
            count += 1
            print(f"Enviado: {patient_data['nome']} (ID: {clean_id})")

        except Exception as e:
            print(f"Erro ao processar linha: {row}. Erro: {e}")

    producer.flush()
    print(f"--- Total processado: {count} ---")


#LER DO KAFKA E GRAVAR PACIENTE + CONDIÇÕES NO FHIR
def consume_kafka_to_fhir():
    print("--- Consumindo Kafka -> FHIR (Padrão RNDS + Conditions) ---")
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_SERVER],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='fhir_importer_brindividuo_conditions_v1',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        consumer_timeout_ms=10000
    )
    
    processed_patients = 0
    processed_conditions = 0
    
    for message in consumer:
        data = message.value
        nome_completo = data.get('nome', 'DESCONHECIDO')
        
        if not data.get('nascimento'):
            continue

        #CRIAÇÃO DO PACIENTE (BRIndividuo) 
        partes_nome = nome_completo.split()
        family = partes_nome[-1] if len(partes_nome) > 1 else nome_completo
        given = partes_nome[:-1] if len(partes_nome) > 1 else []

        patient = {
            "resourceType": "Patient",
            "meta": {"profile": ["https://fhir.rnds.saude.gov.br/StructureDefinition/BRIndividuo-1.0"]},
            "identifier": [{
                "use": "official",
                "system": "http://www.saude.gov.br/fhir/rnds/StructureDefinition/cpf-usuario", 
                "value": str(data.get('id', ''))
            }],
            "name": [{"use": "official", "text": nome_completo, "family": family, "given": given}],
            "gender": data.get('genero', 'unknown'),
            "birthDate": data['nascimento']
        }
        
        try:
            res_pat = requests.post(f"{FHIR_SERVER_URL}/Patient", json=patient)
            
            if res_pat.status_code in [200, 201]:
                fhir_id = res_pat.json().get('id')
                print(f"✅ Paciente Criado: {nome_completo} (ID: {fhir_id})")
                processed_patients += 1

                #CRIAÇÃO DAS CONDIÇÕES 
                observacoes_raw = data.get('observacao')
                
                if observacoes_raw:
                    condicoes_texto = observacoes_raw.split('|')
                    
                    for texto in condicoes_texto:
                        texto_limpo = texto.strip().lower()
                        
                        if texto_limpo in CONDICOES_MAP:
                            mapa = CONDICOES_MAP[texto_limpo]
                            
                            condition = {
                                "resourceType": "Condition",
                                "clinicalStatus": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                        "code": "active",
                                        "display": "Active"
                                    }]
                                },
                                "code": {
                                    "coding": [{
                                        "system": SNOMED_SYSTEM_URL,
                                        "code": mapa['code'],
                                        "display": mapa['display']
                                    }],
                                    "text": texto_limpo.capitalize()
                                },
                                "subject": {
                                    "reference": f"Patient/{fhir_id}"
                                }
                            }
                            
                            res_cond = requests.post(f"{FHIR_SERVER_URL}/Condition", json=condition)
                            if res_cond.status_code in [200, 201]:
                                print(f"  -> 🩺 Condição Registrada: {mapa['display']}")
                                processed_conditions += 1
                            else:
                                print(f"  -> ❌ Erro ao salvar Condição: {res_cond.text}")
            else:
                print(f"❌ Erro FHIR (Paciente): {res_pat.status_code} - {res_pat.text}")
        except Exception as ex:
            print(f"Erro de conexão: {ex}")

    print(f"--- Fim. Pacientes: {processed_patients} | Condições: {processed_conditions} ---")


#DEFINIÇÃO DA DAG
with DAG(
    'indra_fhir_pipeline', 
    default_args=default_args, 
    schedule_interval='@once', 
    catchup=False
) as dag:
    
    t1 = PythonOperator(
        task_id='ler_csv_enviar_kafka',
        python_callable=produce_csv_to_kafka 
    )
    
    t2 = PythonOperator(
        task_id='ler_kafka_gravar_fhir',
        python_callable=consume_kafka_to_fhir 
    )

    t1 >> t2