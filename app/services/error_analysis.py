from dataclasses import dataclass
from enum import Enum


class ErrorType(str, Enum):
    CONCEPT = "concept"
    METHOD = "method"
    CALCULATION = "calculation"
    READING = "reading"
    CARELESS = "careless"
    UNKNOWN = "unknown"


ERROR_LABELS = {
    ErrorType.CONCEPT: "Concept mal compris",
    ErrorType.METHOD: "Mauvaise méthode",
    ErrorType.CALCULATION: "Erreur de calcul",
    ErrorType.READING: "Lecture de l'énoncé",
    ErrorType.CARELESS: "Étourderie",
    ErrorType.UNKNOWN: "Non classée",
}


ADAPTATION_STRATEGIES = {
    ErrorType.CONCEPT: (
        "STYLE ADAPTÉ — erreur de concept :\n"
        "- Revenir à la définition simple en 1 phrase\n"
        "- Donner une analogie du quotidien\n"
        "- Un seul exemple très simple avant tout exercice\n"
        "- Éviter le jargon au début"
    ),
    ErrorType.METHOD: (
        "STYLE ADAPTÉ — erreur de méthode :\n"
        "- Rappeler la méthode étape par étape (numérotée)\n"
        "- Dire explicitement quelle formule / outil utiliser et pourquoi\n"
        "- Comparer avec une mauvaise méthode fréquente\n"
        "- Faire faire la 1re étape à l'élève avant de continuer"
    ),
    ErrorType.CALCULATION: (
        "STYLE ADAPTÉ — erreur de calcul :\n"
        "- Insister sur la vérification à chaque ligne\n"
        "- Proposer de recalculer lentement\n"
        "- Donner un moyen de contrôle (ordre de grandeur)\n"
        "- Ne pas remonter au concept si le raisonnement était bon"
    ),
    ErrorType.READING: (
        "STYLE ADAPTÉ — mauvaise lecture de l'énoncé :\n"
        "- Faire reformuler la question par l'élève\n"
        "- Souligner les mots importants\n"
        "- Lister données / demandées\n"
        "- Vérifier unités et hypothèses"
    ),
    ErrorType.CARELESS: (
        "STYLE ADAPTÉ — étourderie :\n"
        "- Encourager sans dramatiser\n"
        "- Checklist de relecture (signe, parenthèses, report)\n"
        "- Un exercice court pour revalider la confiance"
    ),
    ErrorType.UNKNOWN: (
        "STYLE ADAPTÉ — erreur non classée :\n"
        "- Demander ce qui a bloqué\n"
        "- Reprendre avec un exemple guidé"
    ),
}


def classify_error_heuristic(message: str, notion: str = "") -> ErrorType:
    lower = (message or "").lower()
    if any(w in lower for w in ("énoncé", "question", "consigne", "demandé", "lu trop vite")):
        return ErrorType.READING
    if any(w in lower for w in ("calcul", "addition", "multiplication", "signe", "parenthèse")):
        return ErrorType.CALCULATION
    if any(w in lower for w in ("formule", "méthode", "technique", "comment faire", "quelle règle")):
        return ErrorType.METHOD
    if any(w in lower for w in ("c'est quoi", "définition", "concept", "je confonds", "signifie")):
        return ErrorType.CONCEPT
    if any(w in lower for w in ("bête", "étourdi", "j'ai oublié", "mal recopié")):
        return ErrorType.CARELESS
    if notion and any(w in lower for w in ("pas compris", "comprends pas", "confus")):
        return ErrorType.CONCEPT
    return ErrorType.UNKNOWN


@dataclass
class ErrorAnalysis:
    error_type: ErrorType
    notion: str
    subject: str
    summary: str
    strategy: str
    source: str = "heuristic"

    def as_memory_text(self) -> str:
        return (
            f"Analyse d'erreur [{ERROR_LABELS[self.error_type]}] sur « {self.notion} » ({self.subject}).\n"
            f"{self.summary}\n"
            f"Stratégie : {self.strategy[:400]}"
        )
