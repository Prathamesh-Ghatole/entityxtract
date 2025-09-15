import regex as re
from pathlib import Path
from entityxtract import extractor_types

ALL_FILES = Path(__file__).parent.glob("*.txt")
SYSTEM_PROMPT_FILE = "system.txt"
TABLE_PROMPT = "table.txt"
STRING_PROMPT = "string.txt"


def get_system_prompt() -> str:
    return (Path(__file__).parent / SYSTEM_PROMPT_FILE).read_text()


def get_prompt(obj: extractor_types.ExtractableObjectTypes) -> str:
    if isinstance(obj, extractor_types.StringToExtract):
        template = (Path(__file__).parent / STRING_PROMPT).read_text()
        prompt = template.replace(r"{{name}}", obj.name)
        prompt = prompt.replace(r"{{example}}", obj.example_string)
        prompt = prompt.replace(r"{{instructions}}", obj.instructions)
        return prompt

    elif isinstance(obj, extractor_types.TableToExtract):
        template = (Path(__file__).parent / TABLE_PROMPT).read_text()
        prompt = template.replace(r"{{name}}", obj.name)
        prompt = prompt.replace(r"{{columns}}", ", ".join(obj.example_table.columns))
        prompt = prompt.replace(
            r"{{example}}", obj.example_table.head(3).to_dicts().__str__()
        )
        prompt = prompt.replace(r"{{instructions}}", obj.instructions)
        return prompt

    else:
        raise ValueError(f"Unknown object type: {type(obj)}")
