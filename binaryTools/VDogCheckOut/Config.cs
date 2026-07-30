using System;
using System.Collections.Generic;
using System.IO;

namespace VDogCheckOut;

/// <summary>Gecombineerde applicatieconfiguratie uit .env en Windows Credential Manager.</summary>
internal sealed record AppConfig(
    string User,
    string Password,
    string Domain,
    string Server,
    bool SslVerify,
    string ArchivePath,
    string CheckoutPath,
    string VdogClientPath,
    string ProjectRoot
);

internal static class ConfigLoader
{
    private const string CredentialTarget = "Octoplant";
    private const string VdogClientPath = @"C:\Program Files (x86)\vdogClient";

    public static AppConfig Load(string? envPath = null)
    {
        var envFile = envPath ?? FindFileUpward(".env")
            ?? throw new ConfigException("Lokale configuratie ontbreekt.");

        var env = LoadEnvFile(envFile);
        var projectRoot = Path.GetFullPath(Path.GetDirectoryName(envFile)!);
        var credential = CredentialsManagerClient.ReadGenericCredential(CredentialTarget);
        var vdogClientPath = ResolveVdogClientPath();
        var archivePath = ResolvePath(GetRequired(env, "OCTOPLANT_CLIENT_ARCHIVE_PATH"), projectRoot);
        var server = GetRequired(env, "OCTOPLANT_SERVER").TrimEnd('/');
        var sslVerify = false;
        var checkoutPath = Path.Combine(
            Path.GetFullPath(Directory.GetCurrentDirectory()),
            "octoPlantCheckouts");

        return new AppConfig(
            credential.UserName,
            credential.Password,
            credential.Domain,
            server,
            sslVerify,
            archivePath,
            checkoutPath,
            vdogClientPath,
            projectRoot);
    }

    private static string ResolveVdogClientPath()
    {
        if (File.Exists(Path.Combine(VdogClientPath, "VDogAutoCheckOut.exe")))
            return VdogClientPath;

        throw new ConfigException("De vereiste versiondog-client is niet beschikbaar.");
    }

    private static string? FindFileUpward(string fileName)
    {
        var directory = new DirectoryInfo(Directory.GetCurrentDirectory());
        while (directory is not null)
        {
            var candidate = Path.Combine(directory.FullName, fileName);
            if (File.Exists(candidate))
                return candidate;
            directory = directory.Parent;
        }

        return null;
    }

    private static Dictionary<string, string> LoadEnvFile(string path)
    {
        var values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var line in File.ReadLines(path))
        {
            var trimmed = line.Trim();
            if (trimmed.StartsWith('#') || !trimmed.Contains('='))
                continue;

            var separator = trimmed.IndexOf('=');
            var key = trimmed[..separator].Trim();
            var value = trimmed[(separator + 1)..].Trim();
            if (!string.IsNullOrEmpty(key))
                values[key] = value;
        }

        return values;
    }

    private static string ResolvePath(string value, string projectRoot)
    {
        var expanded = Environment.ExpandEnvironmentVariables(value.Trim());
        return Path.IsPathRooted(expanded)
            ? Path.GetFullPath(expanded)
            : Path.GetFullPath(Path.Combine(projectRoot, expanded));
    }

    private static string GetRequired(Dictionary<string, string> env, string key)
    {
        if (env.TryGetValue(key, out var value) && !string.IsNullOrWhiteSpace(value))
            return value;
        throw new ConfigException("Lokale configuratie is onvolledig.");
    }
}

internal sealed class ConfigException : Exception
{
    public ConfigException(string message) : base(message) { }
}
