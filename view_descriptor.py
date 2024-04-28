from typing import Any
from dataclasses import dataclass


@dataclass
class ViewDescriptor:
    text: str
    reply_markup: Any
