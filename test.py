#!/usr/bin/env python3
"""
Custom interactive REPL with toolbox, full features:

- Expressions: printed & stored in `ans`
- Assignments (single-name): printed & stored in `ans`
- Multi-line blocks: executed; `ans` becomes replay callable (C1)
- ans() replays block output, no trailing None
- ans_list stores all previous ans values (B1: include functions)
- Exceptions: printed as "ExceptionType: message" (E3)
- exit / exit() / quit() closes terminal
- Toolbox: math, cmath, numpy, matrix/vector helpers
- clear_var() / clv() Option A (preserve toolbox)
"""

import ast
import code
import sys
import os
import numpy as np
import cmath as c
from math import *
from types import FunctionType
from typing import Optional

# ---------- REPL CORE --------------------------------------------------------

def _is_block_node(node: ast.AST) -> bool:
    return isinstance(node, (
        ast.For, ast.AsyncFor, ast.While, ast.If,
        ast.With, ast.AsyncWith, ast.Try,
        ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
        getattr(ast, "Match", ()),  # Python 3.10+
    ))

def _find_last_assign(nodes):
    for node in reversed(nodes):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            return node
    return None

def _simple_assign_name(node) -> Optional[str]:
    if isinstance(node, ast.AugAssign):
        t = node.target
        return t.id if isinstance(t, ast.Name) else None
    if isinstance(node, ast.AnnAssign):
        t = node.target
        return t.id if isinstance(t, ast.Name) else None
    if isinstance(node, ast.Assign):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            return node.targets[0].id
    return None

def _repr_for_display(value):
    try:
        return repr(value)
    except Exception:
        return "<unrepresentable>"

class AnsInteractiveConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<input>"):
        super().__init__(locals=locals, filename=filename)
        self.locals.setdefault('ans', None)
        self.locals.setdefault('ans_list', [])
        self._last_source = None

    def runsource(self, source, filename="<input>", symbol="single"):
        self._last_source = source
        return super().runsource(source, filename, symbol)

    def runcode(self, code_obj):
        try:
            old_displayhook = sys.displayhook

            def _capture_displayhook(value):
                if value is None:
                    return
                # Skip appending if value is exactly ans or ans_list themselves
                if value is self.locals.get('ans') or value is self.locals.get('ans_list'):
                    print(_repr_for_display(value))
                    return
                self.locals['ans'] = value
                self.locals['ans_list'].append(value)
                print(_repr_for_display(value))


            sys.displayhook = _capture_displayhook

            # detect direct ans() to suppress trailing None
            use_exec_instead = False
            src = self._last_source or ""
            try:
                parsed = ast.parse(src, mode='exec')
                if len(parsed.body) == 1 and isinstance(parsed.body[0], ast.Expr):
                    expr = parsed.body[0].value
                    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == 'ans':
                        use_exec_instead = True
            except SyntaxError:
                use_exec_instead = False

            if use_exec_instead:
                exec(compile(src, "<input>", "exec"), globals(), self.locals)
            else:
                exec(code_obj, globals(), self.locals)

        except SystemExit:
            raise
        except Exception as e:
            name = e.__class__.__name__
            msg = str(e)
            if msg:
                print(f"{name}: {msg}")
            else:
                print(f"{name}")
        finally:
            try:
                sys.displayhook = old_displayhook
            except Exception:
                sys.displayhook = sys.__displayhook__

            # post-execution: set ans & ans_list
            if self._last_source:
                try:
                    parsed = ast.parse(self._last_source, mode='exec')
                    if not parsed.body:
                        self._last_source = None
                        return

                    # blocks => ans = replay function
                    if any(_is_block_node(node) for node in parsed.body):
                        src_copy = self._last_source
                        def make_replay(s):
                            def replay():
                                old_hook = sys.displayhook
                                def _no_display(value):
                                    if value is None:
                                        return
                                    self.locals['ans'] = value
                                    self.locals['ans_list'].append(value)
                                    print(_repr_for_display(value))
                                sys.displayhook = _no_display
                                try:
                                    exec(compile(s, "<ans-replay>", "exec"), globals(), self.locals)
                                finally:
                                    sys.displayhook = old_hook
                            replay.__name__ = "<ans_replay>"
                            replay.__doc__ = f"Replay of block:\n{s}"
                            return replay
                        replay_func = make_replay(src_copy)
                        self.locals['ans'] = replay_func
                        self.locals['ans_list'].append(replay_func)
                        self._last_source = None
                        return

                    last_node = parsed.body[-1]
                    if isinstance(last_node, ast.Expr):
                        self._last_source = None
                        return

                    # statements only, maybe assignment
                    last_assign = _find_last_assign(parsed.body)
                    if last_assign is not None:
                        name = _simple_assign_name(last_assign)
                        if name and name in self.locals:
                            try:
                                val = self.locals[name]
                                self.locals['ans'] = val
                                self.locals['ans_list'].append(val)
                                print(_repr_for_display(val))
                            except Exception:
                                pass
                except Exception:
                    pass
            self._last_source = None

