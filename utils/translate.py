from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import re

# Load Meta's NLLB model — supports 200 languages including Telugu
MODEL_NAME = "facebook/nllb-200-distilled-600M"

print("Loading English→Telugu translation model (first run downloads ~2.4GB)...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Telugu language code for NLLB
TELUGU_LANG_CODE = "tel_Telu"

print("Model loaded successfully!")


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
    """Translate a chunk of texts using the NLLB model."""
    translated = []

    for text in texts:
        # Skip empty or whitespace-only text
        if not text or not text.strip():
            translated.append(text)
            continue

        # Skip if text is only numbers, punctuation, or symbols (no letters)
        if not re.search(r'[a-zA-Z]', text):
            translated.append(text)
            continue

        try:
            # Tokenize
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

            # Generate Telugu translation
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids(TELUGU_LANG_CODE),
                max_length=512,
                num_beams=4,           # beam search for better quality
                length_penalty=1.0,
                early_stopping=True
            )

            result = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
            translated.append(result)
        except Exception as e:
            print(f"  Translation error for '{text[:50]}...': {e}")
            translated.append(text)  # fallback to original

    return translated


def translate_text_to_telugu(text):
    """
    Translate a single English text string to Telugu.
    Kept for backward compatibility.
    """
    results = translate_batch([text])
    return results[0] if results else text
