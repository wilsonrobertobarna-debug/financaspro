@st.cache_resource
def conectar_google():
    try:
        # 1. Remove cabeçalhos e qualquer caractere invisível
        miolo = CHAVE_BRUTA.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
        # Remove TUDO que não for base64 (letras, números, +, /) - removemos o '=' aqui para recalcular
        miolo_limpo = re.sub(r'[^a-zA-Z0-9+/]', '', miolo)
        
        # 2. CONSERTO DO PADDING (O segredo do erro InvalidPadding)
        # O base64 precisa ser múltiplo de 4. Adicionamos '=' até ficar correto.
        while len(miolo_limpo) % 4 != 0:
            miolo_limpo += '='
        
        # 3. Reconstrói a chave em blocos de 64 caracteres
        linhas = [miolo_limpo[i:i+64] for i in range(0, len(miolo_limpo), 64)]
        chave_final = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(linhas) + "\n-----END PRIVATE KEY-----\n"

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        creds_info = {
            "type": "service_account",
            "project_id": "financaspro-wilson",
            "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
            "private_key": chave_final
        }
        
        return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))
    except Exception as e:
        st.error(f"Erro Crítico na Chave: {e}")
        return None
