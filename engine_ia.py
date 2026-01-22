import os
import io
import pandas as pd
from docx import Document
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
import openpyxl
import re

load_dotenv()

PASTA_DRIVE_ID = "1KHOOf3uLPaWHnDahcRNl1gIYhMT8v4rE"
ARQUIVO_CREDENCIAIS = "credentials.json"

class EngineIA:
    def __init__(self):
        if not os.path.exists(ARQUIVO_CREDENCIAIS):
            raise FileNotFoundError(f"Arquivo '{ARQUIVO_CREDENCIAIS}' não encontrado.")
        self.creds = service_account.Credentials.from_service_account_file(ARQUIVO_CREDENCIAIS)
        self.service = build("drive", "v3", credentials=self.creds)
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

    def carregar_arquivos_recursivo(self, folder_id, path_nome="empresa"):
        documentos_finais = []
        page_token = None
        while True:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)", pageToken=page_token).execute()
            for f in results.get('files', []):
                if f['mimeType'] == 'application/vnd.google-apps.folder':
                    documentos_finais.extend(self.carregar_arquivos_recursivo(f['id'], f"{path_nome}/{f['name']}"))
                    continue
                
                nome_arquivo = f['name']
                ext = os.path.splitext(nome_arquivo)[1].lower()
                mime = f['mimeType']
                export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if mime == 'application/vnd.google-apps.document' else None
                if not export_mime:
                    export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if mime == 'application/vnd.google-apps.spreadsheet' else None
                
                if ext in ['.pdf', '.docx', '.xlsx', '.xls'] or export_mime:
                    temp_path = f"temp_{f['id']}{ext if not export_mime else ('.docx' if 'word' in export_mime else '.xlsx')}"
                    try:
                        request_media = self.service.files().export_media(fileId=f['id'], mimeType=export_mime) if export_mime else self.service.files().get_media(fileId=f['id'])
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request_media)
                        done = False
                        while not done: _, done = downloader.next_chunk()
                        with open(temp_path, "wb") as out: out.write(fh.getvalue())
                        
                        loader = PyPDFLoader(temp_path) if temp_path.endswith('.pdf') else (Docx2txtLoader(temp_path) if temp_path.endswith('.docx') else UnstructuredExcelLoader(temp_path, mode="elements"))
                        docs = loader.load()
                        for d in docs:
                            d.page_content = f"ARQUIVO_ID: {f['id']}\nNOME_ARQUIVO: {nome_arquivo}\n{d.page_content}"
                            d.metadata.update({"file_id": f['id'], "origem": nome_arquivo})
                        documentos_finais.extend(docs)
                    finally:
                        if os.path.exists(temp_path): os.remove(temp_path)
            page_token = results.get('nextPageToken'); 
            if not page_token: break
        return documentos_finais

    def inicializar_sistema(self):
        documentos = self.carregar_arquivos_recursivo(PASTA_DRIVE_ID)
        chunks = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100).split_documents(documentos)
        vector_db = FAISS.from_documents(chunks, self.embeddings)

        # PROMPT COM INTELIGÊNCIA SEMÂNTICA
        template = """
        ### SISTEMA: Mindhub Hybrid Assistant (MHA)
        Você é a IA Central do Grupo Mindhub.

        ---
        ### 1. DICIONÁRIO DE INTENÇÕES (Interprete o usuário)
        O usuário usa linguagem natural. Converta os verbos dele para o comando técnico correto:

        **SINÔNIMOS DE "INSERIR" (Colocar em lugar específico):**
        - Se o usuário disser: "Adicione em...", "Bote no plano...", "Inclua na lista...", "Escreva abaixo de..."
        - AÇÃO TÉCNICA: `[AÇÃO: INSERIR | APÓS: "Referência" ...]`
        
        **SINÔNIMOS DE "ADICIONAR" (Colocar no final):**
        - Se o usuário disser: "Adicione no arquivo" (sem dizer onde), "Põe no fim", "Anexa aí".
        - AÇÃO TÉCNICA: `[AÇÃO: ADICIONAR ...]`

        **SINÔNIMOS DE "SUBSTITUIR" (Trocar algo):**
        - Se o usuário disser: "Mude", "Corrija", "Atualize", "Troque X por Y".
        - Se for específico (ex: "na linha do fulano"): Use `CONTEXTO`.
        - Se for geral (ex: "em todo o arquivo"): Use substituição simples.

        ---
        ### 2. PROTOCOLO DE MEMÓRIA
        - Se o usuário disser **"no mesmo arquivo"**, **"nele"**, **"continue"** ou não citar nome, USE O ARQUIVO DO TURNO ANTERIOR.
        - Ignore arquivos do contexto que não sejam o foco atual.

        ---
        ### 3. TABELA DE COMANDOS TÉCNICOS
        Gere APENAS estes comandos quando for editar:

        | Intenção Real | Comando de Saída |
        | :--- | :--- |
        | Inserir no início | `[AÇÃO: TOPO | CONTEÚDO: "texto"]` |
        | Inserir no final | `[AÇÃO: ADICIONAR | CONTEÚDO: "texto"]` |
        | Apagar tudo | `[AÇÃO: LIMPAR]` |
        | Substituir GERAL | `[AÇÃO: SUBSTITUIR | DE: "antigo" | PARA: "novo"]` |
        | **Substituir com CONTEXTO (Seguro)** | `[AÇÃO: SUBSTITUIR | DE: "valor" | PARA: "novo" | CONTEXTO: "nome ou id da linha"]` |
        | Inserir em local específico | `[AÇÃO: INSERIR | APÓS: "referencia" | CONTEÚDO: "texto"]` |

        **REGRA:** Use SEMPRE aspas duplas nos textos. Ex: `CONTEÚDO: "Texto Aqui"`.

        ---
        ### FORMATO DA RESPOSTA:
        (Se for pergunta): Responda em texto.
        (Se for ordem):
        [SUGESTÃO DE EDIÇÃO]
        Arquivo: {{nome_do_arquivo}}
        ID: {{id_do_arquivo}}
        Alteração: [AÇÃO: ...]
        Conteúdo:
        '''
        {{conteudo}}
        '''
        [FIM DA SUGESTÃO]

        HISTÓRICO: {chat_history}
        CONTEXTO: {context}
        USUÁRIO: {question}
        RESPOSTA:
        """

        return ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(model="gpt-4o", temperature=0),
            retriever=vector_db.as_retriever(search_kwargs={"k": 50}),
            memory=ConversationBufferMemory(memory_key="chat_history", input_key="question", output_key="answer", return_messages=True),
            combine_docs_chain_kwargs={"prompt": PromptTemplate(template=template, input_variables=["chat_history", "context", "question"])}
        )

    def editar_e_salvar_no_drive(self, file_id, nome_arquivo, comando_ia):
        try:
            ext = os.path.splitext(nome_arquivo)[1].lower()
            temp_path = os.path.join("/tmp", f"edit_{file_id}{ext}")
            
            # 1. BAIXA O ARQUIVO
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done: _, done = downloader.next_chunk()
            with open(temp_path, 'wb') as f: f.write(fh.getbuffer())

            # ==========================================
            # LÓGICA PARA WORD (.DOCX)
            # ==========================================
            if ext == '.docx':
                doc = Document(temp_path)
                
                if "[AÇÃO: TOPO]" in comando_ia:
                    try:
                        txt = comando_ia.split("CONTEÚDO:")[1].replace("]", "").strip()
                        doc.paragraphs[0].insert_paragraph_before(txt)
                    except: pass

                elif "[AÇÃO: LIMPAR]" in comando_ia:
                    for p in doc.paragraphs: p.text = ""

                elif "AÇÃO: SUBSTITUIR" in comando_ia:
                    try:
                        # Padrões Regex para capturar o texto, ignorando erros de formatação da IA
                        # Captura o que está depois de DE: até encontrar | ou PARA:
                        match_de = re.search(r"DE:\s*['\"]?(.*?)['\"]?\s*(?:\||PARA:)", comando_ia, re.IGNORECASE)
                        # Captura o que está depois de PARA: até encontrar | ou CONTEXTO: ou ]
                        match_para = re.search(r"PARA:\s*['\"]?(.*?)['\"]?\s*(?:\||CONTEXTO:|\])", comando_ia, re.IGNORECASE)
                        # Captura o contexto se houver
                        match_contexto = re.search(r"CONTEXTO:\s*['\"]?(.*?)['\"]?\s*(?:\||\])", comando_ia, re.IGNORECASE)

                        if match_de and match_para:
                            termo_antigo = match_de.group(1).strip()
                            termo_novo = match_para.group(1).strip()
                            contexto = match_contexto.group(1).strip() if match_contexto else None

                            print(f"DEBUG SUBSTITUIR: De '{termo_antigo}' Para '{termo_novo}' (Contexto: {contexto})")

                            for row in ws.iter_rows():
                                # Lógica de Contexto
                                if contexto:
                                    linha_texto = " ".join([str(c.value) for c in row if c.value])
                                    if contexto not in linha_texto:
                                        continue 

                                for cell in row:
                                    # Converte para string para garantir que ache números (ex: 750 virar "750")
                                    val_str = str(cell.value) if cell.value is not None else ""
                                    
                                    if termo_antigo in val_str:
                                        # Substitui mantendo o resto do conteúdo da célula
                                        cell.value = val_str.replace(termo_antigo, termo_novo)
                        else:
                            print(f"ERRO DE PARSE: Não consegui ler DE/PARA no comando: {comando_ia}")
                                    
                    except Exception as e:
                        print(f"Erro substituição Excel: {e}")

                elif "AÇÃO: INSERIR" in comando_ia:
                    try:
                        raw_ancora = comando_ia.split("APÓS:")[1].split("| CONTEÚDO:")[0].strip()
                        raw_conteudo = comando_ia.split("CONTEÚDO:")[1].split("]")[0].strip()
                        ancora = raw_ancora.strip('"').strip("'")
                        conteudo = raw_conteudo.strip('"').strip("'")
                        
                        inserido = False
                        if ancora and conteudo:
                            for i, p in enumerate(doc.paragraphs):
                                if ancora in p.text:
                                    if i + 1 < len(doc.paragraphs):
                                        doc.paragraphs[i+1].insert_paragraph_before(conteudo)
                                    else:
                                        doc.add_paragraph(conteudo)
                                    inserido = True
                                    break
                            if not inserido: doc.add_paragraph(f"\n{conteudo}")
                    except: pass

                else: # ADICIONAR (Padrão)
                    try:
                        txt = comando_ia.split("CONTEÚDO:")[1].replace("]", "").strip()
                        doc.add_paragraph(txt)
                    except: pass

                doc.save(temp_path)
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

            # ==========================================
            # LÓGICA PARA EXCEL (.XLSX / .XLSM)
            # ==========================================
            elif ext in ['.xlsx', '.xlsm']:
                is_macro = (ext == '.xlsm')
                wb = openpyxl.load_workbook(temp_path, keep_vba=is_macro)
                ws = wb.active 
                
                # 1. TOPO
                if "[AÇÃO: TOPO]" in comando_ia:
                    try:
                        txt = comando_ia.split("CONTEÚDO:")[1].replace("]", "").strip()
                        ws.insert_rows(1)
                        ws.cell(row=1, column=1, value=txt)
                    except: pass

                # 2. LIMPAR
                elif "[AÇÃO: LIMPAR]" in comando_ia:
                    ws.delete_rows(1, ws.max_row)

                # 3. SUBSTITUIR (AGORA COM CONTEXTO/ÂNCORA)
                elif "AÇÃO: SUBSTITUIR" in comando_ia:
                    try:
                        # Extração dos dados básicos
                        raw_de = comando_ia.split("DE:")[1].split("|")[0].strip()
                        raw_para = comando_ia.split("PARA:")[1].split("|")[0].replace("]", "").strip() # Remove ] caso seja o último
                        
                        termo_antigo = raw_de.strip('"').strip("'") 
                        termo_novo = raw_para.strip('"').strip("'")
                        
                        # Verifica se existe CONTEXTO
                        contexto = None
                        if "CONTEXTO:" in comando_ia:
                            raw_contexto = comando_ia.split("CONTEXTO:")[1].replace("]", "").strip()
                            contexto = raw_contexto.strip('"').strip("'")

                        for row in ws.iter_rows():
                            # Se tiver contexto, verificamos se a linha tem a palavra-chave
                            if contexto:
                                # Cria uma string com todo o conteúdo da linha para buscar o contexto
                                linha_texto = " ".join([str(c.value) for c in row if c.value])
                                if contexto not in linha_texto:
                                    continue # Pula essa linha se não tiver o contexto

                            # Faz a substituição na célula
                            for cell in row:
                                if cell.value and termo_antigo in str(cell.value):
                                    val_str = str(cell.value)
                                    cell.value = val_str.replace(termo_antigo, termo_novo)
                                    
                    except Exception as e:
                        print(f"Erro substituição Excel: {e}")

                # 4. INSERIR ESPECÍFICO
                elif "AÇÃO: INSERIR" in comando_ia:
                    try:
                        raw_ancora = comando_ia.split("APÓS:")[1].split("| CONTEÚDO:")[0].strip()
                        raw_conteudo = comando_ia.split("CONTEÚDO:")[1].split("]")[0].strip()
                        ancora = raw_ancora.strip('"').strip("'")
                        conteudo = raw_conteudo.strip('"').strip("'")
                        
                        inserido = False
                        rows = list(ws.iter_rows()) 
                        for row in rows:
                            for cell in row:
                                if cell.value and ancora in str(cell.value):
                                    idx = cell.row + 1 
                                    ws.insert_rows(idx)
                                    ws.cell(row=idx, column=1, value=conteudo)
                                    inserido = True
                                    break
                            if inserido: break
                        
                        if not inserido: ws.append([conteudo])
                    except: pass

                # 5. ADICIONAR
                else: 
                    try:
                        txt = comando_ia.split("CONTEÚDO:")[1].replace("]", "").strip()
                        ws.append([txt]) 
                    except: pass

                wb.save(temp_path)
                
                if is_macro:
                    mime_type = 'application/vnd.ms-excel.sheet.macroEnabled.12'
                else:
                    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

            else:
                return False # Formato não suportado para edição

            # 3. SOBE O ARQUIVO DE VOLTA PRO DRIVE
            media = MediaIoBaseUpload(open(temp_path, 'rb'), mimetype=mime_type, resumable=True)
            self.service.files().update(fileId=file_id, media_body=media).execute()
            
            if os.path.exists(temp_path): os.remove(temp_path)
            return True

        except Exception as e:
            print(f"Erro Geral: {e}")
            return False