import ast

class DataFlowAnalyzer:

    def __init__(self, filepath):
        self.filepath = filepath
        self.tree = None
        self.assignments = []
        self.flow = []

    def extract_parse_tree(self):
        with open(self.filepath, 'r') as file:
            self.tree = ast.parse(file.read())

    def parse_assignments(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                self.assignments.append(node)

    def extract_assignment_operations(self):
        sources = {}

        for node in self.assignments:
            target = node.targets[0]
            value = node.value

            if isinstance(target, ast.Tuple) and isinstance(value, ast.Tuple):
                for t, v in zip(target.elts, value.elts):
                    if isinstance(t, ast.Name) and isinstance(v, ast.Constant):
                        sources[t.id] = str(v.value)
                    elif isinstance(t, ast.Name) and isinstance(v, ast.Name):
                        sources[t.id] = v.id

            elif isinstance(target, ast.Name):
                name = target.id
                # res = s1 * repeat
                if isinstance(value, ast.BinOp):
                    if isinstance(value.right, ast.Name):
                        sources[name] = value.right.id
                    elif isinstance(value.left, ast.Name):
                        sources[name] = value.left.id

                # data = repeatString(val1, op) - map args to params that feed res
                elif isinstance(value, ast.Call):
                    func_name = value.func.id if isinstance(value.func, ast.Name) else None
                    for n in ast.walk(self.tree):
                        if isinstance(n, ast.FunctionDef) and n.name == func_name:
                            for param, arg in zip(n.args.args, value.args):
                                if isinstance(arg, ast.Name) and sources.get("res") == param.arg:
                                    sources["res"] = arg.id
                            sources[name] = "res"
                            break

        start = None
        for src in sources.values():
            if src not in sources and src.isdigit():
                start = src
                break

        self.flow = []
        if start is None:
            return

        current = start
        self.flow.append(current)
        while True:
            nxt = None
            for var, src in sources.items():
                if src == current:
                    nxt = var
                    break
            if nxt is None:
                break
            self.flow.append(nxt)
            current = nxt

    def generate_flow(self):
        return "->".join(self.flow)

    def run(self):
        self.extract_parse_tree()
        self.parse_assignments()
        self.extract_assignment_operations()
        return self.generate_flow()


if __name__ == "__main__":
    analyzer = DataFlowAnalyzer("E3/repeat.py")
    print(analyzer.run())
