
from .deuil import Deuil
from .naissance import Naissance
from .interruption_grossesse import InterruptionGrossesse
from .rencontres_virtuelle import RencontresVirtuelles
from .intervention_perinatale import InterventionPerinatale
from .relevailles import Relevailles

# Custom Types to be exported.
# IMPORTANT. Do not use inside models module

type ServiceProfile = Naissance | Deuil | InterruptionGrossesse | RencontresVirtuelles | InterventionPerinatale | Relevailles