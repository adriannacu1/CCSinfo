#!/usr/bin/env python3
"""
Simple test to verify analytics template syntax
"""

def test_template_syntax():
    """Test template for basic syntax issues"""
    try:
        with open("templates/admin/analytics.html", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Test for specific broken patterns
        broken_patterns = [
            "| safe\n        }}",  # Most common issue
            "| tojson | safe\n}}", # Another variant
            "default (",          # Space after default
        ]
        
        issues = []
        for pattern in broken_patterns:
            if pattern in content:
                issues.append(f"Found broken pattern: {repr(pattern)}")
        
        # Check for unmatched {{ }}
        open_double = content.count('{{')
        close_double = content.count('}}')
        
        if open_double != close_double:
            issues.append(f"Unmatched Jinja2 brackets: {open_double} {{ vs {close_double} }}")
        
        # Check for JavaScript function completeness
        if 'initializeCharts()' in content and content.count('{') != content.count('}'):
            issues.append("Unmatched JavaScript braces")
        
        if issues:
            print("❌ Syntax issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✅ No syntax issues found!")
            print("✅ Analytics template is ready to use")
            return True
            
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False

if __name__ == "__main__":
    print("=== Analytics Template Syntax Check ===")
    test_template_syntax()
