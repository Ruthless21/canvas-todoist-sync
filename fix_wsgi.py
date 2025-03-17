#!/usr/bin/env python3
"""
Script to fix the WSGI error where 'e' is not defined.
Run this on PythonAnywhere to fix the issue.
"""
import os
import re

# Path to the WSGI file
WSGI_PATH = '/var/www/www_syncmyassignments_com_wsgi.py'

def fix_wsgi_file():
    """Fix the WSGI file where 'e' is not defined."""
    # First check if the file exists
    if not os.path.exists(WSGI_PATH):
        print(f"❌ WSGI file not found at: {WSGI_PATH}")
        print("Please update the script with the correct path to your WSGI file.")
        return False

    # Read the WSGI file
    with open(WSGI_PATH, 'r') as f:
        content = f.read()

    # Check for the error pattern - a reference to str(e) without a defined 'e'
    error_line_match = re.search(r'<p><strong>Error:</strong>\s*{str\(e\)}</p>', content)
    if not error_line_match:
        print("❓ Could not find the exact error pattern in your WSGI file.")
        print("Please check line 97 manually for a reference to '{str(e)}'")
        return False

    # Get the context around the error
    error_line = error_line_match.group(0)
    line_num = content.count('\n', 0, error_line_match.start()) + 1
    print(f"Found error on line {line_num}: {error_line}")

    # Look for a try-except block nearby
    try_except_block = re.search(r'try:.*?except.*?:.*?' + re.escape(error_line), 
                                content, re.DOTALL)

    if try_except_block:
        # Check if the except block captures the exception
        except_clause = re.search(r'except.*?:', try_except_block.group(0))
        if except_clause:
            except_str = except_clause.group(0)
            
            # Check if exception is captured as a variable
            if ' as ' not in except_str:
                # Fix: Add 'as e' to the except clause
                new_except = except_str.replace(':', ' as e:', 1)
                fixed_content = content.replace(except_str, new_except)
                
                print(f"✅ Fixed WSGI file. Changed '{except_str}' to '{new_except}'")
                
                # Write the fixed content back
                with open(WSGI_PATH + '.fixed', 'w') as f:
                    f.write(fixed_content)
                
                print(f"✅ Wrote fixed WSGI file to: {WSGI_PATH}.fixed")
                print("To apply the fix, run:")
                print(f"cp {WSGI_PATH}.fixed {WSGI_PATH}")
                
                return True
            else:
                # The except already has a variable, but it might not be 'e'
                var_name = except_str.split(' as ')[1].strip(':')
                if var_name != 'e':
                    # We need to change the error reference instead
                    fixed_line = error_line.replace('str(e)', f'str({var_name})')
                    fixed_content = content.replace(error_line, fixed_line)
                    
                    print(f"✅ Fixed WSGI file. Changed reference from 'e' to '{var_name}'")
                    
                    # Write the fixed content back
                    with open(WSGI_PATH + '.fixed', 'w') as f:
                        f.write(fixed_content)
                    
                    print(f"✅ Wrote fixed WSGI file to: {WSGI_PATH}.fixed")
                    print("To apply the fix, run:")
                    print(f"cp {WSGI_PATH}.fixed {WSGI_PATH}")
                    
                    return True
                else:
                    print("⚠️ Exception is already captured as 'e', but the error still occurs.")
                    print("This suggests there might be multiple try-except blocks or scope issues.")
                    print("Please check the WSGI file manually.")
                    return False
    
    # If we can't find a specific pattern to fix, create a more generalized fix
    # We'll add a generic except Exception as e block around the error
    lines = content.split('\n')
    error_line_idx = line_num - 1
    
    # Look at the indentation of the error line
    match = re.match(r'^(\s*)', lines[error_line_idx])
    indent = match.group(1) if match else ''
    
    # Insert a try-except block around the line with the error
    lines.insert(error_line_idx, f"{indent}try:")
    # Increase indentation for the error line
    lines[error_line_idx + 1] = indent + "    " + lines[error_line_idx + 1].lstrip()
    # Add except block after
    lines.insert(error_line_idx + 2, f"{indent}except Exception as e:")
    # Copy the same line but with proper indentation and error handling
    lines.insert(error_line_idx + 3, indent + "    " + lines[error_line_idx + 1].lstrip())
    
    fixed_content = '\n'.join(lines)
    
    # Write the fixed content back
    with open(WSGI_PATH + '.fixed', 'w') as f:
        f.write(fixed_content)
    
    print(f"✅ Created a more general fix by adding a try-except block")
    print(f"✅ Wrote fixed WSGI file to: {WSGI_PATH}.fixed")
    print("To apply the fix, run:")
    print(f"cp {WSGI_PATH}.fixed {WSGI_PATH}")
    
    return True

# Main part of the script
if __name__ == "__main__":
    print("=" * 70)
    print(" WSGI Error Fixer ".center(70, "="))
    print("=" * 70)
    print(f"Attempting to fix WSGI file: {WSGI_PATH}")
    
    success = fix_wsgi_file()
    
    if success:
        print("\nAfter applying the fix, reload your web app on PythonAnywhere!")
    else:
        print("\nCould not automatically fix the WSGI file.")
        print("If you need to fix it manually, locate the line with '{str(e)}' and ensure")
        print("the exception is properly captured as 'e' in a surrounding except block.")
        
        print("\nTypical fix pattern:")
        print("try:")
        print("    # code that might fail")
        print("except Exception as e:  # Make sure the exception is captured as 'e'")
        print("    # error handling code that uses 'e'")
    
    # Also recommend installing email_validator
    print("\n" + "=" * 70)
    print(" Email Validator Package ".center(70, "="))
    print("=" * 70)
    print("Don't forget to install the email_validator package:")
    print("pip install --user email_validator")
    print("\nThen reload your web app from the PythonAnywhere dashboard.") 