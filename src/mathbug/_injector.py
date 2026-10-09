from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import FrameType
from typing import NoReturn


class OperatorSwapTransformer(ast.NodeTransformer):
    """Swap Python arithmetic operators in an AST."""

    _replacements: dict[type[ast.operator], type[ast.operator]] = {
        ast.Add: ast.Sub,
        ast.Sub: ast.Add,
        ast.Mult: ast.Div,
        ast.Div: ast.Mult,
    }

    def _swap_operator(self, operator: ast.operator) -> ast.operator:
        replacement = self._replacements.get(type(operator))

        if replacement is None:
            return operator

        return replacement()

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        """Transform normal binary operations such as a + b."""
        self.generic_visit(node)
        node.op = self._swap_operator(node.op)
        return node

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        """Transform assignments such as value += 1."""
        self.generic_visit(node)
        node.op = self._swap_operator(node.op)
        return node


def _get_caller_frame() -> FrameType:
    """Return the frame that called mathbug.inject()."""
    current_frame = inspect.currentframe()

    if current_frame is None:
        raise RuntimeError("mathbug could not inspect the current frame")

    inject_frame = current_frame.f_back

    if inject_frame is None:
        raise RuntimeError("mathbug could not inspect inject()")

    caller_frame = inject_frame.f_back

    if caller_frame is None:
        raise RuntimeError("mathbug could not inspect the caller")

    return caller_frame


def _load_remaining_source(
    filename: str,
    inject_line: int,
) -> ast.Module:
    """Load top-level statements that appear after inject()."""
    if filename.startswith("<"):
        raise RuntimeError(
            "mathbug.inject() must be called from a real Python file. "
            "Interactive shells, eval(), exec(), and most notebooks "
            "are not supported."
        )

    source_path = Path(filename)

    if not source_path.is_file():
        raise RuntimeError(
            f"mathbug could not find the source file: {source_path}"
        )

    source = source_path.read_text(encoding="utf-8")
    syntax_tree = ast.parse(source, filename=filename)

    remaining_statements = [
        statement
        for statement in syntax_tree.body
        if getattr(statement, "lineno", 0) > inject_line
    ]

    return ast.Module(
        body=remaining_statements,
        type_ignores=[],
    )


def inject() -> NoReturn:
    """
    Replace arithmetic operators after the inject() call.

    Operator mappings:

        + becomes -
        - becomes +
        * becomes /
        / becomes *

    The remainder of the caller's source file is transformed and executed.
    The original execution is then stopped to prevent duplicate execution.
    """
    caller_frame = _get_caller_frame()
    filename = caller_frame.f_code.co_filename
    inject_line = caller_frame.f_lineno

    syntax_tree = _load_remaining_source(
        filename=filename,
        inject_line=inject_line,
    )

    transformed_tree = OperatorSwapTransformer().visit(syntax_tree)
    ast.fix_missing_locations(transformed_tree)

    compiled_code = compile(
        transformed_tree,
        filename=filename,
        mode="exec",
    )

    exec(
        compiled_code,
        caller_frame.f_globals,
        caller_frame.f_locals,
    )

    raise SystemExit(0)