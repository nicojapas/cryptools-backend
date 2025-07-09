import os
import shutil
import subprocess


def get_installed_packages(layer_path):
    """Get a dictionary of installed packages and their versions."""
    result = subprocess.run(
        ["pip", "list", "--format=freeze", "--path", layer_path],
        capture_output=True,
        text=True,
    )
    installed_packages = {}
    for line in result.stdout.splitlines():
        if "==" in line:
            package, version = line.split("==")
            installed_packages[package] = version
    return installed_packages


def get_required_packages(requirements_file):
    """Get a dictionary of required packages and their versions."""
    required_packages = {}
    with open(requirements_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "==" in line:
                    package, version = line.split("==")
                    required_packages[package] = version
                else:
                    required_packages[line] = None  # No version specified
    return required_packages


def packages_are_up_to_date(installed_packages, required_packages):
    """Check if installed packages match the required versions."""
    for package, required_version in required_packages.items():
        if package not in installed_packages:
            return False  # Package is not installed
        if required_version and installed_packages[package] != required_version:
            return False  # Installed version does not match required version
    return True


# Path to the layers directory
LAYERS_DIR = os.path.join("cryptools_backend", "layers")

# Iterate through each subfolder in the layers directory
for layer_name in os.listdir(LAYERS_DIR):
    layer_path = os.path.join(LAYERS_DIR, layer_name)

    # Skip if it's not a directory
    if not os.path.isdir(layer_path):
        continue

    # Path to the requirements.txt file in the layer
    requirements_file = os.path.join(layer_path, "requirements.txt")

    # Skip if there's no requirements.txt file
    if not os.path.exists(requirements_file):
        print(f"Skipping {layer_name}: No requirements.txt found.")
        continue

    # Path to the python subfolder in the layer
    python_folder = os.path.join(layer_path, "python")

    # Create the python subfolder if it doesn't exist
    os.makedirs(python_folder, exist_ok=True)

    # Get installed and required packages
    installed_packages = get_installed_packages(python_folder)
    required_packages = get_required_packages(requirements_file)

    # Check if packages are up to date
    if packages_are_up_to_date(installed_packages, required_packages):
        print(f"{layer_name} dependencies are already up to date.")
        continue

    # Clean up old dependencies in the python subfolder
    print(f"Cleaning up {layer_name}...")
    for item in os.listdir(python_folder):
        item_path = os.path.join(python_folder, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

    # Install new dependencies into the python subfolder
    print(f"Installing dependencies for {layer_name}...")
    subprocess.run(["pip", "install", "--no-user", "-r", requirements_file, "-t", python_folder], check=True)

    # Clean up unnecessary files in the python subfolder
    print(f"Cleaning up unnecessary files in {layer_name}...")
    for root, dirs, files in os.walk(python_folder):
        for file in files:
            if file.endswith(".pyc") or file.endswith(".dist-info"):
                os.remove(os.path.join(root, file))
        for dir in dirs:
            if dir == "__pycache__":
                shutil.rmtree(os.path.join(root, dir))

print("Dependencies checked and installed successfully!")