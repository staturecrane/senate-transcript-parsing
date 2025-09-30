### Install UV

```shell
curl -LsSf https://astral.sh/uv/0.8.22/install.sh | sh
```

### Sync/Install Dependencies

```shell
uv sync
uv pip install pip
```

### Download Spacy Model

```shell
uv run -m spacy download en_core_web_sm
```

### Run Transript Extraction

```shell
uv run -m src.extract_spacy
```

Or if you would like to also print the transcript:
```shell
uv run -m src.extract_spacy --print-transcript
```