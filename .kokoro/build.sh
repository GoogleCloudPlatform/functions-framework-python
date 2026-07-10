#!/bin/bash
set -euo pipefail

cd "${KOKORO_ARTIFACTS_DIR}/git/serverless/functions-framework-python"

### Set up Airlock for Bookworm
rm -f /etc/apt/sources.list.d/* /etc/apt/sources.list
echo 'deb https://us-apt.pkg.dev/remote/artifact-foundry-prod/debian-3p-remote-bookworm bookworm main' | \
    tee -a  /etc/apt/sources.list.d/artifact-registry.list

# Set up Airlock for Python
cat > "$HOME/.pypirc" <<EOF
[distutils]
index-servers =
    python-3p-trusted

[python-3p-trusted]
repository = https://us-python.pkg.dev/artifact-foundry-prod/python-3p-trusted/
EOF

mkdir -p "$HOME/.pip"
cat > "$HOME/.pip/pip.conf" <<EOF
[global]
index-url = https://us-python.pkg.dev/artifact-foundry-prod/python-3p-trusted/simple/
EOF

### Install dependencies
pip install \
  --only-binary :all: \
  --require-hashes \
  --no-deps \
  -r .kokoro/requirements/build.txt \
  --verbose # shows it is pulling from Airlock

### Build and Publish
artifacts_dir="$KOKORO_ARTIFACTS_DIR/artifacts/"
mkdir -p "${artifacts_dir}"

readarray -t pkgs < <(find -name "pyproject.toml" -or -name "setup.py")
for pkg in "${pkgs[@]}"; do
    pkg="$(dirname "${pkg}")"
    python3 -m build --wheel "${pkg}" --outdir "${artifacts_dir}"
done

twine upload \
    --repository-url "https://us-python.pkg.dev/oss-exit-gate-prod/functions-framework-releases--pypi" \
    --verbose \
    "${artifacts_dir}/*"
