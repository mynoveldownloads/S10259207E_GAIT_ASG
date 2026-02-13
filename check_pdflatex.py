import os
import subprocess

print("=" * 60)
print("MiKTeX/pdflatex Diagnostic Script")
print("=" * 60)

# Check 1: Your custom path
custom_path = r"C:\Users\mynov\Documents\MiKTeX\miktex\bin\x64\pdflatex.exe"
print(f"\n1. Checking custom path: {custom_path}")
if os.path.exists(custom_path):
    print("   ✓ File exists!")
    try:
        result = subprocess.run([custom_path, "--version"], capture_output=True, text=True, timeout=5)
        print(f"   ✓ Executable works! Version info:")
        print(f"   {result.stdout[:200]}")
    except Exception as e:
        print(f"   ✗ Error running: {e}")
else:
    print("   ✗ File NOT found!")
    # Try to find it
    print("\n   Searching for pdflatex.exe in Documents folder...")
    for root, dirs, files in os.walk(r"C:\Users\mynov\Documents\MiKTeX"):
        for file in files:
            if file == "pdflatex.exe":
                print(f"   Found at: {os.path.join(root, file)}")

# Check 2: PATH environment variable
print("\n2. Checking if pdflatex is in PATH:")
try:
    result = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True, timeout=5)
    print("   ✓ pdflatex found in PATH!")
    print(f"   {result.stdout[:200]}")
except FileNotFoundError:
    print("   ✗ pdflatex NOT in PATH")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Check 3: Common installation paths
print("\n3. Checking common MiKTeX installation paths:")
common_paths = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"),
    r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
    r"C:\Program Files (x86)\MiKTeX\miktex\bin\x64\pdflatex.exe"
]
for path in common_paths:
    exists = os.path.exists(path)
    print(f"   {'✓' if exists else '✗'} {path}")

# Check 4: Current working directory
print(f"\n4. Current working directory: {os.getcwd()}")

# Check 5: Python subprocess environment
print(f"\n5. Python PATH environment:")
path_env = os.environ.get('PATH', '')
miktex_in_path = any('miktex' in p.lower() for p in path_env.split(os.pathsep))
print(f"   MiKTeX in PATH: {'✓ Yes' if miktex_in_path else '✗ No'}")
if miktex_in_path:
    miktex_paths = [p for p in path_env.split(os.pathsep) if 'miktex' in p.lower()]
    for mp in miktex_paths:
        print(f"   - {mp}")

print("\n" + "=" * 60)
print("Diagnostic complete!")
print("=" * 60)
