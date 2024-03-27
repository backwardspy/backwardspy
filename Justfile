lock:
    pip-compile --strip-extras --generate-hashes --quiet

install:
    pip install -r requirements.txt
