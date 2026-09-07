import ast
import boto3

from app.remediation.validator import validate_remediation_code


def execute_remediation(code: str, boto3_module=boto3):
    """Execute validated remediation code in a restricted local scope."""

    # Validate the generated remediation code first.
    validate_remediation_code(code)

    # Parse the validated code.
    tree = ast.parse(code)

    # Remove import boto3 because the sandbox provides
    # the approved boto3 object directly.
    filtered_body = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            continue
        filtered_body.append(node)

    tree.body = filtered_body

    # Convert the modified AST back into executable code.
    safe_code = compile(tree, "<remediation>", "exec")

    # Only expose the approved boto3 object.
    safe_globals = {
        "__builtins__": {},
        "boto3": boto3_module,
    }

    safe_locals = {}

    exec(
        safe_code,
        safe_globals,
        safe_locals,
    )

    return safe_locals