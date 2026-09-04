using System;
using System.Collections.Generic;
using System.IO;

namespace VDogCheckOut;

/// <summary>Gecombineerde applicatieconfiguratie uit Windows Credential Manager.</summary>
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

    public static AppConfig Load(string? workspacePath = null)
    {
        var credential = CredentialsManagerClient.ReadGenericCredential(CredentialTarget);
        var vdogClientPath = ResolveVdogClientPath();
        var archivePath = ResolvePath(CredentialsManagerClient.ReadSetting(
            CredentialTarget, "OCTOPLANT_CLIENT_ARCHIVE_PATH"));
        var server = BuildServerUri(
            CredentialsManagerClient.ReadSetting(CredentialTarget, "URL"),
            CredentialsManagerClient.ReadSetting(CredentialTarget, "Portnumber"));
        var sslVerify = false;
        var projectRoot = ResolveWorkspacePath(workspacePath);
        var checkoutPath = Path.Combine(projectRoot, "octoPlantCheckouts");

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

    private static string BuildServerUri(string server, string portNumber)
    {
        if (!Uri.TryCreate(server.Trim(), UriKind.Absolute, out var serverUri)
            || (!string.Equals(serverUri.Scheme, Uri.UriSchemeHttp, StringComparison.OrdinalIgnoreCase)
                && !string.Equals(serverUri.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
            || !int.TryParse(portNumber, out var port)
            || port is < 1 or > 65535)
        {
            throw new ConfigException("De Octoplant-instellingen zijn ongeldig.");
        }

        var builder = new UriBuilder(serverUri) { Port = port };
        return builder.Uri.GetLeftPart(UriPartial.Authority).TrimEnd('/');
    }

    private static string ResolvePath(string value)
    {
        var expanded = Environment.ExpandEnvironmentVariables(value.Trim());
        if (string.IsNullOrWhiteSpace(expanded))
            throw new ConfigException("De Octoplant-instellingen zijn ongeldig.");

        return Path.GetFullPath(expanded);
    }

    private static string ResolveWorkspacePath(string? workspacePath)
    {
        var path = string.IsNullOrWhiteSpace(workspacePath)
            ? Directory.GetCurrentDirectory()
            : workspacePath;
        if (!Path.IsPathFullyQualified(path) || !Directory.Exists(path))
            throw new ConfigException("De opgegeven workspace bestaat niet of is ongeldig.");

        return Path.GetFullPath(path);
    }
}

internal sealed class ConfigException : Exception
{
    public ConfigException(string message) : base(message) { }
}
