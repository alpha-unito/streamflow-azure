#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: Workflow

requirements:
  InlineJavascriptRequirement: {}

inputs:
  ssh_script_1: File
  ssh_script_2: File
  ssh_script_3: File
  ssh_script_4: File
  streamflow_path:
    type: string
  streamflow_workflow:
    type: string
  streamflow_outdir:
    type: string
  streamflow_tmpdir:
    type: string

outputs: []

steps:
  step1:
    run: step1.cwl
    in:
      ssh_script_1: ssh_script_1
    out: [dependency_output]
  step2:
    in:
      streamflow_path: streamflow_path
      streamflow_workflow: streamflow_workflow
      streamflow_outdir: streamflow_outdir
      streamflow_tmpdir: streamflow_tmpdir
      dependency_input: step1/dependency_output
    run: step2.cwl
    out: [dependency_output]
  step3:
    run: step3.cwl
    in:
      ssh_script_2: ssh_script_2
    out: [dependency_output]
  step4:
    run: step4.cwl
    in:
      ssh_script_3: ssh_script_3
      dependency_input: step2/dependency_output
      dependency_input_1: step3/dependency_output
    out: [dependency_output]
  step5:
    run: step5.cwl
    in:
      ssh_script_4: ssh_script_4
      dependency_input: step4/dependency_output
    out: [dependency_output]