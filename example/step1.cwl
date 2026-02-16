#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: CommandLineTool

requirements:
  ShellCommandRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entryname: run-ssh-1.py
        entry: $(inputs.ssh_script_1)

baseCommand: [bash, -lc]

arguments:
  - valueFrom: |
      set -e
      if ! python3 -m pip --version >/dev/null 2>&1; then
        if python3 -m ensurepip --version >/dev/null 2>&1; then
          python3 -m ensurepip --upgrade
        else
          echo "[ERR] pip non disponibile e ensurepip assente." >&2
          exit 127
        fi
      fi
      python3 -m pip install --upgrade pip --no-cache-dir
      python3 -m pip install --no-cache-dir "cryptography>=42" "paramiko>=3.4" --user
      python3 run-ssh-1.py
    shellQuote: false

inputs:
  ssh_script_1:
    type: File

outputs: 
  dependency_output:
    type: string
    outputBinding:
      outputEval: "Finished local run"
