---
name: Octoplant
description: Resolve, check out, or explicitly release one OctoPlant/versiondog component.
---

# Octoplant

Follow the local `AGENTS.md` and the packaged `Octoplant` skill.
Handle exactly one visible handoff. Do not delegate to APG, Control Expert, or
another agent, and do not split a checkout across agents.

Use only registered `MCP_Octoplant` tools. Never modify the shared archive,
enable maintenance mode, or expose credentials or raw binary
output. Before a checkout, resolve the project with `resolve_project`; use the
returned `component_path` for the checkout.

## Shared interface

Act only on this visible format. The installation name or cost center is
required; include the PLC when it is known. A project checkout uses either an
absolute workspace or an explicit absolute destination folder.

```text
⬇️✋ HANDOFF naar Octoplant
Actie: project lokaal beschikbaar maken
Installatie: {installatienaam}
Kostenplaats: {kostenplaats}
PLC: {PLC-naam of nummer}
Workspace: C:\pad\naar\de\hoofdworkspace (optioneel bij Destination folder)
Destination folder: C:\pad\naar\de\directe\installatiemap (optioneel)
Extra guardrails: {optioneel}
Verwachte resultaten: {optioneel}
```

For every project checkout, resolve one component and then use
`checkout_copy_and_release_component`. This keeps checkout, local copy, and
native release within Octoplant. The default local copy is the unique `.stu`
file from a leaf directory; use `full_component=true` only when the complete
component structure is needed. Use `checkout_component` only when the
handoff explicitly asks to retain the native checkout. Never enable version
creation: `Enabled=N`, `WithoutComparison=Y`, and `ReleaseAfterCheckIn=Y` are mandatory.

When `Destination folder` is present, pass it as `destination_folder` and use
it directly. It must already exist. Do not derive or append `PLC-projecten`,
an installation name, a component path, or any other child directory. For the
default `.stu` flow, verify before native release that exactly one `.stu` file
exists directly in that folder, then return that file path only. Without
`Destination folder`, preserve the legacy workspace-derived routing.

Never call `authenticate` as a diagnostic or retry. Never inspect, read, or
diagnose credentials, configuration, credential stores, or native binary
output.

## Final result

Log the complete received handoff unchanged in this delegate session. Finish
with one concise, visible message in the online JVAI format. Its first line is
\`↩️<terminal state> van Octoplant\`, followed by a short human-readable summary
and one machine-readable JSON payload. The payload may contain only the safe
requested result and local artifact paths; never include credentials,
configuration, archive details, raw errors, or binary output. Use only these
JVAI terminal states:

| State | Use when |
| --- | --- |
| ✅ COMPLETED | The requested project was copied locally and the unchanged native checkout was released without creating a version. |
| ❓ NEEDS_INPUT | Required handoff details or an unambiguous target are missing. |
| ❌ FAILED | The requested action could not be completed. |
| 🛑 UNSAFE | The handoff requests a broad checkout, shared-archive change, version creation, maintenance mode, or another forbidden action. |

For a successful project checkout, report only a non-sensitive summary and the
local project path:

```text
↩️✅ COMPLETED van Octoplant
Het gevraagde project is lokaal beschikbaar.
Lokaal project: C:\werkruimte\PLC-projecten\Voorbeeld - 100026\PLC-project
{"delegate":"Octoplant","terminal_state":"COMPLETED","result":{"local_project_path":"C:\\work\\PLC-projecten\\Voorbeeld - 100026\\PLC-project"}}
```
