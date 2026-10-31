"""Compare shared context metadata and exact package-local instruction bytes."""
from pathlib import Path


def instruction_source(context):
    package = context.parent.parent
    prefix = f'.prifly/workflows/{package.name}/'
    source = next((line.removeprefix('source: ') for line in context.read_text().splitlines()
                   if line.startswith('source: .prifly/workflows/')), None)
    if source is None:
        return None
    assert source.startswith(prefix), (context, 'instruction must belong to its own package', source)
    path = package / source.removeprefix(prefix)
    assert path.resolve().is_relative_to(package.resolve()) and path.is_file(), (context, source)
    return path


def assert_same_context(left, right):
    def content(path):
        source = instruction_source(path)
        metadata = path.read_bytes().replace(
            f'.prifly/workflows/{path.parent.parent.name}/'.encode(), b'.prifly/workflows/PACKAGE/')
        return metadata, source.read_bytes() if source else None
    assert content(left) == content(right), (left, right)


def relocate_instructions(package, original_name):
    """Disposable renamed package copies carry their own Markdown files."""
    for path in (package / 'contexts').glob('*.yaml'):
        text = path.read_text()
        old = f'source: .prifly/workflows/{original_name}/'
        if old in text:
            path.write_text(text.replace(old, f'source: .prifly/workflows/{package.name}/'))
            instruction_source(path)
