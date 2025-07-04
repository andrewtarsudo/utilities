#!/usr/bin/env powershell

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force;
[System.Environment]::SetEnvironmentVariable("_TW_UTILITIES_UPDATE", "1", "User");
RefreshEnv.cmd;