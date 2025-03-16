# -*- coding: utf-8 -*-
from xml.etree.ElementTree import QName


def prefix_tagroot(tag: str) -> list[str]: ...


def prefix(tag: str) -> str: ...


def tagroot(tag: str) -> str: ...


def uri(tag: str) -> str: ...


def fqdn(tag: str | None) -> QName | str | None: ...
