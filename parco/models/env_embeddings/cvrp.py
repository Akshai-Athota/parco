"""Embeddings for the homogeneous-fleet CVRP.

These are deliberately the HCVRP embeddings verbatim: the state tensors are
identical, and a homogeneous fleet is just the special case where the capacity
and speed agent features are constant across agents. They exist only so the
new environment can register under its own name, keeping the "zero model
changes" property of the CVRP extension literally true.

Note that ``demand_scaler`` should be set to the fleet capacity (see
``init_embedding_kwargs`` in configs/experiment/cvrp.yaml) so the normalised
capacity feature stays around 1, as it is for HCVRP.
"""

from .hcvrp import HCVRPContextEmbedding, HCVRPInitEmbedding


class CVRPInitEmbedding(HCVRPInitEmbedding):
    """Identical to :class:`HCVRPInitEmbedding`."""


class CVRPContextEmbedding(HCVRPContextEmbedding):
    """Identical to :class:`HCVRPContextEmbedding`."""
