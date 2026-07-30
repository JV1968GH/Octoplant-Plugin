using System.ComponentModel;
using System.Diagnostics;
using System.IO.Pipes;
using System.Security.Cryptography;
using System.Text.Json;

namespace VDogCheckOut;

internal sealed record ManagedCredential(string UserName, string Domain, string Password);

internal static class CredentialsManagerClient
{
    private const string ExecutableName = "CredentialsManager.exe";
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public static ManagedCredential ReadGenericCredential(string credentialTarget) =>
        ReadGenericCredentialAsync(credentialTarget).GetAwaiter().GetResult();

    private static async Task<ManagedCredential> ReadGenericCredentialAsync(
        string credentialTarget)
    {
        var executablePath = Path.Combine(AppContext.BaseDirectory, ExecutableName);
        if (!File.Exists(executablePath))
            throw new ConfigException("De credential-hulpprogramma ontbreekt.");

        var pipeName = $"vdogcheckout-{Convert.ToHexString(RandomNumberGenerator.GetBytes(32))}";
        using var pipe = new NamedPipeServerStream(
            pipeName,
            PipeDirection.In,
            1,
            PipeTransmissionMode.Byte,
            PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
        using var cancellation = new CancellationTokenSource(TimeSpan.FromSeconds(30));
        using var process = StartHelper(executablePath, credentialTarget, pipeName);

        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();
        try
        {
            await pipe.WaitForConnectionAsync(cancellation.Token);
            var credential = await JsonSerializer.DeserializeAsync<ManagedCredential>(
                pipe,
                JsonOptions,
                cancellation.Token);

            await process.WaitForExitAsync(cancellation.Token);
            await Task.WhenAll(stdoutTask, stderrTask);

            if (process.ExitCode != 0 || credential is null
                || string.IsNullOrWhiteSpace(credential.UserName)
                || credential.Domain is null
                || string.IsNullOrEmpty(credential.Password))
            {
                throw new ConfigException("De vereiste Windows-referentie is niet beschikbaar.");
            }

            return credential;
        }
        catch (Exception exception) when (
            exception is IOException
                or JsonException
                or OperationCanceledException
                or InvalidOperationException
                or Win32Exception
                or UnauthorizedAccessException)
        {
            throw new ConfigException("De vereiste Windows-referentie is niet beschikbaar.");
        }
        finally
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync();
            }
        }
    }

    private static Process StartHelper(
        string executablePath,
        string credentialTarget,
        string pipeName)
    {
        var startInfo = new ProcessStartInfo(executablePath)
        {
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        startInfo.ArgumentList.Add("--credential-target");
        startInfo.ArgumentList.Add(credentialTarget);
        startInfo.ArgumentList.Add("--pipe-name");
        startInfo.ArgumentList.Add(pipeName);

        return Process.Start(startInfo)
            ?? throw new ConfigException("De credential-hulpprogramma kon niet starten.");
    }
}
