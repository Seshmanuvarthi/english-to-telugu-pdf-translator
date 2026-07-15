from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import re
import torch
import threading

MODEL_NAME = "facebook/nllb-200-distilled-600M"
TELUGU_LANG_CODE = "tel_Telu"

_inference_lock = threading.Lock()
_model_load_error = None

print("Loading English→Telugu translation model (first run downloads ~2.4GB)...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
    print(f"Model loaded successfully on device: {device}")
except Exception as e:
    _model_load_error = str(e)
    tokenizer = model = device = None
    print(f"ERROR: Failed to load translation model: {e}")


def translate_batch(text_list):
    if _model_load_error:
        raise RuntimeError(f"Translation model failed to load: {_model_load_error}")

    if not text_list:
        return []

    results = []
    batch_size = 16

    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i + batch_size]
        translated_batch = _translate_chunk(batch)
        results.extend(translated_batch)

    return results


def _translate_chunk(texts):
    """Translate a chunk of texts using the NLLB model with a serialising lock for GPU safety."""
    translated = []
    to_translate = []
    to_translate_indices = []

    for i, text in enumerate(texts):
        if not text or not text.strip():
            translated.append(text)
            continue
        if not re.search(r'[a-zA-Z]', text):
            translated.append(text)
            continue
        to_translate.append(text)
        to_translate_indices.append(i)
        translated.append(None)  # placeholder

    if not to_translate:
        return translated

    try:
        with _inference_lock:
            inputs = tokenizer(
                to_translate, return_tensors="pt",
                padding=True, truncation=True, max_length=512
            )
            if hasattr(model, 'device') and model.device.type != 'cpu':
                inputs = {k: v.to(model.device) for k, v in inputs.items()}

            forced_bos_token_id = tokenizer.convert_tokens_to_ids(TELUGU_LANG_CODE)
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                max_length=512,
                num_beams=2,
                length_penalty=1.0,
                early_stopping=True
            )
            results = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)

        for idx, result in zip(to_translate_indices, results):
            translated[idx] = result

    except Exception as e:
        print(f"  Translation error for batch: {e}")
        for idx, text in zip(to_translate_indices, to_translate):
            translated[idx] = text

    return translated


def translate_text_to_telugu(text):
    """Kept for backward compatibility."""
    results = translate_batch([text])
    return results[0] if results else text
