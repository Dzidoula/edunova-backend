import time
from typing import Dict, List, Optional

try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from app.services.error_analysis import (
    ADAPTATION_STRATEGIES,
    ERROR_LABELS,
    ErrorAnalysis,
    ErrorType,
    classify_error_heuristic,
)

SYSTEM_PROMPT = """Tu es EduNova, un tuteur IA patient et clair.
Tu travailles à partir des documents de l'élève et de sa mémoire pédagogique.

Règles :
1. Base-toi sur le document fourni. N'invente pas de contenu absent.
2. Explique simplement, étape par étape, niveau lycée / début université.
3. Si l'élève ne comprend pas, reformule + donne un exemple concret.
4. Pour les exercices : guide, pose des questions, donne des indices. Ne donne pas toute la solution d'un coup.
5. Réponds toujours en français, de façon concise (1 à 3 paragraphes sauf demande contraire).
6. Si une MÉMOIRE PÉDAGOGIQUE est fournie (erreurs passées, notions fragiles, stratégies qui ont marché),
   utilise-la pour personnaliser l'aide : rappelle les pièges connus, évite de répéter une explication
   qui n'a pas fonctionné, renforce ce qui a déjà aidé l'élève.
7. Si une ANALYSE D'ERREUR ou un STYLE D'EXPLICATION ADAPTÉ est fourni, suis ce style en priorité.
"""


def format_api_error(err: Exception) -> str:
    msg = str(err).lower()
    status = getattr(err, "status_code", None) or getattr(err, "code", None)
    if status is None and hasattr(err, "response"):
        try:
            status = getattr(err.response, "status_code", None)
        except Exception:
            pass

    if status == 401 or "unauthorized" in msg or "invalid api key" in msg or "incorrect api key" in msg:
        return (
            "⚠️ Clé API invalide ou expirée (erreur 401).\n"
            "Va dans Paramètres, vérifie ta clé Groq/OpenAI, puis enregistre à nouveau."
        )
    if status == 403 or "forbidden" in msg or "permission" in msg:
        return (
            "⚠️ Accès refusé par l'API (erreur 403).\n"
            "Ta clé n'a peut-être pas les droits nécessaires. Régénère une clé sur console.groq.com."
        )
    if status == 429 or "rate limit" in msg or "too many requests" in msg:
        return (
            "⚠️ Trop de requêtes (limite atteinte — erreur 429).\n"
            "Attends 20–60 secondes puis réessaie. Le plan gratuit Groq a des limites par minute."
        )
    if status in (500, 502, 503) or "server" in msg:
        return "⚠️ Le service IA est temporairement indisponible (erreur serveur).\nRéessaie dans quelques instants."
    if "timeout" in msg or "timed out" in msg:
        return "⚠️ Délai dépassé : l'IA met trop de temps à répondre.\nVérifie ta connexion internet et réessaie."
    if "connection" in msg or "network" in msg or "connect" in msg:
        return "⚠️ Problème de connexion internet.\nVérifie ton réseau puis réessaie."
    if "model" in msg and ("not found" in msg or "does not exist" in msg):
        return "⚠️ Modèle introuvable.\nDans Paramètres, choisis un modèle valide (ex: llama-3.3-70b-versatile)."
    return f"⚠️ Erreur API : {err}\n\nTu peux réessayer ou utiliser le mode local (sans clé)."


