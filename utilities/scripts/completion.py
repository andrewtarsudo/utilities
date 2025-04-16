# -*- coding: utf-8 -*-
from os import environ, scandir
from pathlib import Path

from click.core import Context, Parameter
from click.parser import split_arg_string
from click.shell_completion import add_completion_class, CompletionItem, ShellComplete

from utilities.common.shared import ADOC_EXTENSION, MD_EXTENSION


# noinspection PyUnusedLocal
def file_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_suffix: bool = Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION)
        is_file: bool = path.is_file(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if is_suffix and is_file and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def dir_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_suffix: bool = Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION)
        is_dir: bool = path.is_dir(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if is_suffix and is_dir and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def doc_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_suffix: bool = Path(path).suffix in (".docx", ".docm")
        is_file: bool = path.is_file(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if is_suffix and is_file and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]


# noinspection PyUnusedLocal
def file_dir_completion(ctx: Context, parameter: Parameter, incomplete: str):
    paths: list[str] = []

    for path in scandir("."):
        is_file: bool = path.is_file() and Path(path).suffix in (MD_EXTENSION, ADOC_EXTENSION)
        is_dir: bool = path.is_dir(follow_symlinks=True)
        is_incomplete: bool = path.name.startswith(incomplete)

        if (is_file or is_dir) and is_incomplete:
            paths.append(path.path)

    return [CompletionItem(path) for path in paths]


_SOURCE_PWSH = """\
Register-ArgumentCompleter -Native -CommandName %(prog_name)s -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
        $env:COMP_WORDS = $commandAst
        $env:COMP_WORDS = $env:COMP_WORDS.replace('\\', '/')
        $incompleteCommand = $commandAst.ToString()

        $myCursorPosition = $cursorPosition
        if ($myCursorPosition -gt $incompleteCommand.Length) { $myCursorPosition = \
$incompleteCommand.Length }
        $env:COMP_CWORD = @($incompleteCommand.substring(0, \
$myCursorPosition).Split(" ") | Where-Object { $_ -ne "" }).Length
        if ( $wordToComplete.Length -gt 0) { $env:COMP_CWORD -= 1 }

        $env:%(complete_var)s = "pwsh_complete"

        %(prog_name)s | ForEach-Object {
            $type, $value, $help = $_.Split(",", 3)
            if ( ($type -eq "plain") -and ![string]::IsNullOrEmpty($value) ) {
                [System.Management.Automation.CompletionResult]::new($value, $value, \
"ParameterValue", $value)
            } elseif ( ($type -eq "file") -or ($type -eq "dir") ) {
                if ([string]::IsNullOrEmpty($wordToComplete)) {
                    $dir = "./"
                } else {
                    $dir = $wordToComplete.replace('\\', '/')
                }
                if ( (Test-Path -Path $dir) -and ((Get-Item $dir) -is \
[System.IO.DirectoryInfo]) ) {
                    [System.Management.Automation.CompletionResult]::new($dir, $dir, \
"ParameterValue", $dir)
                }
                Get-ChildItem -Path $dir | Resolve-Path -Relative | ForEach-Object {
                    $path = $_.ToString().replace('\\', \
'/').replace('Microsoft.PowerShell.Core/FileSystem::', '')
                    $isDir = $false
                    if ((Get-Item $path) -is [System.IO.DirectoryInfo]) {
                        $path = $path + "/"
                        $isDir = $true
                    }
                    if ( ($type -eq "file") -or ( ($type -eq "dir") -and $isDir ) ) {
                        [System.Management.Automation.CompletionResult]::new($path, \
$path, "ParameterValue", $path)
                    }
                }
            }
        }

        $env:COMP_WORDS = $null | Out-Null
        $env:COMP_CWORD = $null | Out-Null
        $env:%(complete_var)s = $null | Out-Null
}
"""


@add_completion_class
class PowershellComplete(ShellComplete):
    """Class to represent PowerShell completion."""

    name = "pwsh"
    source_template = _SOURCE_PWSH

    def get_completion_args(self) -> tuple[list[str], str]:
        comp_words: list[str] = split_arg_string(environ.get("COMP_WORDS"))
        comp_cword: int = int(environ.get("COMP_CWORD"))
        args: list[str] = comp_words[1:comp_cword]

        try:
            incomplete: str = comp_words[comp_cword]

        except IndexError:
            incomplete: str = ""

        return args, incomplete

    def format_completion(self, item: CompletionItem) -> str:
        return f"{item.type},{item.value},{item.help if item.help else '_'}"
