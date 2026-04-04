from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import re
import torch

# Load Meta's NLLB model — supports 200 languages including Telugu
MODEL_NAME = "facebook/nllb-200-distilled-600M"

print("Loading English→Telugu translation model (first run downloads ~2.4GB)...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
device = "mps" if torch.backends.mps.is_available() else "cpu"
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)

# Telugu language code for NLLB
TELUGU_LANG_CODE = "tel_Telu"

print(f"Model loaded successfully on device: {device}")


def translate_batch(text_list):
    """
    Translate a list of English text segments to Telugu.
    - Meaningful text is translated preserving meaning.
    - Proper nouns / names are transliterated to Telugu script.
    - Numbers, dates, and symbols are kept unchanged.

    Args:
        text_list: List of English strings to translate.

    Returns:
        List of Telugu translated strings (same length as input).
    """
    if not text_list:
        return []

    results = []
    # Process in batches of 16 for memory efficiency
    batch_size = 16

    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i + batch_size]
        translated_batch = _translate_chunk(batch)
        results.extend(translated_batch)

    return results


def _translate_chunk(texts):
    """Translate a chunk of texts using the NLLB model using true batching."""
    translated = []
    to_translate = []
    to_translate_indices = []

    for i, text in enumerate(texts):
        # Skip empty or whitespace-only text
        if not text or not text.strip():
            translated.append(text)
            continue

        # Skip if text is only numbers, punctuation, or symbols (no letters)
        if not re.search(r'[a-zA-Z]', text):
            translated.append(text)
            continue

        # Otherwise queue for translation
        to_translate.append(text)
        to_translate_indices.append(i)
        translated.append(None)  # placeholder

    if not to_translate:
        return translated

    try:
        # Tokenize as a batch
        inputs = tokenizer(to_translate, return_tensors="pt", padding=True, truncation=True, max_length=512)
        if hasattr(model, 'device') and model.device.type != 'cpu':
            inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # Generate Telugu translation
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(TELUGU_LANG_CODE)
        translated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_length=512,
            num_beams=2,           # reduced beam search for better speed
            length_penalty=1.0,
            early_stopping=True
        )

        results = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
        
        # Put translated texts back into their original positions
        for idx, result in zip(to_translate_indices, results):
            translated[idx] = result
            
    except Exception as e:
        print(f"  Translation error for batch: {e}")
        # fallback to original text for this batch
        for idx, text in zip(to_translate_indices, to_translate):
            translated[idx] = text

    return translated


def translate_text_to_telugu(text):
    """
    Translate a single English text string to Telugu.
    Kept for backward compatibility.
    """
    results = translate_batch([text])
    return results[0] if results else text
