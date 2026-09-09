using System.Diagnostics;
using System.Text.Json;
using VDogCheckOut;

namespace VDogCheckIn;

internal static class Program
{
    private const int ExitError = 1;
    private const int ExitConfig = 10;

    private static async Task<int> Main(string[] args)
    {
        if (args.Length != 3 || args[0] != "checkin" || args[1] != "--json")
            return ExitError;

        var componentPath = args[2];
        var parts = componentPath.Replace('/', '\\').Split('\\', StringSplitOptions.RemoveEmptyEntries);
        if (!componentPath.StartsWith('\\') || parts.Length == 0 || parts.Any(part => part is "." or ".."))
            return ExitError;

        AppConfig config;
        try
        {
            config = ConfigLoader.Load();
        }
        catch (ConfigException)
        {
            return ExitConfig;
        }

        var exe = Path.Combine(config.VdogClientPath, "VDogAutoCheckIn.exe");
        if (!File.Exists(exe))
            return ExitConfig;

        var iniPath = Path.Combine(Path.GetTempPath(), $"octoplant-checkin-{Guid.NewGuid():N}.ini");
        try
        {
            await File.WriteAllTextAsync(
                iniPath,
                $"[Component]{Environment.NewLine}Dir={componentPath}{Environment.NewLine}{Environment.NewLine}" +
                $"[Version]{Environment.NewLine}Enabled=N{Environment.NewLine}WithoutComparison=Y{Environment.NewLine}{Environment.NewLine}" +
                $"[CheckIn]{Environment.NewLine}ReleaseAfterCheckIn=Y{Environment.NewLine}SilentMode=Y{Environment.NewLine}");

            var startInfo = new ProcessStartInfo(exe)
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            startInfo.ArgumentList.Add("/at:c");
            startInfo.ArgumentList.Add($"/rd:{config.ArchivePath}");
            startInfo.ArgumentList.Add($"/account:{config.User}");
            if (!string.IsNullOrWhiteSpace(config.Domain))
                startInfo.ArgumentList.Add($"/domain:{config.Domain}");
            startInfo.ArgumentList.Add($"/password:{config.Password}");
            startInfo.ArgumentList.Add($"/CFile:{iniPath}");

            using var process = Process.Start(startInfo);
            if (process is null)
                return ExitError;
            await process.StandardOutput.ReadToEndAsync();
            await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();
            Console.WriteLine(JsonSerializer.Serialize(new { returncode = process.ExitCode }));
            return process.ExitCode;
        }
        catch
        {
            return ExitError;
        }
        finally
        {
            if (File.Exists(iniPath))
                File.Delete(iniPath);
        }
    }
}
