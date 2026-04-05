"""
Módulo de memoria de conversación usando Firestore.
Reemplaza la memoria de N8N con persistencia en la nube.
"""
from google.cloud import firestore
from datetime import datetime
import pytz
from typing import List, Optional
from ..config import get_settings


class FirestoreConversationMemory:
    """
    Gestión de memoria de conversación usando Firestore.

    Mantiene un historial de mensajes por usuario,
    persistido en Cloud Firestore para escalabilidad.
    """

    def __init__(self, user_id: int):
        """
        Inicializa la memoria para un usuario específico.

        Args:
            user_id: ID de Telegram del usuario
        """
        self.settings = get_settings()
        self.db = firestore.Client(project=self.settings.project_id)
        self.user_id = str(user_id)
        self.collection_name = self.settings.firestore_collection
        self.window_size = self.settings.memory_window_size
        self._messages: List[dict] = []
        self._loaded = False

    def _get_doc_ref(self) -> firestore.DocumentReference:
        """Retorna la referencia al documento del usuario."""
        return self.db.collection(self.collection_name).document(self.user_id)

    def load(self) -> List[dict]:
        """
        Carga el historial de conversación desde Firestore.

        Returns:
            Lista de mensajes del historial
        """
        if self._loaded:
            return self._messages

        doc_ref = self._get_doc_ref()
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            self._messages = data.get("messages", [])
            # Mantener solo los últimos N mensajes
            if len(self._messages) > self.window_size:
                self._messages = self._messages[-self.window_size:]
        else:
            self._messages = []

        self._loaded = True
        return self._messages

    def save(self) -> None:
        """Guarda el historial de conversación en Firestore."""
        doc_ref = self._get_doc_ref()
        tz = pytz.timezone(self.settings.default_timezone)

        doc_ref.set({
            "messages": self._messages,
            "last_updated": datetime.now(tz),
            "message_count": len(self._messages)
        }, merge=True)

    def add_message(self, role: str, content: str) -> None:
        """
        Añade un mensaje al historial.

        Args:
            role: "user" o "assistant"
            content: Contenido del mensaje
        """
        tz = pytz.timezone(self.settings.default_timezone)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(tz).isoformat()
        }

        self._messages.append(message)

        # Mantener el tamaño de la ventana
        if len(self._messages) > self.window_size:
            self._messages = self._messages[-self.window_size:]

    def get_messages(self) -> List[dict]:
        """
        Retorna los mensajes en formato para LangChain.

        Returns:
            Lista de mensajes con formato {"role": ..., "content": ...}
        """
        return [{"role": m["role"], "content": m["content"]} for m in self._messages]

    def clear(self) -> None:
        """Limpia el historial de conversación."""
        self._messages = []
        self.save()

    def get_last_user_message(self) -> Optional[str]:
        """
        Obtiene el último mensaje del usuario.

        Returns:
            Contenido del último mensaje del usuario o None
        """
        for message in reversed(self._messages):
            if message["role"] == "user":
                return message["content"]
        return None

    def get_context_summary(self) -> str:
        """
        Genera un resumen del contexto de la conversación.

        Returns:
            Resumen del contexto actual
        """
        user_messages = [m for m in self._messages if m["role"] == "user"]
        assistant_messages = [m for m in self._messages if m["role"] == "assistant"]

        return (
            f"Contexto de conversación:\n"
            f"- Mensajes del usuario: {len(user_messages)}\n"
            f"- Respuestas del asistente: {len(assistant_messages)}\n"
            f"- Último mensaje: {self._messages[-1]['content'][:100] if self._messages else 'N/A'}"
        )


class MemoryManager:
    """
    Gestor centralizado de memorias por usuario.
    Mantiene caché de memorias en memoria para mejor rendimiento.
    """

    def __init__(self):
        self._memories: dict = {}

    def get_memory(self, user_id: int) -> FirestoreConversationMemory:
        """
        Obtiene o crea la memoria para un usuario.

        Args:
            user_id: ID de Telegram del usuario

        Returns:
            Instancia de FirestoreConversationMemory
        """
        if user_id not in self._memories:
            self._memories[user_id] = FirestoreConversationMemory(user_id)
            self._memories[user_id].load()
        return self._memories[user_id]

    def save_all(self) -> None:
        """Guarda todas las memorias en caché."""
        for memory in self._memories.values():
            memory.save()

    def clear_cache(self) -> None:
        """Limpia el caché de memorias."""
        self._memories.clear()


# Instancia global del gestor de memoria
memory_manager = MemoryManager()