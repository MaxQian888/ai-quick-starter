# Testing With Pester

## Pester 5 Baseline

Use `Describe` as the command-level test boundary.
Use `Context` to group behavior classes: parameter validation, pipeline behavior, side effects, and output contract.

Example structure:

```powershell
Describe "Get-ExampleItem" {
    Context "Parameter validation" {
        It "throws when required parameter is missing" {
            { Get-ExampleItem } | Should -Throw
        }
    }

    Context "Output contract" {
        It "returns objects with expected properties" {
            $result = Get-ExampleItem -Name "demo"
            $result | Should -Not -BeNullOrEmpty
            $result.Name | Should -Be "demo"
        }
    }
}
```

## What To Test First

- Required parameter behavior.
- Happy path result shape and key property values.
- Error behavior for invalid inputs.
- `ShouldProcess` behavior for mutating commands.
- Pipeline input behavior when `ValueFromPipeline` or `ValueFromPipelineByPropertyName` is used.

## Mocking Guidance

Mock side-effect cmdlets (filesystem, network, process execution) to keep tests deterministic and fast.
Assert both command output and side-effect invocation intent.

For mutating commands with `ShouldProcess`:

- Test `-WhatIf` path to confirm no mutation occurs.
- Test normal path with mocked side-effect cmdlets and invocation assertions.

## Stable Assertions

- Assert business behavior rather than implementation details.
- Prefer exact property assertions for public output contract.
- Avoid asserting verbose log text unless logging format is part of the contract.

## Execution

Run tests:

```powershell
Invoke-Pester -Path .\tests -Output Detailed
```

Run a single test file:

```powershell
Invoke-Pester -Path .\tests\Get-ExampleItem.Tests.ps1 -Output Detailed
```
