# -*- coding: utf-8 -*-
"""Read-only audit: what's dead in the code, what's clutter in the folder.
Changes nothing."""
import ast, io, os, re, collections, sys

SRC = r"X:\NextUp\nextup.py"
src = io.open(SRC, encoding="utf-8").read()
tree = ast.parse(src)

# ---------- python: defined but never used ----------------------------------
defined = {}
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        defined[node.name] = node.lineno
consts = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id.isupper():
                consts[t.id] = node.lineno

used = collections.Counter()
for node in ast.walk(tree):
    if isinstance(node, ast.Name):
        used[node.id] += 1
    elif isinstance(node, ast.Attribute):
        used[node.attr] += 1
# names inside the embedded page (strings) count too
page_text = "".join(n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str))

def mentions(name):
    return len(re.findall(r"\b%s\b" % re.escape(name), src))

print("=" * 76)
print("PYTHON: defined but never referenced")
print("=" * 76)
dead_fn = [(n, l) for n, l in sorted(defined.items(), key=lambda x: x[1])
           if used[n] <= (1 if n in used else 0) and mentions(n) <= 1]
for n, l in dead_fn:
    print("  line %-6d def %s" % (l, n))
print("  (%d)" % len(dead_fn))

dead_const = [(n, l) for n, l in sorted(consts.items(), key=lambda x: x[1])
              if mentions(n) <= 1]
print("\nPYTHON: module constants never used")
for n, l in dead_const:
    print("  line %-6d %s" % (l, n))
print("  (%d)" % len(dead_const))

# ---------- imports ----------------------------------------------------------
imported = []
for node in tree.body:
    if isinstance(node, ast.Import):
        for a in node.names:
            imported.append((a.asname or a.name.split(".")[0], node.lineno))
    elif isinstance(node, ast.ImportFrom):
        for a in node.names:
            imported.append((a.asname or a.name, node.lineno))
print("\nPYTHON: imports never used")
for name, line in imported:
    hits = len(re.findall(r"\b%s\b" % re.escape(name), src))
    if hits <= 1:
        print("  line %-6d %s" % (line, name))

# ---------- the embedded page: css classes/ids with nothing using them -------
def page_of(varname):
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == varname:
            return node.value.value
    return ""

for var in ("PAGE", "REMOTE_PAGE"):
    page = page_of(var)
    if not page:
        continue
    styles = "\n".join(re.findall(r"<style>(.*?)</style>", page, re.S))
    body = page.replace(styles, "")
    classes = set()
    for sel in re.findall(r"\.([a-zA-Z][\w-]*)", styles):
        classes.add(sel)
    ids = set(re.findall(r"#([a-zA-Z][\w-]*)", styles))
    dead_classes = sorted(c for c in classes
                          if not re.search(r"""['"\s.]%s\b""" % re.escape(c), body))
    dead_ids = sorted(i for i in ids if not re.search(r"""['"#]%s\b""" % re.escape(i), body))
    print("\n%s: CSS classes styled but never used in HTML or JS" % var)
    for c in dead_classes:
        print("  .%s" % c)
    print("  (%d of %d)" % (len(dead_classes), len(classes)))
    print("%s: CSS ids styled but never used" % var)
    for i in dead_ids:
        print("  #%s" % i)

# ---------- loose ends -------------------------------------------------------
print("\n" + "=" * 76)
print("LOOSE ENDS IN COMMENTS")
print("=" * 76)
for i, line in enumerate(src.splitlines(), 1):
    if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line):
        print("  line %-6d %s" % (i, line.strip()[:90]))
# comments naming things that no longer exist
for name in ("POOL_PER_TYPE", "unrated_pool", "view-queue", "showing-queue",
             "Next Up 0.1.1", "queue tab", "Queue tab"):
    hits = [i for i, l in enumerate(src.splitlines(), 1) if name in l]
    if hits:
        print("  mentions of %-16s at lines %s" % (name, hits[:6]))

print("\nfile: %d lines, %.0f KB" % (len(src.splitlines()), len(src.encode("utf-8")) / 1024))