# ---------- TOOLBOX --------------------------------------------------------

# REPL namespace
REPL_LOCALS = {}

# imports
REPL_LOCALS['np'] = np
REPL_LOCALS['c'] = c
REPL_LOCALS['os'] = os
REPL_LOCALS['sys'] = sys
REPL_LOCALS['eps0'] = 8.854188e-12
REPL_LOCALS['j'] = 1j

# math names
import math as _math_module
for _name in dir(_math_module):
    if not _name.startswith("_"):
        try:
            REPL_LOCALS[_name] = getattr(_math_module, _name)
        except Exception:
            pass

# ans and ans_list
REPL_LOCALS['ans'] = None
REPL_LOCALS['ans_list'] = []

# help
def help():
    print()
    print("E_mat(n) returns identity Matrix (n x n) \n")
    print("mat_inv( mat ) return the inverse of mat \n")
    print("mat_det( mat ) get determinant of mat \n")
    print("mat_times( mat1, mat2 ) return the matrix mat1*mat2 \n")
    print("mat_solve( mat, vec ) solves for v in mat * v = vec \n")
    print("vec_cross( vec1, vec2 ) return the crossproduct \n")
REPL_LOCALS['help'] = help

# matrix / vector helpers
def E_mat(n):
    return np.identity(n)
def mat_inv(mat):
    return np.linalg.inv(mat)
def mat_det(mat):
    return np.linalg.det(mat)
def mat_times(mat1, mat2):
    return np.dot(mat1, mat2)
def mat_solve(mat, vec):
    return np.linalg.solve(mat, vec)
def vec_cross(vec1, vec2):
    return np.cross(vec1, vec2)
def vec_add(vec1, vec2):
    return np.add(vec1, vec2)
def vec_neg(vec):
    return [-i for i in vec]

REPL_LOCALS.update({
    'E_mat': E_mat,
    'mat_inv': mat_inv,
    'mat_det': mat_det,
    'mat_times': mat_times,
    'mat_solve': mat_solve,
    'vec_cross': vec_cross,
    'vec_add': vec_add,
    'vec_neg': vec_neg,
})

# clear screen
def clear():
    os.system("cls" if os.name == "nt" else "clear")
REPL_LOCALS['clear'] = clear

# clear_var & clv (Option A)
def clear_var(cls=False):
    keys = list(REPL_LOCALS.keys())
    for k in keys:
        if k in REPL_LOCALS['_clear_prot_']:
            continue
        if k == '__builtins__':
            continue
        try:
            del REPL_LOCALS[k]
        except Exception:
            pass
    if cls:
        clear()
REPL_LOCALS['clear_var'] = clear_var

def clv():
    clear_var(True)
REPL_LOCALS['clv'] = clv

# protected keys
protected = set(REPL_LOCALS.keys())
protected.add('__builtins__')
REPL_LOCALS['_clear_prot_'] = protected

# ---------- Exit / quit behavior ------------------------------------------------
def _exit_completely():
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.FreeConsole()
            os._exit(0)
        else:
            ppid = os.getppid()
            try:
                os.kill(ppid, 9)
            except Exception:
                pass
            os._exit(0)
    except Exception:
        os._exit(0)

REPL_LOCALS['exit'] = _exit_completely
REPL_LOCALS['quit'] = _exit_completely

# ---------- START REPL --------------------------------------------------------
def start_repl():
    banner = (
        "Custom Python REPL with toolbox (C1, E3, B1, assignment prints):\n"
        "- expressions: printed & stored in ans & ans_list\n"
        "- assignments: printed & stored in ans & ans_list\n"
        "- multi-line blocks: executed; ans becomes replay callable & stored in ans_list\n"
        "- calling ans() replays block output, no trailing None\n"
        "- exit / exit() / quit() closes terminal\n"
        "- Toolbox: np, c (cmath), math names, E_mat, mat_inv, mat_det, mat_times, mat_solve, vec_* helpers, clear_var(), clv(), clear()\n"
    )
    console = AnsInteractiveConsole(locals=REPL_LOCALS)
    console.interact(banner=banner)

if __name__ == "__main__":
    start_repl()
