#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["/bin/sh", "-c"]

requirements:
  - class: InlineJavascriptRequirement

inputs: 
  streamflow_path:
    type: string
  streamflow_workflow:
    type: string
  dependency_input:
    type: string
  streamflow_outdir:
    type: string
  streamflow_tmpdir:
    type: string

outputs: 
  dependency_output:
    type: string

arguments:
  - valueFrom: "TMPDIR=$(inputs.streamflow_tmpdir) $(inputs.streamflow_path) run $(inputs.streamflow_workflow) --outdir $(inputs.streamflow_outdir)"
    shellQuote: true

  