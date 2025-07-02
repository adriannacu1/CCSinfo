import re

def validate_jinja_template(file_path):
    """Basic validation of Jinja2 template syntax"""
    print(f"Validating template: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Check for unmatched brackets
    open_braces = content.count('{{')
    close_braces = content.count('}}')
    if open_braces != close_braces:
        issues.append(f"Unmatched Jinja expression braces: {open_braces} opening, {close_braces} closing")
    
    open_tags = content.count('{%')
    close_tags = content.count('%}')
    if open_tags != close_tags:
        issues.append(f"Unmatched Jinja tag braces: {open_tags} opening, {close_tags} closing")
    
    # Check for common problematic patterns
    problematic_patterns = [
        (r'\{\{[^}]*\n[^}]*\}\}', 'Multi-line Jinja expressions'),
        (r'\{\%[^%]*\n[^%]*\%\}', 'Multi-line Jinja tags'),
        (r'default\s*\(\s*\[', 'Potential default filter syntax issues')
    ]
    
    for pattern, description in problematic_patterns:
        matches = re.findall(pattern, content)
        if matches:
            issues.append(f"{description}: {len(matches)} instances found")
    
    # Basic HTML structure check
    if '<html>' not in content and '<!DOCTYPE html>' not in content:
        issues.append("Missing HTML document declaration")
    
    if issues:
        print("⚠ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Basic template validation passed")
    
    return len(issues) == 0

if __name__ == '__main__':
    template_path = 'templates/admin/analytics_robust.html'
    is_valid = validate_jinja_template(template_path)
    
    if is_valid:
        print("\n🎉 Template appears to be syntactically correct!")
    else:
        print("\n❌ Template has potential issues that should be reviewed.")
