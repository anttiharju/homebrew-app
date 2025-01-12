#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import re
from typing import Dict

@dataclass
class FormulaConfig:
    """Configuration for generating a Homebrew formula."""
    app_name: str
    description: str
    homepage: str
    url: str
    go_version: str

def calculate_sha256(url: str) -> str:
    """Calculate SHA256 hash of file at given URL."""
    with tempfile.NamedTemporaryFile() as tmp:
        try:
            subprocess.run(['curl', '-L', '-o', tmp.name, url], 
                         check=True, capture_output=True)
            result = subprocess.run(['shasum', '-a', '256', tmp.name],
                                  capture_output=True, text=True, check=True)
            return result.stdout.split()[0]
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to calculate SHA256: {e}")

def to_pascal_case(kebab_str: str) -> str:
    """Convert kebab-case string to PascalCase."""
    return ''.join(word.capitalize() for word in kebab_str.split('-'))

def extract_repo(url: str) -> str:
    """Extract repository path from GitHub URL."""
    if match := re.search(r'(github\.com/[^/]+/[^/]+)/', url):
        return match.group(1)
    raise ValueError("Could not extract repo from GitHub URL")

def extract_version(url: str) -> str:
    """Extract version from GitHub release URL."""
    if match := re.search(r'/tags/([^/]+)\.tar\.gz$', url):
        return match.group(1)
    raise ValueError("Could not extract version from URL")

def generate_replacements(config: FormulaConfig) -> Dict[str, str]:
    """Generate replacement dictionary for template variables."""
    return {
        "CLASS_NAME": to_pascal_case(config.app_name),
        "DESCRIPTION": config.description,
        "HOMEPAGE": config.homepage,
        "URL": config.url,
        "SHA256": calculate_sha256(config.url),
        "REPO": extract_repo(config.url),
        "GO_VERSION": config.go_version,
        "APP_NAME": config.app_name,
        "VERSION": extract_version(config.url)
    }

def create_formula(config: FormulaConfig, script_dir: Path, template_name: str) -> None:
    """Create Homebrew formula from a template.
    
    Args:
        config: Formula configuration
        script_dir: Directory containing script and templates
        template_name: Name of the template file to use
    """
    template_path = script_dir / template_name
    formula_dir = script_dir.parent / "Formula"
    formula_dir.mkdir(exist_ok=True)

    replacements = generate_replacements(config)
    template = template_path.read_text()
    
    for key, value in replacements.items():
        template = template.replace(f"${key}", value)
    
    (formula_dir / f"{config.app_name}.rb").write_text(template)

def main() -> None:
    """Main entry point."""
    config = FormulaConfig(
        app_name="vmatch-golangci-lint",
        description="Wrapper that automatically calls the golangci-lint version matching your project",
        homepage="https://anttiharju.dev/vmatch/",
        url="https://github.com/anttiharju/vmatch/archive/refs/tags/build5.tar.gz",
        go_version="1.23"
    )
    
    create_formula(config, Path(__file__).parent, "go-formula-template")

if __name__ == "__main__":
    main()
