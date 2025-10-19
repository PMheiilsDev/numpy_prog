import code
import ast

ans = None

def store_last_result(value):
    global ans
    ans = value
    print(value)

def func():
    print("This is a sample function.")

class TrackingConsole(code.InteractiveConsole):
    def runsource(self, source, filename="<input>", symbol="single"):
        try:
            global ans
            try:
                # Parse the input
                tree = ast.parse(source, mode='exec')
            except SyntaxError:
                # Let the default handler deal with invalid code
                return super().runsource(source, filename, symbol)

            # Check if last node is an expression
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                # Evaluate the expression and store result
                expr_code = compile(ast.Expression(tree.body[-1].value), filename, 'eval')
                result = eval(expr_code, globals(), self.locals)
                store_last_result(result)
                # Remove last expression before executing full code
                tree.body.pop()
                if tree.body:
                    exec(compile(tree, filename, 'exec'), globals(), self.locals)
            else:
                # Check for assignments
                for node in tree.body:
                    if isinstance(node, ast.Assign):
                        # Evaluate right-hand side of assignment
                        value = eval(compile(ast.Expression(node.value), filename, 'eval'), globals(), self.locals)
                        store_last_result(value)
                # Execute full statement
                exec(compile(tree, filename, 'exec'), globals(), self.locals)

            return False  # indicate successful execution

        except Exception as e:
            self.showtraceback()
            return True  # indicate an error occurred

# Start custom interactive console
console = TrackingConsole()
console.interact()
