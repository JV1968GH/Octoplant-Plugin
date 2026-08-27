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

    public static AppConfig Load()
    {
        var credential = CredentialsManagerClient.ReadGenericCredential(CredentialTarget);
        var vdogClientPath = ResolveVdogClientPath();
        var archivePath = ResolvePath(CredentialsManagerClient.ReadSetting(
            CredentialTarget, "OCTOPLANT_CLIENT_ARCHIVE_PATH"));
        var server = BuildServerUri(
            CredentialsManagerClient.ReadSetting(CredentialTarget, "Server"),
            CredentialsManagerClient.ReadSetting(CredentialTarget, "Portnumber"));
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
            Path.GetFullPath(Directory.GetCurrentDirectory()));
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
}

internal sealed class ConfigException : Exception
{
    public ConfigException(string message) : base(message) { }
}
