"""
Singleton para gerenciar a instância global do EngineIA.
Equivalente ao ia_instancia e ia_engine globais do Flask.
"""
from .services import EngineIA

class IAManager:
    _instance = None
    _ia_instancia = None
    _ia_engine = None
    _esta_atualizando = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IAManager, cls).__new__(cls)
        return cls._instance
    
    def inicializar(self):
        """Inicializa a IA (equivalente à inicialização no Flask)"""
        if self._ia_engine is None:
            self._ia_instancia = EngineIA()
            self._ia_engine = self._ia_instancia.inicializar_sistema()
        return self._ia_engine
    
    def get_engine(self):
        """Retorna a engine IA (cria se não existir)"""
        if self._ia_engine is None:
            self.inicializar()
        return self._ia_engine
    
    def get_instancia(self):
        """Retorna a instância EngineIA"""
        if self._ia_instancia is None:
            self.inicializar()
        return self._ia_instancia
    
    def forcar_atualizacao(self):
        """Força atualização da base (equivalente à rota /forçar-atualizacao)"""
        self._esta_atualizando = True
        try:
            self._ia_instancia = EngineIA()
            self._ia_engine = self._ia_instancia.inicializar_sistema()
            return True
        except Exception as e:
            raise e
        finally:
            self._esta_atualizando = False
    
    def esta_atualizando(self):
        """Retorna status de atualização"""
        return self._esta_atualizando


# Instância singleton global
ia_manager = IAManager()
