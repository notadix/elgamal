import streamlit as st
import socket
import threading
import queue
import pandas as pd
import time

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

def mod_inverse(a, p):
    return pow(a, -1, p)

def decrypt_chunks(chunks, p, x):
    text = ""
    summary = []
    for idx, (c1, c2) in enumerate(chunks, start=1):
        s = mod_exp(c1, x, p)
        s_inv = mod_inverse(s, p)
        m = (c2 * s_inv) % p
        ch = chr(m)
        text += ch
        summary.append((idx, c1, c2, s, s_inv, m, ch))
    return text, summary

st.set_page_config(page_title="ElGamal Receiver", layout="wide")
st.markdown("<h1 style='text-align:center;'>📥 ElGamal Receiver</h1>", unsafe_allow_html=True)


p = int(st.number_input("Prime (p):", value=467, step=1))
g = int(st.number_input("Generator (g):", value=2, step=1))
x = int(st.number_input("Private Key (x):", value=127, step=1))

y = mod_exp(g, x, p)
st.info(f"Share ONLY this public key with the sender →  y = {y}")

PORT = int(st.number_input("Listening Port:", value=5000, step=1))

if "messages" not in st.session_state:
    st.session_state["messages"] = []      
if "server_started" not in st.session_state:
    st.session_state["server_started"] = False
if "inbox" not in st.session_state:
    st.session_state["inbox"] = queue.Queue()

def server_thread(port_snapshot, p_snapshot, x_snapshot, inbox_q):
    HOST = "0.0.0.0"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, port_snapshot))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                try:
                    data = conn.recv(8192).decode()
                except Exception:
                    continue
                if not data:
                    continue
                for msg_data in data.split("||MSG||"):
                    if not msg_data.strip():
                        continue
                    parts = [p for p in msg_data.split(";") if p]
                    try:
                        chunks = [tuple(map(int, part.split(","))) for part in parts]
                    except Exception:
                        continue
                    text, summary = decrypt_chunks(chunks, p_snapshot, x_snapshot)
                    inbox_q.put((text, summary))

cols = st.columns(3)
with cols[0]:
    if not st.session_state["server_started"]:
        if st.button("▶ Start Receiver"):
            t = threading.Thread(
                target=server_thread,
                args=(PORT, p, x, st.session_state["inbox"]),
                daemon=True,
                name="receiver-server",
            )
            t.start()
            st.session_state["server_started"] = True
            st.success(f"Listening on port {PORT}...")
    else:
        st.success(f"Server running on port {PORT}")

with cols[1]:
    if st.button("↻ Refresh Inbox"):
        pass  
drained = 0
while not st.session_state["inbox"].empty():
    text, summary = st.session_state["inbox"].get_nowait()
    st.session_state["messages"].append((text, summary))
    drained += 1

if drained:
    st.toast(f"Received {drained} new message(s)")

st.subheader("Received Messages")
if not st.session_state["messages"]:
    st.write("No messages yet.")
else:
    for text, summary in reversed(st.session_state["messages"]):
        st.write(f"### Message: **{text}**")

        df = pd.DataFrame(summary, columns=["Chunk", "c1", "c2", "s", "s⁻¹", "m", "Char"])
        st.dataframe(df, use_container_width=True)
