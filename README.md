
# mathbug

> A deliberately confusing Python library that swaps basic arithmetic operators at runtime by transforming the caller's source code.

```python
import mathbug

mathbug.inject()

print(1 + 1)  # 0
print(1 - 1)  # 2
print(1 * 2)  # 0.5
print(1 / 3)  # 3
```

`mathbug` is a small experimental library for exploring Python's Abstract Syntax Tree (AST), source transformation, and runtime code execution. It does not modify Python's built-in numeric types or interpreter. Instead, it reads and transforms the code that appears after `mathbug.inject()`.

## Operator mappings

After `mathbug.inject()` is called, the following operators are swapped:

| Written operator | Executed as |
| ---------------- | ----------- |
| `+`            | `-`       |
| `-`            | `+`       |
| `*`            | `/`       |
| `/`            | `*`       |
| `+=`           | `-=`      |
| `-=`           | `+=`      |
| `*=`           | `/=`      |
| `/=`           | `*=`      |

For example:

```python
result = (10 + 4) * 2
```

is transformed into the equivalent of:

```python
result = (10 - 4) / 2
```

The result is therefore `3.0`.

## Requirements

- Python 3.14 or later
- A real `.py` source file

Interactive shells, `eval()`, `exec()`, and most notebook environments are not supported because `mathbug` needs to read the caller's source file.

## Installation

### Install from the local repository

Clone the repository and install it with `uv`:

```bash
git clone https://github.com/swarfte/mathbug.git
cd mathbug
uv sync
```

To use the local package in another `uv` project:

```bash
uv add --editable ../path/to/mathbug
```

Alternatively, install it with `pip`:

```bash
pip install -e ../path/to/mathbug
```

> The GitHub URL above assumes this repository is published as `swarfte/mathbug`. Update it if the final repository URL is different.

## Usage

Create a Python file, for example `example.py`:

```python
import mathbug

mathbug.inject()

print(1 + 1)
print(1 - 1)
print(1 * 2)
print(1 / 3)
```

Run it:

```bash
uv run python example.py
```

Expected output:

```text
0
2
0.5
3
```

### Variables

The transformation is not limited to numeric literals:

```python
import mathbug

mathbug.inject()

a = 10
b = 4

print(a + b)  # 6
print(a - b)  # 14
print(a * b)  # 2.5
print(a / b)  # 40
```

### Augmented assignments

Augmented assignments are transformed as well:

```python
import mathbug

mathbug.inject()

value = 10
value += 3

print(value)  # 7
```

In this example, `value += 3` is executed as `value -= 3`.

## Important placement rule

Call `mathbug.inject()` near the beginning of the file and at module level:

```python
import mathbug

mathbug.inject()

# Transformed code starts here.
```

Only top-level statements that appear after the `inject()` call are selected for transformation and re-execution by the current implementation.

Do not place it inside a function, loop, conditional block, or class body:

```python
# Not supported

def main():
    mathbug.inject()
```

## How it works

A normal `import` cannot retroactively change operators in the same file because Python parses and compiles the module before executing its statements. For that reason, merely writing `import mathbug` is not enough.

When `mathbug.inject()` runs, it:

1. Inspects the calling frame.
2. Locates the caller's `.py` file and the line containing `inject()`.
3. Reads and parses the source file into a Python AST.
4. Keeps the top-level statements after the `inject()` call.
5. Replaces `Add`, `Sub`, `Mult`, and `Div` AST operators.
6. Applies the same replacements to augmented assignments.
7. Compiles and executes the transformed AST in the caller's namespace.
8. Stops the original execution to prevent the remaining code from running twice.

In simplified form:

```text
source file
    |
    v
parse into AST
    |
    v
swap arithmetic operators
    |
    v
compile transformed AST
    |
    v
execute transformed code
```

`mathbug` therefore performs source transformation. It does not monkey-patch `int`, `float`, or Python's bytecode interpreter.

## Limitations and surprising behavior

This project intentionally changes the apparent meaning of source code. Expect unusual behavior.

### Division changes result types

```python
4 * 2
```

is transformed into:

```python
4 / 2
```

The result is `2.0`, not `2`.

### Multiplication by zero may fail

```python
10 * 0
```

becomes:

```python
10 / 0
```

and raises `ZeroDivisionError`.

### Operators on strings and collections may fail

Valid Python such as:

```python
"bug" * 3
[1, 2] + [3, 4]
```

becomes equivalent to:

```python
"bug" / 3
[1, 2] - [3, 4]
```

which raises `TypeError`.

### Imported libraries are not rewritten

`mathbug` transforms the selected statements in the caller's source file. It does not rewrite Python's standard library or every installed dependency.

### Tooling may be misleading

Editors, linters, type checkers, debuggers, coverage tools, and code reviewers see the operators that were written, not necessarily the operations eventually executed.

### The process exits after transformed execution

The current implementation raises `SystemExit(0)` after executing the transformed code. Applications that need to intercept or manage process termination may require a different integration approach.

## Intended use

`mathbug` is intended for:

- learning about Python AST transformations;
- experimenting with runtime code rewriting;
- programming puzzles;
- demonstrations and educational examples;
- harmless joke programs in controlled environments.

It is not intended for:

- production applications;
- safety-critical calculations;
- financial, medical, scientific, or security-sensitive software;
- code that must remain easy to audit and debug;
- modifying third-party programs without their users' knowledge.

## Development

### Set up the environment

```bash
uv sync
```

### Run the example

```bash
uv run python example.py
```

### Run the tests

If `pytest` has not been added yet:

```bash
uv add --dev pytest
```

Then run:

```bash
uv run pytest
```

### Project structure

```text
mathbug/
|-- src/
|   `-- mathbug/
|       |-- __init__.py
|       |-- _injector.py
|       `-- py.typed
|-- test/
|   |-- fixtures/
|   |   `-- basic_operations.py
|   `-- test_mathbug.py
|-- LICENSE
|-- pyproject.toml
|-- README.md
`-- uv.lock
```

## Build the package

Build both the source distribution and wheel:

```bash
uv build
```

The generated files will be placed in `dist/`.

To verify that the package can be built without local source overrides:

```bash
uv build --no-sources
```

You can inspect the generated artifacts with:

```bash
uv run python -m zipfile -l dist/*.whl
```

On PowerShell, if wildcard handling causes a problem, replace `dist/*.whl` with the exact wheel filename.

## Public API

The public API currently contains one function:

```python
mathbug.inject()
```

Internal implementation details live in `mathbug._injector` and may change between releases.

## Contributing

Bug reports, tests, documentation improvements, and focused pull requests are welcome.

When contributing:

1. Create a branch for the change.
2. Add or update tests where appropriate.
3. Run `uv run pytest`.
4. Confirm that `uv build --no-sources` succeeds.
5. Open a pull request describing the behavior and motivation.

## License

This project is licensed under the terms included in the [LICENSE](LICENSE) file.

## Disclaimer

This library deliberately makes Python code behave differently from how it appears. Use it only in environments where all participants understand what it does. The author is not responsible for incorrect calculations, broken programs, confused coworkers, or arithmetic-related existential crises.
