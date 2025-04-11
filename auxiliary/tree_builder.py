from click import Group

from utilities.scripts import cli


def build_command_tree(cmd):
    tree = {}
    if isinstance(cmd, Group):
        for name, subcmd in cmd.commands.items():
            tree[name] = build_command_tree(subcmd)
    else:
        tree = None

    return tree


def get_completions(tokens, tree=None):
    if tree is None:
        tree = build_command_tree(cli)
    for token in tokens:
        if token.startswith("-"):
            continue
        if tree and token in tree:
            tree = tree[token]
        else:
            return []
    return list(tree.keys()) if tree else []
