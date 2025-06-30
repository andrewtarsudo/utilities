# -*- coding: utf-8 -*-
from typing import Any, Mapping, NamedTuple

from httpx import Client, HTTPStatusError, Response
from loguru import logger


def to_str(cls: type[NamedTuple]):
    for field in cls._fields:
        if


class Software(NamedTuple):
    name: str
    version: str
    buildDate: str
    apiVersion: int
    premium: bool
    premiumHint: str
    status: str


class Warnings(NamedTuple):
    incompleteResults: bool


class DetectedLanguage(NamedTuple):
    name: str
    code: str
    confidence: float
    source: str


class Language(NamedTuple):
    name: str
    code: str
    detectedLanguage: DetectedLanguage


class Replacement(NamedTuple):
    value: str


class Context(NamedTuple):
    text: str
    offset: int
    length: int


class RuleType(NamedTuple):
    typeName: str


class Category(NamedTuple):
    id: str
    name: str


class Rule(NamedTuple):
    id: str
    description: str
    issueType: str
    category: Category
    isPremium: bool
    confidence: float


class Match(NamedTuple):
    message: str
    shortMessage: str
    replacements: list[Replacement]
    offset: int
    length: int
    context: Context
    sentence: str
    type: RuleType
    rule: Rule
    ignoreForIncompleteSentence: bool
    contextForSureMatch: int


class DetectedLanguageInfo(NamedTuple):
    language: str
    rate: float


class ExtendedSentenceRange(NamedTuple):
    from_: int
    to: int
    detectedLanguages: list[DetectedLanguageInfo]


class LanguageToolResponse(NamedTuple):
    software: Software
    warnings: Warnings
    language: Language
    matches: list[Match]
    sentenceRanges: list[tuple[int, int]]
    extendedSentenceRanges: list[ExtendedSentenceRange]


class LanguageToolClient:
    def __init__(self, base_url: str = "https://api.languagetool.org/v2"):
        self._base_url: str = base_url
        self._headers: dict[str, str] = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"}

        self._client = Client(timeout=10.0)

    def check_text(self, text: str, language: str = "ru-RU"):
        data: dict[str, str] = {
            "text": text,
            "language": language,
            "enabledOnly": False}

        try:
            return (
                self._client
                .post(
                    self._base_url,
                    data=data,
                    headers=self._headers)
                .raise_for_status()
                .json())

        except HTTPStatusError as e:
            logger.error(
                f"{e.__class__.__name__}:"
                f"\nЗапрос:"
                f"\n{e.request}"
                f"\nнекорректен")

    def get_corrections(self, data: Mapping[str, Any] = None):
        if data is None:
            return []

        matches: list[dict[str, Any]] = data.get("matches", [])
        corrections = []

        for match in matches:
            message: str = match.get("message")
            replacements = [r.get("value") for r in match.get("replacements", [])]
            offset: int = match.get("offset")
            length: int = match.get("length")
            context: dict[str, str] = match.get("context")
            sentence: str = match.get("sentence")

            corrections.append(
                {
                    "message": message,
                    "replacements": replacements,
                    "offset": offset,
                    "length": length,
                    "context": context,
                }
            )
        return corrections

    def close(self):
        self._client.close()


# Example usage
if __name__ == "__main__":
    client = LanguageToolClient()

    sample_text = "This are a example with a misstakes."
    corrections = client.get_corrections(sample_text)

    if corrections:
        print("Found corrections:")
        for c in corrections:
            print(f"- {c['context']} → {c['replacements']} ({c['message']})")
    else:
        print("No corrections found!")

    client.close()
