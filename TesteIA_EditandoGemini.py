import os
import io
import streamlit as st
import googleapiclient.http  # Importante para MediaIoBaseUpload

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredExcelLoader,
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="IA Corporativa",
    layout="centered"
)

# =========================================================
# 2. BLOCO DE SEGURANÇA (VALIDAÇÃO DE LOGIN)
# =========================================================

# Passo A: Verificar se o usuário já estava logado nesta sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# Passo B: Capturar parâmetro da URL (vindo do seu HTML)
# O Streamlit 1.30+ usa st.query_params diretamente como um dicionário
auth_param = st.query_params.get("auth")

# Passo C: Se o parâmetro for 'true', libera o acesso permanentemente nesta sessão
if auth_param == "true":
    st.session_state["logado"] = True
    # Opcional: limpa a URL para ficar bonita
    # st.query_params.clear()

# Passo D: Se após verificar a URL ele ainda não estiver logado, para a execução
if not st.session_state["logado"]:
    # CSS de fundo para a tela de erro não piscar preto
    st.markdown("<style>.stApp {background-color: #f8f9fa !important;}</style>", unsafe_allow_html=True)
    st.warning("⚠️ Acesso restrito. Por favor, realize o login.")
    st.stop()

# =========================================================
# 3. INJEÇÃO DE CSS PARA FADE-IN (Só roda se passar pela trava)
# =========================================================
st.markdown("""
    <style>
    /* Fade-in da aplicação */
    .stApp {
        
        animation: fadeInAnimation 1.5s ease-in-out forwards;
    }

    /* Box Shadow na Sidebar */
    [data-testid="stSidebar"] {
        box-shadow: 10px 0px 20px rgba(0, 0, 0, 0.15);
        border-right: 1px solid rgba(0, 0, 0, 0.05);
    }

    @keyframes fadeInAnimation {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

PASTA_DRIVE_ID = "1KHOOf3uLPaWHnDahcRNl1gIYhMT8v4rE"
ARQUIVO_CREDENCIAIS = "credentials.json"


# =========================
# ENGINE IA
# =========================
class EngineIA:
    def __init__(self):
        if not os.path.exists(ARQUIVO_CREDENCIAIS):
            st.error(f"Arquivo '{ARQUIVO_CREDENCIAIS}' não encontrado.")
            st.stop()

        self.creds = service_account.Credentials.from_service_account_file(
            ARQUIVO_CREDENCIAIS
        )
        self.service = build("drive", "v3", credentials=self.creds)
        self.embeddings = OpenAIEmbeddings()

    def atualizar_arquivo_drive(self, file_id, novo_conteudo, mime_type):
        """Atualiza o conteúdo de um arquivo existente no Google Drive."""
        media = MediaIoBaseUpload(
            io.BytesIO(novo_conteudo.encode("utf-8")),
            mimetype=mime_type,
            resumable=True
        )

        self.service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()

    def carregar_arquivos_recursivo(self, folder_id, path_nome="empresa"):
        documentos_finais = []
        page_token = None
        
        while True:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query, 
                fields="nextPageToken, files(id, name, mimeType)", 
                pageToken=page_token
            ).execute()
            
            for f in results.get('files', []):
                # 1. SE FOR PASTA: Entra nela (Recursão)
                if f['mimeType'] == 'application/vnd.google-apps.folder':
                    st.write(f"📁 Acessando pasta: {path_nome}/{f['name']}")
                    documentos_finais.extend(
                        self.carregar_arquivos_recursivo(f['id'], f"{path_nome}/{f['name']}")
                    )
                    continue

                # 2. SE FOR ARQUIVO: Define extensões e exportação
                nome_arquivo = f['name']
                ext = os.path.splitext(nome_arquivo)[1].lower()
                mime = f['mimeType']
                export_mime = None

                # Converte formatos nativos do Google (Docs/Sheets) para Office
                if mime == 'application/vnd.google-apps.document':
                    export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    ext = '.docx'
                elif mime == 'application/vnd.google-apps.spreadsheet':
                    export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    ext = '.xlsx'

                # 3. FILTRO: Só processa se for um formato suportado
                if ext in ['.pdf', '.docx', '.xlsx', '.xls'] or export_mime:
                    st.write(f"📄 Lendo arquivo: {path_nome}/{nome_arquivo}")
                    temp_path = f"temp_{f['id']}{ext}"
                    
                    try:
                        # Download
                        if export_mime:
                            request = self.service.files().export_media(fileId=f['id'], mimeType=export_mime)
                        else:
                            request = self.service.files().get_media(fileId=f['id'])
                        
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)
                        done = False
                        while not done:
                            _, done = downloader.next_chunk()
                        
                        with open(temp_path, "wb") as out:
                            out.write(fh.getvalue())

                        # 4. CARREGAMENTO (LOADERS)
                        if ext == '.pdf':
                            loader = PyPDFLoader(temp_path)
                        elif ext == '.docx':
                            loader = Docx2txtLoader(temp_path)
                        else:
                            loader = UnstructuredExcelLoader(temp_path, mode="elements")

                        docs = loader.load()
                        
                        # Adiciona metadados para a IA saber de onde veio a info
                        for d in docs:
                            d.metadata.update({
                                "setor": path_nome.split('/')[-1],
                                "origem": nome_arquivo,
                                "caminho_completo": path_nome
                            })
                        
                        documentos_finais.extend(docs)
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao ler {nome_arquivo}: {str(e)}")
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                else:
                    st.info(f"⏭️ Ignorado (formato não suportado): {nome_arquivo}")

            page_token = results.get('nextPageToken')
            if not page_token:
                break
                
        return documentos_finais

    def inicializar_sistema(self):
        documentos = self.carregar_arquivos_recursivo(PASTA_DRIVE_ID)

        if not documentos:
            st.error("Nenhum documento encontrado nas pastas.")
            st.stop()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=100
        )

        chunks = text_splitter.split_documents(documentos)

        vector_db = FAISS.from_documents(chunks, self.embeddings)

        template = """
Você é um sistema de auditoria e extração de dados corporativos de nível forense.

Sua função é extrair informações do contexto com 100 porcento de fidelidade,
sem resumir, sem omitir e sem inferir dados.

OBJETIVO:
Listar TODOS os registros relevantes sem qualquer limitação.

REGRAS:
1. Se houver 50 itens, liste TODOS os 50 em lista numerada.
2. Ignore empresas com nomes similares mas diferentes do solicitado.
3. Se não tiver certeza absoluta, marque como "NECESSITA VALIDAÇÃO".
4. Analise o metadado 'setor' para confirmar se pertence à pasta solicitada.
5. Sempre dê prioridade MAXIMA para o que o PERGUNTA esta perguntando! Obedecer Sempre, e se por algum acaso não conseguir, explicar o porque

CONTEXTO:
{context}

PERGUNTA:
{question}

RESPOSTA TÉCNICA:
"""

        return ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(model="gpt-4o", temperature=0),
            retriever=vector_db.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 40}
            ),
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            ),
            combine_docs_chain_kwargs={
                "prompt": PromptTemplate(
                    template=template,
                    input_variables=["context", "question"]
                )
            }
        )


# =========================
# INTERFACE STREAMLIT
# =========================
st.set_page_config(
    page_title="IA Corporativa",
    layout="centered"
)

with st.sidebar:
    if st.button("🔄 Recarregar"):
        st.cache_resource.clear()
        st.session_state.clear()
        st.rerun()

st.header("🏢 MindLink")

if "chat_engine" not in st.session_state:
    with st.status("Varrendo pastas e subpastas...", expanded=True):
        st.session_state.chat_engine = EngineIA().inicializar_sistema()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Pergunte algo..."):
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res = st.session_state.chat_engine.invoke(
            {"question": prompt}
        )
        st.markdown(res["answer"])

    st.session_state.messages.append(
        {"role": "assistant", "content": res["answer"]}
    )
