import streamlit as st
import socket
import random
import pandas as pd
import math

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
    * {
        font-family: 'Poppins', sans-serif !important;
    }

    .main {
        background-color: #0b0618 !important;
    }

    html, body {
        background-color: #0b0618 !important;
        color: #e9e6ff !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #120a27 !important;
        border-right: 1px solid #3b2f68 !important;
    }

    /* Text Inputs */
    .stTextInput input, .stNumberInput input, textarea {
        background-color: #1a1333 !important;
        border: 1px solid #6a4df4 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 8px !important;
        transition: 0.3s;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border: 1px solid #9d7aff !important;
        box-shadow: 0 0 8px #7b5bff !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #6a4df4, #8a6eff) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 0.6rem 1.3rem !important;
        font-weight: 500 !important;
        transition: 0.25s ease-in-out;
        box-shadow: 0 0 6px rgba(120,70,255,0.5);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 16px rgba(145,105,255,0.85);
    }

    /* Keep success messages GREEN */
    .stSuccess {
        background-color: rgba(0, 255, 140, 0.15) !important;
        border-left: 4px solid #00ff9a !important;
        color: #baffdd !important;
    }

    /* DataFrame Styling */
    .stDataFrame, .dataframe {
        background-color: #110a26 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    .dataframe th {
        background-color: #6a4df4 !important;
        color: white !important;
        font-weight: 500 !important;
    }
    .dataframe td {
        background-color: #1a1333 !important;
        border-color: #3d2f65 !important;
    }

    /* Titles Glow */
    h1, h2, h3 {
        color: #c9baff !important;
        text-shadow: 0 0 10px #7a5cff, 0 0 20px #5a3bcc;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: #6a4df4;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

def mod_exp(a, b, p):
    result = 1
    a %= p
    while b > 0:
        if b % 2 == 1:
            result = (result * a) % p
        b //= 2
        a = (a * a) % p
    return result

def max_bytes_per_chunk(p):
    return max(1, int(math.log2(p) // 8))

def encrypt(message, p, g, y):
    msg_bytes = message.encode("utf-8")
    size = max_bytes_per_chunk(p)
    chunks = [msg_bytes[i:i+size] for i in range(0, len(msg_bytes), size)]

    ct = []
    details = []
    for idx, part in enumerate(chunks, start=1):
        m = int.from_bytes(part, "big")
        k = random.randint(2, p - 2)
        c1 = mod_exp(g, k, p)
        c2 = (m * mod_exp(y, k, p)) % p
        ct.append((c1, c2))
        details.append((idx, part, m, k, c1, c2))
    return ct, details

st.set_page_config(page_title="ElGamal Sender", layout="wide")
st.markdown("<h1 style='text-align:center;'>📤 ElGamal Sender</h1>", unsafe_allow_html=True)

p = int(st.number_input("Prime (p):", value=467, step=1))
g = int(st.number_input("Generator (g):", value=2, step=1))
y = int(st.number_input("Receiver Public Key (y):", value=132, step=1))

HOST = st.text_input("Receiver IP:", "127.0.0.1")
PORT = int(st.number_input("Receiver Port:", value=5000, step=1))

message = st.text_input("Message:", "hi")

send = st.button("Send")

if send:
    try:
        ct, details = encrypt(message, p, g, y)
        packet = ";".join([f"{c1},{c2}" for c1, c2 in ct]) 

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(packet.encode())

        st.success("✅ Message Sent Successfully")

        df = pd.DataFrame(details, columns=[
            "Chunk",
            "Bytes",
            "m (int value)",
            "k (random)",
            "c1 = g^k mod p",
            "c2 = (m * y^k) mod p"
        ])

        st.subheader("🔐 Encryption Details (Sender Side)")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")
