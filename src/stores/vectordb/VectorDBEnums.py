from enum import Enum

class VectorDBEnums(Enum):
    QDRANT ="QDRANT"

class DistanceMethod(Enum):
    COSINE = "cosine"
    DOT = "dot"