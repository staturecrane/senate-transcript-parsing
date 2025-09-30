import itertools
from collections import defaultdict
from typing import Any, TypeAlias, TypedDict

import click
import requests
import spacy
from requests.models import Response
from rich import print
from rich.table import Table
from spacy.language import Language
from spacy.matcher import Matcher
from spacy.tokens.doc import Doc

SpeakerPattern: TypeAlias = list[dict[str, bool | str]]


class ConversationTurn(TypedDict):
    speaker: str
    text: str


def create_speaker_pattern(title: str) -> list[SpeakerPattern]:
    return [
        [{"IS_SENT_START": True, "TEXT": title}, {"ENT_TYPE": "PERSON"}, {"TEXT": "."}],
        [
            {"IS_SENT_START": True, "TEXT": title},
            {"ENT_TYPE": "PERSON"},
            {"ENT_TYPE": "PERSON"},
            {"TEXT": "."},
        ],
    ]


@click.command()
@click.option("--print-transcript", is_flag=True)
def main(print_transcript: bool) -> None:
    nlp: Language = spacy.load(name="en_core_web_sm")
    matcher: Any = Matcher(nlp.vocab)

    titles: list[str] = ["Mr.", "Chairman", "Senator", "Chairwoman"]
    patterns: list[SpeakerPattern] = list(
        itertools.chain.from_iterable(
            [create_speaker_pattern(title) for title in titles]
        )
    )

    for idx, pattern in enumerate(patterns):
        matcher.add(f"Title-{idx}", [pattern])

    response: Response = requests.get(
        url="https://www.govinfo.gov/content/pkg/CHRG-116shrg37919/html/CHRG-116shrg37919.htm"
    )
    response.raise_for_status()

    text_content_to_use: str = response.text.split(
        sep="STATEMENT OF DAVID A. MARCUS, HEAD OF CALIBRA, FACEBOOK"
    )[1].split(sep="PREPARED STATEMENT OF CHAIRMAN MIKE CRAPO")[0]

    speaker_words: dict[str, int] = defaultdict(int)
    speaker_questions: dict[str, int] = defaultdict(int)

    paragraphs: list[str] = text_content_to_use.split(sep="    ")
    paragraphs_filtered: list[str] = [
        stripped_paragraph
        for paragraph in paragraphs
        if (stripped_paragraph := paragraph.strip())
    ]

    transcript: list[ConversationTurn] = []

    current_speaker: None | str = None
    current_text: str = ""

    for paragraph in paragraphs_filtered:
        doc: Doc = nlp(text=paragraph)

        speaker_matches = matcher(doc)
        speaker: str | None = None
        speaker_text: str = ""

        if speaker_matches:
            _, start, end = speaker_matches[0]
            speaker: str = doc[start : end - 1].text
            speaker_text: str = doc[end:].text
        else:
            speaker_text: str = doc.text

        if current_speaker is None:
            current_speaker: str = speaker
            current_text += speaker_text
        
        elif speaker is None or current_speaker == speaker:
            current_text += speaker_text
        
        elif current_speaker != speaker:
            stripped_text: str = current_text.strip().replace("\n", "")
            transcript.append({"speaker": current_speaker, "text": stripped_text})

            num_questions: int = stripped_text.count("?")

            speaker_questions[current_speaker] += num_questions
            speaker_words[current_speaker] += len(stripped_text.split(sep=" "))

            current_speaker: str = speaker
            current_text: str = speaker_text

    if print_transcript:
        for conversation_turn in transcript:
            print(f"[bold magenta]{conversation_turn['speaker']}[/bold magenta]: ", conversation_turn['text'])

    table: Table = Table(show_header=True, header_style="bold light_sea_green")
    table.add_column(header="Speaker Name")
    table.add_column(header="Word Ratio")
    table.add_column(header="Num Questions")

    total_words: int = sum(speaker_words.values())
    for speaker, num_words in speaker_words.items():
        table.add_row(
            speaker,
            str(round(number=num_words / total_words, ndigits=3)),
            str(speaker_questions[speaker]),
        )

    print(table)


if __name__ == "__main__":
    main()
