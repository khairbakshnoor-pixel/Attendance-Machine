"""Set an admin password without putting plaintext in command history or .env."""
import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.security import hash_password


def main():
    password = getpass.getpass("New administrator password (minimum 12 characters): ")
    if password != getpass.getpass("Confirm password: "):
        raise ValueError("Passwords do not match.")
    encoded = hash_password(password)
    target = ROOT / ".env"
    source = target if target.exists() else ROOT / ".env.example"
    lines = [line for line in source.read_text().splitlines() if not line.startswith("ADMIN_PASSWORD_HASH=")]
    # Single quotes prevent dotenv interpolation and preserve the hash exactly.
    lines.append(f"ADMIN_PASSWORD_HASH='{encoded}'")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Administrator password configured. Restart Streamlit if it is running.")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
