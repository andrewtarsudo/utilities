# -*- coding: utf-8 -*-
from os import environ

from click.parser import split_arg_string
from click.shell_completion import CompletionItem, ShellComplete
from loguru import logger

_SOURCE_PWSH = """\
Register-ArgumentCompleter -Native -CommandName %(prog_name)s -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
        $env:COMP_WORDS = $commandAst
        $env:COMP_WORDS = $env:COMP_WORDS.replace('\\', '/')
        $incompleteCommand = $commandAst.ToString()

        $myCursorPosition = $cursorPosition
        if ($myCursorPosition -gt $incompleteCommand.Length) {
            $myCursorPosition = $incompleteCommand.Length
        }
        $env:COMP_CWORD = @($incompleteCommand.substring(0, $myCursorPosition).Split(" ") | Where-Object { $_ -ne "" }).Length
        if ( $wordToComplete.Length -gt 0)
        {
            $env:COMP_CWORD -= 1
        }

        $env:%(complete_var)s = "pwsh_complete"

        %(prog_name)s | ForEach-Object {
            $type, $value, $help = $_.Split(",", 3)
            if ( ($type -eq "plain") -and ![string]::IsNullOrEmpty($value) )
            {
                [System.Management.Automation.CompletionResult]::new($value, $value, "ParameterValue", $value)
            }
            elseif ( ($type -eq "file") -or ($type -eq "dir") ) {
                if ([string]::IsNullOrEmpty($wordToComplete)) {
                    $dir = "./"
                }
                else {
                    $dir = $wordToComplete.replace('\\', '/')
                }
                if ( (Test-Path -Path $dir) -and ((Get-Item $dir) -is [System.IO.DirectoryInfo]) )
                {
                    [System.Management.Automation.CompletionResult]::new($dir, $dir, "ParameterValue", $dir)
                }
                Get-ChildItem -Path $dir | Resolve-Path -Relative | ForEach-Object {
                    $path = $_.ToString().replace('\\', '/').replace('Microsoft.PowerShell.Core/FileSystem::', '')
                    $isDir = $false
                    if ((Get-Item $path) -is [System.IO.DirectoryInfo])
                    {
                        $path = $path + "/"
                        $isDir = $true
                    }
                    if ( ($type -eq "file") -or ( ($type -eq "dir") -and $isDir ) )
                    {
                        [System.Management.Automation.CompletionResult]::new($path, $path, "ParameterValue", $path)
                    }
                }
            }
        }

        $env:COMP_WORDS = $null | Out-Null
        $env:COMP_CWORD = $null | Out-Null
        $env:%(complete_var)s = $null | Out-Null
}
"""

APP_NAME = "TW_UTILITIES"  # Replace with your actual CLI command name


def activate_cmd_autocompletion():
    try:
        import winreg

    except (ImportError, ModuleNotFoundError):
        logger.error("Текущая операционная система не Windows.")
        return

    else:
        from winreg import HKEYType, OpenKeyEx, HKEY_LOCAL_MACHINE, KEY_WRITE, REG_DWORD, SetValueEx, CloseKey

    cmd_params: HKEYType = OpenKeyEx(HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Command Processor", access=KEY_WRITE)
    SetValueEx(cmd_params, "CompletionChar", 0, REG_DWORD, 0x9)
    SetValueEx(cmd_params, "PathCompletionChar", 0, REG_DWORD, 0x9)
    CloseKey(cmd_params)
    cmd_params.Close()


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
