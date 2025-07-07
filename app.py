import streamlit as st
import pandas as pd
from openai import OpenAI
import os
import requests

# URL de tu webhook de n8n
webhook_url = "https://andres505.app.n8n.cloud/webhook-test/netogpt/accion"

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cargar datos
df = pd.read_csv("ventas_inventario_diario.csv", parse_dates=["fecha"])

# UI
st.set_page_config(page_title="NetoGPT – Co-Piloto Regional", layout="centered")
st.title("🧠 NetoGPT – Co-Piloto Operativo para Tiendas Hard Discount")
st.markdown("Haz una pregunta como gerente regional y obtén una respuesta con base en los datos reales de las tiendas.")

user_input = st.text_input("¿Qué deseas saber o mejorar hoy?", placeholder="Ej. ¿Qué tiendas tienen quiebre de stock hoy?")

if st.button("Responder"):
    if user_input.strip() == "":
        st.warning("Por favor, escribe una pregunta.")
    else:
        with st.spinner("Analizando datos y generando respuesta..."):
            resumen = df.groupby(["id_tienda", "producto_nombre"]).agg({
                "ventas_unidades": "sum",
                "stock_actual": "mean",
                "quiebre_stock": "sum",
                "pedido_sugerido": "mean"
            }).reset_index().head(20).to_csv(index=False)

            prompt = f"""
Eres NetoGPT, un copiloto inteligente para el gerente regional de una cadena de tiendas hard discount como Neto.

Tu rol es dar respuestas operativas, claras y accionables, basadas en datos reales. A continuación te paso un resumen de datos operativos de las tiendas:

{resumen}

La pregunta del gerente es:
{user_input}

Responde de manera profesional y concreta. Si hay riesgos, alertas o buenas prácticas que aplicar, menciónalo.
"""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )

            answer = response.choices[0].message.content.strip()

            # Trigger webhook a n8n (independientemente del contenido)
            try:
                r = requests.post(webhook_url, json={"pregunta": user_input, "respuesta": answer})
                if r.status_code != 200:
                    st.warning(f"Webhook no respondió correctamente: {r.status_code}")
            except Exception as e:
                st.warning(f"Error al enviar al webhook: {e}")

            st.success("Respuesta de NetoGPT:")
            st.write(answer)