class Tutor:
    def __init__(self, api_key: str, api_base: str, model: str):
        self.model = model or "llama-3.3-70b-versatile"
        self.client = None
        self.available = False
        key = (api_key or "").strip()
        if HAS_OPENAI and key:
            try:
                self.client = OpenAI(api_key=key, base_url=(api_base or "").strip(), timeout=45.0)
                self.available = True
            except Exception as e:
                print(f"[IA] {e}")

    def analyze_error(
        self, message: str, notion: str = "", subject: str = "", learner_work: str = ""
    ) -> ErrorAnalysis:
        etype = classify_error_heuristic(message + " " + learner_work, notion)
        source = "heuristic"

        summary = f"Type détecté : {ERROR_LABELS[etype]}."

        if self.available and self.client and (message or learner_work):
            try:
                prompt = (
                    "Classe l'erreur de l'élève en UNE catégorie parmi : "
                    "concept, method, calculation, reading, careless, unknown.\n"
                    f"Notion : {notion or '—'}\n"
                    f"Message élève : {message[:400]}\n"
                    f"Travail élève : {learner_work[:400]}\n"
                    "Réponds au format exact :\nTYPE: <categorie>\nRESUME: <une phrase>"
                )
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Tu analyses des erreurs scolaires. Réponses très courtes."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=120,
                )
                text = (r.choices[0].message.content or "").strip()
                for line in text.splitlines():
                    if line.upper().startswith("TYPE:"):
                        raw = line.split(":", 1)[-1].strip().lower()
                        for et in ErrorType:
                            if et.value in raw:
                                etype = et
                                source = "llm"
                                break
                    if line.upper().startswith("RESUME:"):
                        summary = line.split(":", 1)[-1].strip() or summary
                        source = "llm"
            except Exception as e:
                print(f"[analyse erreur] {e}")

        strategy = ADAPTATION_STRATEGIES.get(etype, ADAPTATION_STRATEGIES[ErrorType.UNKNOWN])
        return ErrorAnalysis(
            error_type=etype, notion=notion or "", subject=subject or "", summary=summary, strategy=strategy, source=source
        )

    def reply(
        self,
        message: str,
        document_text: Optional[str],
        document_title: Optional[str],
        retrieved_chunks: List[str],
        pedagogical_snippets: List[str],
        history: List[Dict],
        active_adaptation: Optional[str],
    ) -> str:
        if self.available and self.client:
            return self._llm(message, document_text, document_title, retrieved_chunks, pedagogical_snippets, history, active_adaptation)
        return self._fallback(message, document_text, document_title)

    def _llm(
        self,
        message: str,
        document_text: Optional[str],
        document_title: Optional[str],
        retrieved_chunks: List[str],
        pedagogical_snippets: List[str],
        history: List[Dict],
        active_adaptation: Optional[str],
    ) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if active_adaptation:
            messages.append({"role": "system", "content": active_adaptation})

        if retrieved_chunks:
            joined = "\n\n---\n\n".join(retrieved_chunks)
            title_part = f" « {document_title} »" if document_title else ""
            messages.append({
                "role": "system",
                "content": f"Passages pertinents du document{title_part} (base de connaissances) :\n\n{joined[:5000]}",
            })
        elif document_text and len(document_text.strip()) > 40:
            messages.append({
                "role": "system",
                "content": f"Document : « {document_title} ».\nContenu :\n{document_text[:6000]}",
            })

        if pedagogical_snippets:
            messages.append({
                "role": "system",
                "content": "MÉMOIRE PÉDAGOGIQUE de cet élève (expériences passées pertinentes) :\n\n"
                + "\n\n".join(pedagogical_snippets[:5]),
            })

        for h in history[-10:]:
            messages.append(h)
        messages.append({"role": "user", "content": message})

        last_err = None
        for attempt in range(3):
            try:
                r = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.4, max_tokens=900
                )
                return r.choices[0].message.content.strip()
            except Exception as e:
                last_err = e
                err_s = str(e).lower()
                status = getattr(e, "status_code", None)
                if status == 429 or "rate limit" in err_s:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break

        friendly = format_api_error(last_err) if last_err else "⚠️ Erreur inconnue."
        return friendly + "\n\n" + self._fallback(message, document_text, document_title)

    def translate(self, text: str, target_lang: str = "français") -> str:
        text = (text or "").strip()
        if not text:
            return "Aucun texte à traduire."
        excerpt = text[:5000]
        prompt = f"Traduis le texte suivant en {target_lang}. Donne uniquement la traduction, sans commentaire.\n\n{excerpt}"
        if self.available and self.client:
            try:
                r = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Tu es un traducteur précis pour contenus scolaires. Traduis fidèlement."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=1200,
                )
                return r.choices[0].message.content.strip()
            except Exception as e:
                return format_api_error(e) + "\n\n(Traduction API impossible.)"
        return (
            "Traduction automatique indisponible sans clé API.\n"
            f"Configure une clé dans Paramètres, ou demande : « Traduis ce texte en {target_lang} : … »"
        )

    def _fallback(self, message: str, document_text: Optional[str], document_title: Optional[str]) -> str:
        lower = message.lower()
        has_content = bool(document_text and len(document_text.strip()) > 40)
        if has_content:
            preview = document_text[:700].replace("\n", " ")
            if any(w in lower for w in ["résume", "resume", "synthèse", "synthese"]):
                return f"Voici l'essentiel de « {document_title} » (extrait) :\n\n{preview}…\n\nDis-moi quelle partie tu veux approfondir."
            if any(w in lower for w in ["explique", "partie", "section", "chapitre"]):
                return f"D'après « {document_title} » :\n\n{preview}…\n\nPrécise la partie."
            if any(w in lower for w in ["exercice", "entraîne", "quiz"]):
                return f"On peut travailler un exercice de « {document_title} ».\nIndique le numéro ou copie l'énoncé."
            return f"J'ai le contenu de « {document_title} ».\n\nExtrait : {preview[:350]}…\n\nPose ta question."
        return "Importe d'abord un document, puis choisis une option (résumer, expliquer une partie, exercice…)."
