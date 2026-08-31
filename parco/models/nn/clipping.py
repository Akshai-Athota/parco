"""Tanh logit clipping in two functional forms.

PARCO follows Bello et al. (2016) and clips the decoder logits with

    phi_fixed(z; C) = C * tanh(z)

which saturates as soon as ``|z| >> 1``: the gradient w.r.t. ``z`` vanishes and
raising ``C`` only rescales an already-saturated signal. Gemma 2 instead uses

    phi_scaled(z; C) = C * tanh(z / C)

which is near-linear for ``|z| << C``, so the gradient stays close to 1 and ``C``
acts as an actual soft bound rather than a saturation point.

Both forms are exposed here so they can be applied at two places:

1. the decoder logits (pointer scores over the nodes) before the softmax --
   this is where PARCO already clips, with ``phi_fixed`` and ``C = 10``;
2. the attention logits ``Q K^T / sqrt(d)`` inside the encoder MHA layers,
   before the softmax -- PARCO does not clip these at all.
"""

import math

from typing import Optional

import torch

from rl4co.utils.decoding import process_logits as rl4co_process_logits
from torch import Tensor

CLIP_MODES = ("fixed", "scaled", "none")


def tanh_clip(logits: Tensor, clip_value: float, mode: str = "fixed") -> Tensor:
    """Clip ``logits`` into ``(-clip_value, clip_value)`` with a tanh.

    Args:
        logits: tensor to clip.
        clip_value: the bound ``C``. Non-positive values disable clipping.
        mode: ``"fixed"`` for ``C * tanh(z)``, ``"scaled"`` for ``C * tanh(z / C)``,
            ``"none"`` to disable clipping.
    """
    if mode not in CLIP_MODES:
        raise ValueError(f"Unknown tanh clip mode '{mode}'. Available: {CLIP_MODES}")
    if mode == "none" or clip_value is None or clip_value <= 0:
        return logits
    if mode == "fixed":
        return clip_value * torch.tanh(logits)
    return clip_value * torch.tanh(logits / clip_value)


def process_logits(
    logits: Tensor,
    mask: Optional[Tensor] = None,
    tanh_clipping: float = 0,
    tanh_clip_mode: str = "fixed",
    **kwargs,
) -> Tensor:
    """Drop-in replacement for ``rl4co.utils.decoding.process_logits`` that also
    supports the scaled tanh clipping form.

    We apply the clipping ourselves and then delegate the rest (masking,
    temperature, top-k/top-p, log-softmax) to rl4co with clipping disabled.
    """
    logits = tanh_clip(logits, tanh_clipping, tanh_clip_mode)
    return rl4co_process_logits(logits, mask, tanh_clipping=0, **kwargs)


class TanhClippedSDPA:
    """Scaled dot-product attention that tanh-clips the attention logits.

    Passed as ``sdpa_fn`` to the ``MultiHeadAttention`` of the encoder blocks, so
    the scores are clipped right before the softmax. This bounds how peaked a
    single attention distribution can become (attention collapse), which the
    unclipped default cannot prevent.

    Note: this is a module-level class rather than a closure on purpose -- the
    policy object is pickled into the Lightning checkpoint, and closures are not
    picklable.
    """

    def __init__(self, clip_value: float = 10.0, mode: str = "scaled"):
        if mode not in CLIP_MODES:
            raise ValueError(f"Unknown tanh clip mode '{mode}'. Available: {CLIP_MODES}")
        self.clip_value = clip_value
        self.mode = mode

    def __call__(
        self,
        q: Tensor,
        k: Tensor,
        v: Tensor,
        attn_mask: Optional[Tensor] = None,
        dropout_p: float = 0.0,
        is_causal: bool = False,
        scale: Optional[float] = None,
    ) -> Tensor:
        scale = 1.0 / math.sqrt(q.size(-1)) if scale is None else scale
        scores = torch.matmul(q, k.transpose(-2, -1)) * scale

        # The whole point: clip before the softmax, not after
        scores = tanh_clip(scores, self.clip_value, self.mode)

        if attn_mask is not None:
            if attn_mask.dtype == torch.bool:
                scores = scores.masked_fill(~attn_mask, float("-inf"))
            else:
                scores = scores + attn_mask

        if is_causal:
            len_q, len_k = scores.size(-2), scores.size(-1)
            causal_mask = torch.ones(
                (len_q, len_k), dtype=torch.bool, device=scores.device
            ).triu(diagonal=1)
            scores = scores.masked_fill(causal_mask, float("-inf"))

        attn_weights = torch.softmax(scores, dim=-1)
        if dropout_p > 0.0:
            attn_weights = torch.dropout(attn_weights, p=dropout_p, train=True)

        return torch.matmul(attn_weights, v)

    def __repr__(self):
        return f"{type(self).__name__}(clip_value={self.clip_value}, mode={self.mode})"


def get_attention_sdpa(
    clip_value: float = 0.0, mode: str = "scaled"
) -> Optional[TanhClippedSDPA]:
    """Build the clipped attention function, or ``None`` to keep rl4co's default.

    ``None`` is returned when clipping is disabled so that the unmodified PARCO
    behaviour goes through the original (flash-attention capable) kernel.
    """
    if mode == "none" or clip_value is None or clip_value <= 0:
        return None
    return TanhClippedSDPA(clip_value, mode)
