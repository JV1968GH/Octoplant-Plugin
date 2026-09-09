using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;

namespace VDogCheckOut;

internal sealed record CheckOutResult(
    int ReturnCode,
    string Status,
    string CheckoutPath,
    MirrorResult? SyncResult,
    string Stdout,
    string Stderr
);

internal sealed record MirrorResult(
    bool Success,
    int ReturnCode,
    string Source,
    string Destination
);

internal static class CheckOutRunner
{
    private static readonly Dictionary<int, string> StatusMessages = new()
    {
        [0]    = "OK -- ten minste een component uitgecheckt",
        [1]    = "Fout -- geen check-out mogelijk of minimaal een mislukt",
        [2]    = "Geen componenten gevonden (onvoldoende rechten?)",
        [1000] = "Login-fout -- controleer gebruikersnaam en wachtwoord",
    };

    public static async Task<CheckOutResult> RunAsync(
        AppConfig config,
        string?   componentPath,
        string?   componentId,
        bool      withBackups      = false,
        int       numberOfArchives = 1,
        bool      withStdLibs      = false,
        int?      version          = null,
        string?   comment          = null)
    {
        var exe = Path.Combine(config.VdogClientPath, "VDogAutoCheckOut.exe");
        if (!File.Exists(exe))
            throw new FileNotFoundException(
                $"VDogAutoCheckOut.exe niet gevonden: {exe}\n" +
                "Installeer de vereiste versiondog-client.");

        var directWorkspaceCheckout = !PathsEqual(
            config.ArchivePath,
            config.CheckoutPath);

        // --- Beschermingsregel (alleen voor specifiek componentpad) ---
        if (!string.IsNullOrEmpty(componentPath))
        {
            var rel        = componentPath.TrimStart('\\', '/');
            var inCheckout = Directory.Exists(Path.Combine(config.CheckoutPath, rel));

            if (inCheckout)
            {
                return new CheckOutResult(
                    0,
                    "Al beschikbaar -- geen actie vereist",
                    config.CheckoutPath,
                    null, "", "");
            }

            if (!directWorkspaceCheckout
                && Directory.Exists(Path.Combine(config.ArchivePath, rel)))
            {
                return new CheckOutResult(
                    0,
                    "Al beschikbaar -- geen actie vereist",
                    config.CheckoutPath,
                    null, "", "");
            }
        }

        // --- Bouw argumentenlijst ---
        Directory.CreateDirectory(config.CheckoutPath);

        var args = new List<string>
        {
            $"/rd:{config.CheckoutPath}",
            $"/Account:{config.User}",
            $"/Password:{config.Password}",
        };

        if (!string.IsNullOrEmpty(config.Domain))
            args.Add($"/domain:{config.Domain}");

        if (!string.IsNullOrEmpty(componentId))
            args.Add($"/CID:{componentId}");
        else if (!string.IsNullOrEmpty(componentPath))
            args.Add($"/dirR:{componentPath}");
        else
            args.Add("/dirR:");

        args.Add($"/WithBackups:{(withBackups ? "Y" : "N")}");
        args.Add($"/WithStdLibs:{(withStdLibs ? "Y" : "N")}");
        args.Add($"/NumberOfArchives:{numberOfArchives}");

        if (version.HasValue)
            args.Add($"/Version:{version.Value}");
        if (!string.IsNullOrEmpty(comment))
            args.Add($"/comment:{comment}");

        // --- Starten ---
        var psi = new ProcessStartInfo(exe)
        {
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        };
        foreach (var a in args)
            psi.ArgumentList.Add(a);

        using var proc = Process.Start(psi)
            ?? throw new InvalidOperationException("Kon VDogAutoCheckOut.exe niet starten.");

        await proc.StandardOutput.ReadToEndAsync();
        await proc.StandardError.ReadToEndAsync();
        await proc.WaitForExitAsync();

        var rc     = proc.ExitCode;
        var status = StatusMessages.TryGetValue(rc, out var msg)
            ? msg
            : $"Onbekende code ({rc})";

        return new CheckOutResult(rc, status, config.CheckoutPath, null, "", "");
    }

    private static bool PathsEqual(string first, string second) =>
        string.Equals(
            Path.GetFullPath(first).TrimEnd(Path.DirectorySeparatorChar),
            Path.GetFullPath(second).TrimEnd(Path.DirectorySeparatorChar),
            StringComparison.OrdinalIgnoreCase);
}