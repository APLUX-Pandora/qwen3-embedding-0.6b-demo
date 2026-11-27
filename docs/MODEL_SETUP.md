# Model setup

## Device requirements

- A compatible Linux device with Aidlux LMS (`sudo lms check` returns true), drivers, DSP firmware and BSP/FastRPC support.
- Python 3.10–3.12 in the Demo environment (see [Install](../README.md#1-install)).
- The SDK includes its QNN runtime libraries. Do not install QNN separately or set QNN paths.

## Targets

Pick the folder for your device's SoC:

| SoC | Target folder |
| --- | --- |
| QCS8550 | `qcs8550_qnn248` |
| QCS9075 (IQ9) | `qcs9075_qnn248` |
| QCS8625 | `qcs8625_qnn248` |
| QCS8275 (IQ8) | `qcs8275_qnn248` |

## Download

From the Demo root, in the activated environment, download the shared resources once and then one target:

```bash
hf download APLUX-Pandora/Qwen3-Embedding-0.6B --local-dir models --exclude "targets/*" --exclude "media/*" --exclude README.md --exclude .gitattributes
hf download APLUX-Pandora/Qwen3-Embedding-0.6B --local-dir models --include "targets/<target-folder>/*"
```

Run `hf auth login` first if the repository is private. Keep one target per model folder: to switch devices, move the old `targets/` folder out or download into a new folder.

## Folder layout

After the download, `models/` looks like this:

```text
models/
  models.json
  SHA256SUMS
  tokenizer.json
  token_embedding.bin
  targets/<target-folder>/embedding.bin.aidem
```

The SDK reads `models.json`, checks that the shared resources and one complete target are present, and reports what is missing. `hf download` verifies each large file's checksum.

That download check applies to freshly downloaded files. The CLI can reuse local files based on download metadata. To verify the tokenizer, token embedding table, and selected target against `SHA256SUMS`, run the following from the Demo root. Change the target to the folder you downloaded.

```bash
(
  cd models || exit
  target=qcs8625_qnn248
  grep -Fq "  targets/$target/" SHA256SUMS || exit 1
  awk -v prefix="targets/$target/" '$2 !~ /^targets\// || index($2, prefix) == 1' SHA256SUMS |
    sha256sum --check --strict
)
```

## Troubleshooting

| Message or symptom | What to do |
| --- | --- |
| Missing model target | Download the matching folder for the device's SoC. |
| Missing model resource, incorrect size, or checksum mismatch | Download the affected files again with `--force-download`, then recheck. |
| Model authorization failed | Check LMS activation before loading. |
| Input exceeds the token limit | Shorten the input text or prefix. |
