const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

function credentialFilePath(config) {
  return path.join(config.localStateRoot, "rsna-credential.xml");
}

function hasStoredRsnaCredential(config) {
  return fs.existsSync(credentialFilePath(config));
}

function escapePowerShellSingleQuoted(value) {
  return String(value || "").replace(/'/g, "''");
}

function loadStoredRsnaCredential(config) {
  const filePath = credentialFilePath(config);
  if (!fs.existsSync(filePath)) {
    return null;
  }

  const command = [
    "$ErrorActionPreference = 'Stop'",
    `$cred = Import-Clixml -LiteralPath '${escapePowerShellSingleQuoted(filePath)}'`,
    "if (-not $cred) { throw 'Stored RSNA credential could not be loaded.' }",
    "[pscustomobject]@{ username = $cred.UserName; password = $cred.GetNetworkCredential().Password } | ConvertTo-Json -Compress",
  ].join("; ");

  const result = spawnSync(
    "powershell",
    [
      "-NoProfile",
      "-NonInteractive",
      "-ExecutionPolicy",
      "Bypass",
      "-Command",
      command,
    ],
    {
      encoding: "utf8",
    },
  );

  if (result.status !== 0) {
    throw new Error(
      (result.stderr || result.stdout || "Failed to load stored RSNA credential.").trim(),
    );
  }

  return JSON.parse(result.stdout.trim());
}

module.exports = {
  credentialFilePath,
  hasStoredRsnaCredential,
  loadStoredRsnaCredential,
};
