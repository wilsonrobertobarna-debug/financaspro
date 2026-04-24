import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. SUA CHAVE ORIGINAL (Cole aqui a sua lista PK_LIST completa)
PK_LIST = ["..."] 

def transferir_dados():
    # Conexão com o Google
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", "private_key": "\n".join(PK_LIST)
    }
    client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))
    
    # Abre a planilha (A mesma que você usa no App)
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws = sh.get_worksheet(0)

    # 2. LÊ O SEU ARQUIVO LOCAL
    print("Lendo o arquivo financas_bruta.csv...")
    try:
        # Tenta ler com ';' que é o padrão do seu Drive
        df = pd.read_csv('financas_bruta.csv', sep=';', encoding='latin1')
        
        # Seleciona só o que importa (Data, Valor, Tipo, Descrição)
        # Ajustamos os nomes para bater com o que está no seu arquivo
        df_limpo = df[['Data', 'Valor', 'Tipo', 'Descrição']].copy()
        
        # Envia para o Google Sheets (adicionando ao final da lista)
        dados_lista = df_limpo.values.tolist()
        ws.append_rows(dados_lista)
        
        print(f"✅ Sucesso! {len(dados_lista)} linhas transferidas para a nuvem.")
        
    except Exception as e:
        print(f"❌ Erro na transferência: {e}")

if __name__ == "__main__":
    transferir_dados()
