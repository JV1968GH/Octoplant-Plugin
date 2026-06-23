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
        int       numberOfArchives = 0,
        bool      withStdLibs      = false,
        int?      version          = null,
        string?   comment          = null,
        bool      skipMirror       = false)
    {
        var exe = Path.Combine(config.VdogClientPath, "VDogAutoCheckOut.exe");
        if (!File.Exists(exe))
            throw new FileNotFoundException(
                $"VDogAutoCheckOut.exe niet gevonden: {exe}\n" +
                "Controleer OCTOPLANT_VDOG_CLIENT_PATH in .env.");

        // --- Beschermingsregel (alleen voor specifiek componentpad) ---
        if (!string.IsNullOrEmpty(componentPath))
        {
            var rel        = componentPath.TrimStart('\\', '/');
            var inArchive  = Directory.Exists(Path.Combine(config.ArchivePath, rel));
            var inCheckout = Directory.Exists(Path.Combine(config.CheckoutPath, rel));

            if (inArchive && inCheckout)
            {
                return new CheckOutResult(
                    0,
                    "Al beschikbaar -- geen actie vereist",
                    config.CheckoutPath,
                    null, "", "");
            }

            if (inArchive && !inCheckout)
            {
                var mirrorOnly = await MirrorAsync(config, rel);
                return new CheckOutResult(
                    0,
                    "Mirror uitgevoerd (component al in archive -- checkout overgeslagen)",
                    config.CheckoutPath,
                    mirrorOnly, "", "");
            }
        }

        // --- Bouw argumentenlijst ---
        Directory.CreateDirectory(config.ArchivePath);

        var args = new List<string>
        {
            $"/rd:{config.ArchivePath}",
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
        args.Add($"/NumberOfArchives:{numberOfArchives}");
        args.Add($"/WithStdLibs:{(withStdLibs ? "Y" : "N")}");

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

        MirrorResult? syncResult = null;
        if (rc == 0 && !skipMirror)
        {
            var rel = componentPath?.TrimStart('\\', '/');
            syncResult = await MirrorAsync(config, rel);
        }

        return new CheckOutResult(rc, status, config.CheckoutPath, syncResult, "", "");
    }

    private static async Task<MirrorResult> MirrorAsync(AppConfig config, string? relPath)
    {
        var src = relPath != null
            ? Path.Combine(config.ArchivePath, relPath)
            : config.ArchivePath;
        var dst = relPath != null
            ? Path.Combine(config.CheckoutPath, relPath)
            : config.CheckoutPath;

        Directory.CreateDirectory(dst);

        var psi = new ProcessStartInfo("robocopy")
        {
            RedirectStandardOutput = true,
            RedirectStandardError  = true,
            UseShellExecute        = false,
            CreateNoWindow         = true,
        };
        foreach (var a in new[] { src, dst, "/MIR", "/R:1", "/W:1", "/NFL", "/NDL", "/NP" })
            psi.ArgumentList.Add(a);

        using var proc = Process.Start(psi)
            ?? throw new InvalidOperationException("Kon robocopy niet starten.");

        await proc.WaitForExitAsync();

        return new MirrorResult(proc.ExitCode <= 7, proc.ExitCode, src, dst);
    }

}