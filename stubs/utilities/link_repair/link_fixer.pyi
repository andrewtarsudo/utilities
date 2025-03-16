# -*- coding: utf-8 -*-
from utilities.common.errors import LinkRepairFixerNoLinkError as LinkRepairFixerNoLinkError, \
    LinkRepairInvalidHashCharIndexError as LinkRepairInvalidHashCharIndexError
from utilities.link_repair.file_dict import TextFile as TextFile


class LinkFixer:
    PATTERN: str
    text_file: TextFile | None

    def __init__(self) -> None: ...

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    def __iter__(self): ...

    def __bool__(self) -> bool: ...

    def fix_links(self) -> None: ...


link_fixer: LinkFixer
