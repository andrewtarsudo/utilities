# -*- coding: utf-8 -*-
from re import Match, sub

from utilities.common.constants import StrPath
from utilities.common.functions import file_reader, file_writer, ReaderMode


def substitute(file: StrPath):
    translation_table: dict[str, str] = {
        "{global_title}": 'pass:q[<abbr title="Global Title">GT</abbr>]',
        "{np}": 'pass:q[<abbr title="Numbering Plan">NP</abbr>]',
        "{ssn}": 'pass:q[<abbr title="Subsystem Number">SSN</abbr>]',
        "{tt}": 'pass:q[<abbr title="Translation Type">TT</abbr>]',
        "{nai}": 'pass:q[<abbr title="Nature of Address Indicator">NAI</abbr>]',
        "{es}": 'pass:q[<abbr title="Encoding Scheme">ES</abbr>]',
        "{acn}": 'pass:q[<abbr title="Application Context Name">ACN</abbr>]',
        "{npi}": 'pass:q[<abbr title="Numbering Plan Indicator">NPI</abbr>]',
        "{ton}": 'pass:q[<abbr title="Type of Numbering">TON</abbr>]',
        "{apn}": 'pass:q[<abbr title="Access Point Name">APN</abbr>]',
        "{rat}": 'pass:q[<abbr title="Radio Access Technology">RAT</abbr>]',
        "{msu}": 'pass:q[<abbr title="Message Signal Unit">MSU</abbr>]',
        "{pc}": 'pass:q[<abbr title="Protocol Class">PC</abbr>]',
        "{lsl}": 'pass:q[<abbr title="Low Speed Link">LSL</abbr>]',
        "{hsl}": 'pass:q[<abbr title="High Speed Link">HSL</abbr>]'
    }

    lines: list[str] = file_reader(file, ReaderMode.LINES)

    def repl(m: Match):
        if m.group(1) in translation_table:
            substitution: str = translation_table.get(m.group(1))
            print(f"Замена {m.group(1)} -> {substitution}")
            return substitution

        else:
            return m.group(1)

    lines: list[str] = [sub(r"(\{.*?})", repl, line) for line in iter(lines)]

    file_writer(file, lines)


if __name__ == '__main__':
    path: str = "../../shared/FW/analysis_params.en.adoc"
    substitute(path)
