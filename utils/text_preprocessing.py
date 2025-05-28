import re


def process_text(text : str):
    """Preprocess text """
    # text = re.sub(r'[^\w\sÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯàáâãèéêìíòóôõùúăđĩũơư]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)     # Replace multiple spaces with a single space
    return text.strip()                  # Remove leading and trailing spaces

