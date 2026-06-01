"""
GTU-ITR R&D & IIC Portal - AI Engine (Singleton)
Lazy-loads microsoft/Phi-3-mini-4k-instruct via transformers pipeline.
Thread-safe. Falls back to CPU if no GPU. Never crashes if torch/transformers
are missing — returns None so callers fall back to heuristics.
"""

import logging
import threading

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Eager import check at server startup (not during a user request).
# These imports take ~20s on some machines, so we pay this cost once at boot.
# ---------------------------------------------------------------------------
_TORCH_AVAILABLE = False
_HAS_CUDA = False

try:
    import torch
    _TORCH_AVAILABLE = True
    _HAS_CUDA = torch.cuda.is_available()

    if not _HAS_CUDA:
        logger.info(
            "AI engine: No CUDA GPU detected. Phi-3 (3.8B params) is too "
            "large for real-time CPU inference. AI features will use instant "
            "heuristic extraction instead."
        )
except ImportError:
    logger.info("AI engine: torch not installed. AI features will use heuristic extraction.")

_HF_PIPELINE = None
if _TORCH_AVAILABLE and _HAS_CUDA:
    try:
        from transformers import pipeline as _HF_PIPELINE_FUNC
        _HF_PIPELINE = _HF_PIPELINE_FUNC  # Store the callable
    except ImportError:
        logger.info("AI engine: transformers not installed. AI features will use heuristic extraction.")

# ---------------------------------------------------------------------------
# Sentinel used when the pipeline could not be loaded
# ---------------------------------------------------------------------------
_NOT_LOADED = object()


class _AIEngineSingleton:
    """
    Thread-safe singleton that wraps a ``transformers.pipeline``
    for text generation.

    Usage::

        from services.ai_engine import AIEngine
        result = AIEngine.generate("Summarise this document …")
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._pipeline = _NOT_LOADED
                    cls._instance._load_error = None
        return cls._instance

    # ------------------------------------------------------------------
    # Lazy loader
    # ------------------------------------------------------------------
    def _ensure_loaded(self):
        """Load the model on first call (double-checked locking)."""
        if self._pipeline is not _NOT_LOADED:
            return

        with self._lock:
            if self._pipeline is not _NOT_LOADED:
                return

            # ── Fast exit: no GPU or missing packages ──────────────
            if not _TORCH_AVAILABLE:
                self._pipeline = None
                self._load_error = (
                    "AI engine unavailable – torch is not installed."
                )
                return

            if not _HAS_CUDA:
                self._pipeline = None
                self._load_error = (
                    "AI engine skipped – no CUDA GPU detected. "
                    "Using instant heuristic extraction instead."
                )
                return

            if _HF_PIPELINE is None:
                self._pipeline = None
                self._load_error = (
                    "AI engine unavailable – transformers is not installed."
                )
                return

            # ── Load the model (GPU available) ─────────────────────
            try:
                try:
                    from flask import current_app
                    model_name = current_app.config.get(
                        'AI_MODEL_NAME',
                        'microsoft/Phi-3-mini-4k-instruct',
                    )
                    max_tokens = current_app.config.get('AI_MAX_TOKENS', 2048)
                except RuntimeError:
                    model_name = 'microsoft/Phi-3-mini-4k-instruct'
                    max_tokens = 2048

                logger.info("Loading AI model: %s …", model_name)
                try:
                    self._pipeline = _HF_PIPELINE(
                        "text-generation",
                        model=model_name,
                        device_map="auto",
                        torch_dtype="auto",
                        max_new_tokens=max_tokens,
                        model_kwargs={"local_files_only": True}
                    )
                except Exception as auto_exc:
                    logger.warning(
                        "Failed loading with device_map='auto': %s. "
                        "Retrying on CPU...", auto_exc
                    )
                    self._pipeline = _HF_PIPELINE(
                        "text-generation",
                        model=model_name,
                        device="cpu",
                        max_new_tokens=max_tokens,
                        model_kwargs={"local_files_only": True}
                    )
                self._max_tokens = max_tokens
                logger.info("AI model loaded successfully.")

            except Exception as exc:
                self._pipeline = None
                self._load_error = f"AI engine failed to initialise: {exc}"
                logger.exception(self._load_error)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self, prompt: str, *, max_new_tokens: int | None = None,
                 temperature: float = 0.7, top_p: float = 0.9,
                 timeout: int = 15) -> str | None:
        """
        Send *prompt* to the model and return the generated text.

        Returns ``None`` on any failure (model not loaded, generation error,
        or timeout) so callers can fall back to heuristic extraction.

        Parameters
        ----------
        prompt : str
            The full prompt (system + user) to send.
        max_new_tokens : int, optional
            Override the default ``AI_MAX_TOKENS`` from config.
        temperature : float
            Sampling temperature (0 → deterministic, 1 → creative).
        top_p : float
            Nucleus-sampling probability mass.
        timeout : int
            Maximum seconds to wait for generation (default 15).
            Prevents CPU-bound models from hanging web requests.
        """
        self._ensure_loaded()

        # If model is unavailable, return None so caller falls back
        if self._pipeline is None:
            logger.info("AI model unavailable: %s", self._load_error)
            return None

        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

            tokens = max_new_tokens or self._max_tokens

            def _run_generation():
                outputs = self._pipeline(
                    prompt,
                    max_new_tokens=tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    return_full_text=False,
                )
                return outputs[0].get("generated_text", "").strip()

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_generation)
                try:
                    generated = future.result(timeout=timeout)
                    return generated
                except FuturesTimeout:
                    logger.warning(
                        "AI generation timed out after %ds. "
                        "Falling back to heuristic extraction.", timeout
                    )
                    return None

        except Exception as exc:
            logger.exception("AI generation failed: %s", exc)
            return None

    @property
    def is_available(self) -> bool:
        """Return True if the model has been (or can be) loaded."""
        self._ensure_loaded()
        return self._pipeline is not None

    def status(self) -> dict:
        """Return a dict describing the engine's current state."""
        self._ensure_loaded()
        return {
            "available": self._pipeline is not None,
            "error": self._load_error,
            "model": (
                self._pipeline.model.config._name_or_path
                if self._pipeline else None
            ),
        }


# ---------------------------------------------------------------------------
# Module-level convenience singleton
# ---------------------------------------------------------------------------
AIEngine = _AIEngineSingleton()
