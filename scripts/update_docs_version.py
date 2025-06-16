#!/usr/bin/env python3
"""Update documentation with version information from git tags.

Script to update documentation with version information from git tags.
This script is run automatically by GitHub Actions on releases.
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path


def run_command(cmd):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{cmd}': {e}")
        return None


def get_version_info():
    """Get version information from git and package."""
    info = {}

    # Get package version
    try:
        import webextract

        info["package_version"] = webextract.__version__
    except ImportError:
        info["package_version"] = "dev"

    # Get git tag
    git_tag = run_command("git describe --tags --exact-match 2>/dev/null")
    if git_tag:
        info["git_tag"] = git_tag
        info["is_release"] = True
    else:
        info["git_tag"] = "main"
        info["is_release"] = False

    # Get commit info
    info["commit_sha"] = run_command("git rev-parse --short HEAD")
    info["commit_date"] = run_command("git log -1 --format=%cd --date=short")
    info["commit_datetime"] = datetime.now().isoformat()

    # Get all tags for version history
    all_tags = run_command("git tag --sort=-version:refname")
    info["all_versions"] = all_tags.split("\n") if all_tags else []

    return info


def update_readme_badges(info):
    """Update README.md with current version badges."""
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("README.md not found")
        return

    content = readme_path.read_text()

    # Update PyPI version badge
    pypi_pattern = (
        r"\[!\[PyPI version\]\(https://badge\.fury\.io/py/llm-webextract\.svg\)\]"
        r"\(https://badge\.fury\.io/py/llm-webextract\)"
    )
    pypi_replacement = (
        f"[![PyPI version](https://badge.fury.io/py/llm-webextract.svg)]"
        f'(https://pypi.org/project/llm-webextract/{info["package_version"]}/)'
    )
    content = re.sub(pypi_pattern, pypi_replacement, content)

    # Add version info to the top
    version_info = (
        f"<!-- Version Info: {info['package_version']} | "
        f"Tag: {info['git_tag']} | Updated: {info['commit_date']} -->"
    )

    if "<!-- Version Info:" not in content:
        # Add version info after the first line
        lines = content.split("\n")
        lines.insert(1, version_info.strip())
        content = "\n".join(lines)
    else:
        # Update existing version info
        content = re.sub(r"<!-- Version Info:.*?-->", version_info.strip(), content)

    readme_path.write_text(content)
    print(f"✅ Updated README.md with version {info['package_version']}")


def create_version_json(info):
    """Create a JSON file with version information for documentation."""
    version_data = {
        "current_version": info["package_version"],
        "git_tag": info["git_tag"],
        "is_release": info["is_release"],
        "commit_sha": info["commit_sha"],
        "commit_date": info["commit_date"],
        "updated_at": info["commit_datetime"],
        "all_versions": info["all_versions"][:10],  # Last 10 versions
        "documentation_url": "https://himashaherath.github.io/webextract",
        "pypi_url": f"https://pypi.org/project/llm-webextract/{info['package_version']}/",
        "github_release_url": (
            f"https://github.com/HimashaHerath/webextract/releases/tag/{info['git_tag']}"
            if info["is_release"]
            else None
        ),
    }

    # Create docs directory if it doesn't exist
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    version_file = docs_dir / "version.json"
    version_file.write_text(json.dumps(version_data, indent=2))
    print(f"✅ Created {version_file} with version information")

    return version_data


def update_api_reference(info):
    """Update API reference with current version."""
    api_ref_path = Path("API_REFERENCE.md")
    if not api_ref_path.exists():
        print("API_REFERENCE.md not found, skipping")
        return

    content = api_ref_path.read_text()

    # Add version header if not present
    version_header = (
        f"> **Version:** {info['package_version']} | "
        f"**Release:** {info['git_tag']} | **Updated:** {info['commit_date']}\n\n"
    )

    if "> **Version:**" not in content:
        # Add after the first heading
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#"):
                lines.insert(i + 1, version_header.strip())
                break
        content = "\n".join(lines)
    else:
        # Update existing version info
        content = re.sub(r"> \*\*Version:\*\*.*?\n\n", version_header, content, flags=re.DOTALL)

    api_ref_path.write_text(content)
    print(f"✅ Updated API_REFERENCE.md with version {info['package_version']}")


def create_changelog_link(info):
    """Create a symbolic link or copy of CHANGELOG.md for documentation."""
    changelog_source = Path("CHANGELOG.md")
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    changelog_dest = docs_dir / "changelog.md"

    if changelog_source.exists():
        # Copy changelog to docs directory
        changelog_dest.write_text(changelog_source.read_text())
        print(f"✅ Copied CHANGELOG.md to {changelog_dest}")


def main():
    """Update all documentation with version info."""
    print("🔄 Updating documentation with version information...")

    # Get version information
    info = get_version_info()
    print(f"📦 Package Version: {info['package_version']}")
    print(f"🏷️ Git Tag: {info['git_tag']}")
    print(f"🚀 Is Release: {info['is_release']}")
    print(f"📝 Commit: {info['commit_sha']} ({info['commit_date']})")

    # Update documentation files
    update_readme_badges(info)
    version_data = create_version_json(info)
    update_api_reference(info)
    create_changelog_link(info)

    print("\n✅ Documentation update complete!")
    print(f"📚 Documentation URL: {version_data['documentation_url']}")
    if version_data["github_release_url"]:
        print(f"🚀 Release URL: {version_data['github_release_url']}")
    print(f"📦 PyPI URL: {version_data['pypi_url']}")


if __name__ == "__main__":
    main()
