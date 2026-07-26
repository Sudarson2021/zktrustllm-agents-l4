#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
TOOLS_ROOT="${TOOLS_ROOT:-${REPO_ROOT}/.tools/permissioned}"
ETCD_VERSION="${ETCD_VERSION:-3.5.17}"
BESU_VERSION="${BESU_VERSION:-24.5.4}"
BESU_SHA256="${BESU_SHA256:-2d2082bd2ebebdc24a45007dd3c9c45ea9b430ef8a4b6025be4ef3376317f5d7}"

case "$(uname -m)" in
  x86_64) ETCD_ARCH="amd64" ;;
  aarch64|arm64) ETCD_ARCH="arm64" ;;
  *)
    echo "Unsupported architecture: $(uname -m)" >&2
    exit 1
    ;;
esac

for command_name in curl tar sha256sum java; do
  command -v "${command_name}" >/dev/null 2>&1 || {
    echo "Missing prerequisite: ${command_name}" >&2
    exit 1
  }
done

JAVA_MAJOR="$(
  java -version 2>&1 |
    awk -F'[\".]' '/version/ { if ($2 == "1") print $3; else print $2; exit }'
)"
if [[ -z "${JAVA_MAJOR}" || "${JAVA_MAJOR}" -lt 17 ]]; then
  echo "Besu ${BESU_VERSION} requires Java 17 or newer; found: $(java -version 2>&1 | head -1)" >&2
  exit 1
fi

mkdir -p "${TOOLS_ROOT}"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/zktrustllm-permissioned-install.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

ETCD_DIR="${TOOLS_ROOT}/etcd-v${ETCD_VERSION}"
if [[ ! -x "${ETCD_DIR}/etcd" || ! -x "${ETCD_DIR}/etcdctl" ]]; then
  ETCD_ARCHIVE="etcd-v${ETCD_VERSION}-linux-${ETCD_ARCH}.tar.gz"
  ETCD_URL="https://github.com/etcd-io/etcd/releases/download/v${ETCD_VERSION}/${ETCD_ARCHIVE}"
  SUMS_URL="https://github.com/etcd-io/etcd/releases/download/v${ETCD_VERSION}/SHA256SUMS"
  echo "Downloading etcd ${ETCD_VERSION} (${ETCD_ARCH})..."
  curl --fail --location --retry 3 --output "${TMP_ROOT}/${ETCD_ARCHIVE}" "${ETCD_URL}"
  curl --fail --location --retry 3 --output "${TMP_ROOT}/ETCD_SHA256SUMS" "${SUMS_URL}"
  (
    cd "${TMP_ROOT}"
    grep " ${ETCD_ARCHIVE}\$" ETCD_SHA256SUMS | sha256sum --check -
  )
  tar --no-same-owner -xzf "${TMP_ROOT}/${ETCD_ARCHIVE}" -C "${TMP_ROOT}"
  rm -rf "${ETCD_DIR}"
  mv "${TMP_ROOT}/etcd-v${ETCD_VERSION}-linux-${ETCD_ARCH}" "${ETCD_DIR}"
fi

BESU_DIR="${TOOLS_ROOT}/besu-${BESU_VERSION}"
if [[ ! -x "${BESU_DIR}/bin/besu" ]]; then
  BESU_ARCHIVE="besu-${BESU_VERSION}.tar.gz"
  BESU_URL="https://github.com/hyperledger/besu/releases/download/${BESU_VERSION}/${BESU_ARCHIVE}"
  echo "Downloading Hyperledger Besu ${BESU_VERSION}..."
  curl --fail --location --retry 3 --output "${TMP_ROOT}/${BESU_ARCHIVE}" "${BESU_URL}"
  BESU_ARCHIVE_SHA256="$(sha256sum "${TMP_ROOT}/${BESU_ARCHIVE}" | awk '{print $1}')"
  if [[ "${BESU_ARCHIVE_SHA256}" != "${BESU_SHA256}" ]]; then
    echo "Besu archive checksum mismatch." >&2
    echo "Expected: ${BESU_SHA256}" >&2
    echo "Observed: ${BESU_ARCHIVE_SHA256}" >&2
    exit 1
  fi
  tar --no-same-owner -xzf "${TMP_ROOT}/${BESU_ARCHIVE}" -C "${TMP_ROOT}"
  rm -rf "${BESU_DIR}"
  mv "${TMP_ROOT}/besu-${BESU_VERSION}" "${BESU_DIR}"
  printf '%s  %s\n' "${BESU_ARCHIVE_SHA256}" "${BESU_ARCHIVE}" \
    > "${BESU_DIR}/SOURCE_ARCHIVE_SHA256.txt"
fi

ln -sfn "etcd-v${ETCD_VERSION}" "${TOOLS_ROOT}/etcd"
ln -sfn "besu-${BESU_VERSION}" "${TOOLS_ROOT}/besu"

cat > "${TOOLS_ROOT}/VERSIONS.txt" <<EOF
etcd_version=$("${ETCD_DIR}/etcd" --version | awk '/etcd Version/ {print $3; exit}')
etcd_sha256=$(sha256sum "${ETCD_DIR}/etcd" | awk '{print $1}')
etcdctl_sha256=$(sha256sum "${ETCD_DIR}/etcdctl" | awk '{print $1}')
besu_version=$("${BESU_DIR}/bin/besu" --version | head -1)
besu_sha256=$(sha256sum "${BESU_DIR}/bin/besu" | awk '{print $1}')
java_version=$(java -version 2>&1 | head -1)
EOF

echo
echo "Installed clients under ${TOOLS_ROOT}"
cat "${TOOLS_ROOT}/VERSIONS.txt"
