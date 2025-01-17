# -*- coding: utf-8 -*-
from xml.etree.ElementTree import QName

_ns: dict[str, str] = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "aink": "http://schemas.microsoft.com/office/drawing/2016/ink",
    "am3d": "http://schemas.microsoft.com/office/drawing/2017/model3d",
    "dc": "http://purl.org/dc/elements/1.1",
    "ds": "http://schemas.openxmlformats.org/officeDocument/2006/customXml",
    "dcmitype": "http://purl.org/dc/dcmitype",
    "dcterms": "http://purl.org/dc/terms",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "cx1": "http://schemas.microsoft.com/office/drawing/2015/9/8/chartex",
    "cx2": "http://schemas.microsoft.com/office/drawing/2015/10/21/chartex",
    "cx3": "http://schemas.microsoft.com/office/drawing/2016/5/9/chartex",
    "cx4": "http://schemas.microsoft.com/office/drawing/2016/5/10/chartex",
    "cx5": "http://schemas.microsoft.com/office/drawing/2016/5/11/chartex",
    "cx6": "http://schemas.microsoft.com/office/drawing/2016/5/12/chartex",
    "cx7": "http://schemas.microsoft.com/office/drawing/2016/5/13/chartex",
    "cx8": "http://schemas.microsoft.com/office/drawing/2016/5/14/chartex",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "mce": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "o": "urn:schemas-microsoft-com:office:office",
    "oel": "http://schemas.microsoft.com/office/2019/extlst",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "s": "http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes",
    "sl": "http://schemas.openxmlformats.org/schemaLibrary/2006/main",
    "v": "urn:schemas-microsoft-com:vml",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w10": "urn:schemas-microsoft-com:office:word",
    'w14': "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "wpi": "http://schemas.microsoft.com/office/word/2010/wordprocessingInk",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xmlns": "http://schemas.openxmlformats.org/package/2006/content-types",
    "ve": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "vt": "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"}


def prefix_tagroot(tag: str) -> list[str]:
    if tag.startswith("{"):
        return tag[1:].split("}")

    else:
        return tag.split(":", 1)


def prefix(tag: str) -> str:
    return prefix_tagroot(tag)[0]


def tagroot(tag: str) -> str:
    return prefix_tagroot(tag)[1]


def uri(tag: str) -> str:
    if tag.startswith("{"):
        return prefix(tag)

    else:
        return _ns.get(prefix(tag))


def fqdn(tag: str | None) -> QName | str | None:
    if tag is None:
        return None

    elif all([item not in tag for item in (":", "{")]):
        return tag

    else:
        return QName(uri(tag), tagroot(tag)).text
