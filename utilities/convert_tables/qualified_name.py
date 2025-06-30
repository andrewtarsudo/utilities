# -*- coding: utf-8 -*-
from xml.etree.ElementTree import QName

from loguru import logger

_ns: dict[str, str] = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "aink": "http://schemas.microsoft.com/office/drawing/2016/ink",
    "am3d": "http://schemas.microsoft.com/office/drawing/2017/model3d",
    "b": "http://schemas.openxmlformats.org/officeDocument/2006/bibliography",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "cdr": "http://schemas.openxmlformats.org/drawingml/2006/chartDrawing",
    "cdr14": "http://schemas.microsoft.com/office/drawing/2010/chartDrawing",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "cx1": "http://schemas.microsoft.com/office/drawing/2015/9/8/chartex",
    "cx2": "http://schemas.microsoft.com/office/drawing/2015/10/21/chartex",
    "cx3": "http://schemas.microsoft.com/office/drawing/2016/5/9/chartex",
    "cx4": "http://schemas.microsoft.com/office/drawing/2016/5/10/chartex",
    "cx5": "http://schemas.microsoft.com/office/drawing/2016/5/11/chartex",
    "cx6": "http://schemas.microsoft.com/office/drawing/2016/5/12/chartex",
    "cx7": "http://schemas.microsoft.com/office/drawing/2016/5/13/chartex",
    "cx8": "http://schemas.microsoft.com/office/drawing/2016/5/14/chartex",
    "dc": "http://purl.org/dc/elements/1.1",
    "dcmitype": "http://purl.org/dc/dcmitype",
    "dcterms": "http://purl.org/dc/terms",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "ds": "http://schemas.openxmlformats.org/officeDocument/2006/customXml",
    "dsp": "http://schemas.microsoft.com/office/drawing/2008/diagram",
    "ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "mce": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "msink": "http://schemas.microsoft.com/ink/2010/main",
    "mso": "urn:schemas-microsoft-com:office:office",
    "mv": "urn:schemas-microsoft-com:mac:vml",
    "o": "urn:schemas-microsoft-com:office:office",
    "od": "http://opendope.org/conditions",
    "oda": "http://opendope.org/answers",
    "odc": "http://opendope.org/conditions",
    "odx": "http://opendope.org/xpaths",
    "oel": "http://schemas.microsoft.com/office/2019/extlst",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "s": "http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes",
    "sl": "http://schemas.openxmlformats.org/schemaLibrary/2006/main",
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "soap12": "http://www.w3.org/2003/05/soap-envelope",
    "st": "http://schemas.microsoft.com/smarttags/2003",
    "v": "urn:schemas-microsoft-com:vml",
    "ve": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "vt": "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w10": "urn:schemas-microsoft-com:office:word",
    "w13": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16cur": "http://schemas.microsoft.com/office/word/2018/wordml/customXmlDataReuse",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "wcm": "http://schemas.microsoft.com/office/word/2011/wordComments",
    "we": "http://schemas.microsoft.com/office/webextensions/webextension/2010/11",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "wpi": "http://schemas.microsoft.com/office/word/2010/wordprocessingInk",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xmlns": "http://schemas.openxmlformats.org/package/2006/content-types",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    'w14': "http://schemas.microsoft.com/office/word/2010/wordml"}


def fqdn(tag: str) -> str:
    if all(item not in tag for item in (":", "{")):
        return tag

    if tag.startswith("{"):
        uri, tagroot = tag[1:].split("}")

    else:
        uri, tagroot = tag.split(":", 1)

    try:
        if not uri.startswith("{"):
            uri: str = _ns[uri]

    except KeyError:
        logger.warning(f"Обнаружен неизвестный тег `{uri}`")
        _ns[uri] = f"{uri}"
        logger.info(f"Тег {uri} добавлен в пространство имен со значением {uri}")

    return QName(uri, tagroot).text
