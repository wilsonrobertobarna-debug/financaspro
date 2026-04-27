# ... (mantenha o início do seu código igual)

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
# Verifique se a seta no topo esquerdo da tela não está fechada
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# 5. TELA PRINCIPAL
if "💰" in aba:
    # (Código da aba de Finanças aqui...)
    pass

# ABA DOS PETS (Ajustada para encontrar "Pet: Milo" e "Ração")
elif "🐾" in aba:
    st.title("🐾 Milo & Bolt")
    # Agora ele procura por qualquer item que tenha "Pet" ou "Ração" na categoria
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Ração|Milo', case=False, na=False)]
    
    if not df_pet.empty:
        st.dataframe(df_pet[['ID', 'Data', 'Valor', 'Descrição', 'Categoria', 'Status']].iloc[::-1], use_container_width=True)
    else:
        st.info("Nenhum lançamento de Pet encontrado este mês.")

# ABA DO VEÍCULO
elif "🚗" in aba:
    st.title("🚗 Meu Veículo")
    # (Código do comparador de combustível...)
    
    # Filtro ampliado para garantir que apareça Carro ou Combustível
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Carro|Combustível|Posto', case=False, na=False)]
    
    if not df_car.empty:
        st.dataframe(df_car[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)
    else:
        st.info("Nenhum lançamento de Veículo encontrado.")
