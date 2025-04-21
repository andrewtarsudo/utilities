#! /usr/bin/env powershell

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned;
[Environment]::SetEnvironmentVariable("_TW_UTILITIES_UPDATE", "0", "User");
RefreshEnv.cmd;