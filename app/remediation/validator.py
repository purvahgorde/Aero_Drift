import ast


ALLOWED_IMPORTS = {"boto3"}

ALLOWED_CALLS = {
    "boto3.client",
    "ec2.revoke_security_group_ingress",
}


class UnsafeRemediationError(ValueError):
    """Raised when generated remediation code is not allowed."""


def validate_remediation_code(code: str) -> bool:
    """Validate generated remediation code using Python AST."""

    tree = ast.parse(code)

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_IMPORTS:
                    raise UnsafeRemediationError(
                        f"Import not allowed: {alias.name}"
                    )

        elif isinstance(node, ast.ImportFrom):
            raise UnsafeRemediationError(
                "from-import statements are not allowed"
            )

        elif isinstance(node, ast.Call):
            function_name = _get_call_name(node.func)

            if function_name not in ALLOWED_CALLS:
                raise UnsafeRemediationError(
                    f"Function call not allowed: {function_name}"
                )

        elif isinstance(node, ast.Attribute):
            continue

        elif isinstance(
            node,
            (
                ast.Module,
                ast.Assign,
                ast.Name,
                ast.Load,
                ast.Constant,
                ast.Expr,
                ast.keyword,
                ast.List,
                ast.Dict,
            ),
        ):
            continue

    return True


def _get_call_name(node):
    """Convert an AST call target into a dotted name."""

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _get_call_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return ""