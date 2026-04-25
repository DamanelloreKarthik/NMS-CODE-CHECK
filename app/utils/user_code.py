import random
import string

def generate_user_code(length: int = 6) -> str:
    """
    Generates human-friendly user code like:
    ADM3K9, USR7Q2, OPS91A
    """
    return "".join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
