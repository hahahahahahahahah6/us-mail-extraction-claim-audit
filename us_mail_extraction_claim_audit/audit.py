"""Read-only documentation and AST inspection."""
import ast
import os
import re
from pathlib import Path
from .phrases import USMAILEXTRACTION, NOUSMAILEXTRACTION, GENERIC_NAMES


def normalize(text):
    return ' '.join(text.lower().replace("n't", ' not').replace('’nt', ' not').replace('n’t', ' not').replace('-', ' ').split())


def matches(text, phrases):
    found = []
    for phrase in sorted(phrases, key=lambda p: (-len(p), p)):
        pattern = r'\b' + re.escape(phrase) + r'\b'
        if re.search(pattern, text):
            found.append(phrase)
            text = re.sub(pattern, lambda m: ' ' * len(m.group()), text)
    return found, text


def paragraphs(text):
    lines = []
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(fence[1]) + r',}\s*$', line):
                fence = None
            lines.append((number, ''))
        elif opening:
            fence = (opening[1][0], len(opening[1]))
            lines.append((number, ''))
        else:
            lines.append((number, line))
    block = []
    start = 1
    for number, line in lines + [(len(lines) + 1, '')]:
        if line.strip():
            if not block:
                start = number
            block.append(line)
        elif block:
            yield start, normalize('\n'.join(block))
            block = []


def module_evidence(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    imports = {}
    mindee = False
    bound = set()
    definitions = set()
    def names(target):
        return {n.id for n in ast.walk(target) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split('.')[0]] = alias.name
                mindee |= alias.name.split('.')[0] == 'mindee'
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            mindee |= module.split('.')[0] == 'mindee' and not node.level
            if not node.level:
                for alias in node.names:
                    imports[alias.asname or alias.name] = module + '.' + alias.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                bound.update(names(target))
        elif isinstance(node, ast.AnnAssign):
            bound.update(names(node.target))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars:
                    bound.update(names(item.optional_vars))
    shadow = bound | definitions
    def unshadowed(expr):
        return not any(isinstance(n, ast.Name) and n.id in shadow for n in ast.walk(expr))
    def receiver_ok(expr):
        return not any(isinstance(n, ast.Name) and (n.id in definitions or (n.id in bound and n.id in imports)) for n in ast.walk(expr))
    def imported(name):
        return imports.get(name, '') if name not in shadow else ''
    clients, parses, generic = [], [], []
    products = {'UsMailV2', 'UsMailV3'}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            resolved = imported(func.id)
            if resolved == 'mindee.Client':
                clients.append(node.lineno)
            if resolved.rsplit('.', 1)[-1] in GENERIC_NAMES and resolved.rsplit('.', 1)[-1] not in definitions:
                generic.append(node.lineno)
        elif isinstance(func, ast.Attribute):
            if func.attr in GENERIC_NAMES and func.attr not in definitions and receiver_ok(func.value):
                generic.append(node.lineno)
            if func.attr == 'Client' and isinstance(func.value, ast.Name) and func.value.id == 'mindee' and unshadowed(func.value) and 'Client' not in definitions:
                clients.append(node.lineno)
            if func.attr == 'parse' and 'parse' not in definitions:
                args = list(node.args) + [kw.value for kw in node.keywords]
                for arg in args:
                    product = arg.id if isinstance(arg, ast.Name) else arg.attr if isinstance(arg, ast.Attribute) else None
                    # Resolve direct imported aliases as well as literal product names.
                    if isinstance(arg, ast.Name) and imported(arg.id):
                        product = imported(arg.id).rsplit('.', 1)[-1]
                    if product in products and product not in definitions and unshadowed(arg) and receiver_ok(func.value):
                        parses.append(node.lineno)
    result = [{'route': 'generic', 'line': line} for line in generic]
    if mindee and clients and parses:
        result.extend({'route': 'mindee', 'line': line} for line in parses)
    return result


def audit(root, ignore=()):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise OSError('Repository must be a readable directory')
    claims, production, tests = [], [], []
    prefixes = [Path(p).as_posix().strip('./') for p in ignore]
    def ignored(rel):
        value = rel.as_posix()
        return any(value == p or value.startswith(p + '/') for p in prefixes)
    def walk_error(error):
        raise error
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        base = Path(directory)
        dirs[:] = sorted(d for d in dirs if not (base/d).is_symlink() and not ignored((base/d).relative_to(root)))
        for filename in sorted(files):
            path = base / filename
            rel = path.relative_to(root)
            if path.is_symlink() or ignored(rel):
                continue
            if rel.as_posix() == 'README.md' or (path.suffix == '.md' and 'docs' in rel.parts[:-1]):
                for line, text in paragraphs(path.read_text(encoding='utf-8')):
                    negative, remaining = matches(text, NOUSMAILEXTRACTION)
                    positive, _ = matches(remaining, USMAILEXTRACTION)
                    for family, phrases in [('NOUSMAILEXTRACTION', negative), ('USMAILEXTRACTION', positive)]:
                        claims.extend({'family': family, 'phrase': p, 'path': rel.as_posix(), 'line': line} for p in phrases)
            if path.suffix != '.py' or {'fixtures', 'docs', 'examples'} & set(rel.parts[:-1]):
                continue
            is_test = 'tests' in rel.parts[:-1] or filename.startswith('test_') or filename.endswith('_test.py')
            evidence = module_evidence(path.read_text(encoding='utf-8'))
            (tests if is_test else production).extend(dict(e, path=rel.as_posix()) for e in evidence)
    findings = []
    for family, rule in [('USMAILEXTRACTION', 'documented-us-mail-extraction-claim-false'), ('NOUSMAILEXTRACTION', 'documented-no-us-mail-extraction-claim-false')]:
        relevant = [c for c in claims if c['family'] == family]
        if relevant and ((family == 'USMAILEXTRACTION' and not production) or (family == 'NOUSMAILEXTRACTION' and production)):
            severity = 'MEDIUM' if family == 'USMAILEXTRACTION' and tests else 'HIGH'
            message = 'Claim lacks production evidence' if family == 'USMAILEXTRACTION' else 'Denial contradicts production evidence'
            if severity == 'MEDIUM':
                message += '; evidence exists only in tests'
            findings.append({'rule': rule, 'severity': severity, 'message': message, 'claims': relevant})
    return {'verdict': 'FAIL' if findings else 'PASS', 'findings': findings, 'claims': claims, 'evidence': {'production': production, 'tests': tests}}
