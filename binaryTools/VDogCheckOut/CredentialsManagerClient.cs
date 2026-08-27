using System.ComponentModel;
using System.Diagnostics;
using System.IO.Pipes;
using System.Security.Cryptography;
using System.Text.Json;

namespace VDogCheckOut;

internal sealed record ManagedCredential(string UserName, string Domain, string Password);
internal sealed record ManagedSetting(string Value);

internal static class CredentialsManagerClient
{
    private const string ExecutableName = "CredentialsManager.exe";
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
    };

    public static ManagedCredential ReadGenericCredential(string credentialTarget) =>
        ReadResponseAsync<ManagedCredential>(
            startInfo =>
            {
                startInfo.ArgumentList.Add("--credential-target");
                startInfo.ArgumentList.Add(credentialTarget);
            },
            credential => !string.IsNullOrWhiteSpace(credential.UserName)
                && credential.Domain is not null
                && !string.IsNullOrEmpty(credential.Password))
            .GetAwaiter().GetResult();

    public static string ReadSetting(string mainKey, string subKey) =>
        ReadResponseAsync<ManagedSetting>(
            startInfo =>
            {
                startInfo.ArgumentList.Add("--main-key");
                startInfo.ArgumentList.Add(mainKey);
                startInfo.ArgumentList.Add("--sub-key");
                startInfo.ArgumentList.Add(subKey);
            },
            setting => !string.IsNullOrWhiteSpace(setting.Value))
            .GetAwaiter().GetResult().Value;

    private static async Task<T> ReadResponseAsync<T>(
        Action<ProcessStartInfo> configureRequest,
        Func<T, bool> isValid)
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
        using var process = StartHelper(executablePath, pipeName, configureRequest);

        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();
        try
        {
            await pipe.WaitForConnectionAsync(cancellation.Token);
            var response = await JsonSerializer.DeserializeAsync<T>(
                pipe,
                JsonOptions,
                cancellation.Token);

            await process.WaitForExitAsync(cancellation.Token);
            await Task.WhenAll(stdoutTask, stderrTask);

            if (process.ExitCode != 0 || response is null || !isValid(response))
            {
                throw new ConfigException("De vereiste Windows-referentie is niet beschikbaar.");
            }

            return response;
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
        string pipeName,
        Action<ProcessStartInfo> configureRequest)
    {
        var startInfo = new ProcessStartInfo(executablePath)
        {
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        configureRequest(startInfo);
        startInfo.ArgumentList.Add("--pipe-name");
        startInfo.ArgumentList.Add(pipeName);

        return Process.Start(startInfo)
            ?? throw new ConfigException("De credential-hulpprogramma kon niet starten.");
    }
}
