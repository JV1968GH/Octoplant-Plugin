using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Security;
using System.Text.Json;
using System.Threading.Tasks;

namespace VDogCheckOut;

/// <summary>
/// OAuth2 authenticatie tegen de OctoPlant REST API (poort 64023).
/// De token wordt gecachet voor de levensduur van het proces.
///
/// Credentials worden intern geladen vanuit het externe credentials-bestand (buiten de workspace).
/// Ze worden NOOIT hardcoded of als CLI-argument doorgegeven.
/// </summary>
internal static class Authenticator
{
    // Publieke client-credentials uit de OctoPlant-documentatie (geen secret)
    private const string ClientId     = "public-api";
    private const string ClientSecret = "ff99971a-f8c3-4d21-5345-f7cb021b4b54";

    private static string? _cachedToken;

    /// <summary>
    /// Verkrijg een Bearer-token via OAuth2 Resource Owner Password flow.
    /// Gooit <see cref="AuthException"/> bij mislukken.
    /// </summary>
    public static async Task<string> GetTokenAsync(AppConfig config)
    {
        if (_cachedToken is not null)
            return _cachedToken;

        if (string.IsNullOrWhiteSpace(config.Server))
            throw new AuthException(
                "OCTOPLANT_SERVER is niet ingesteld in .env.\n" +
                "Dit is vereist voor OAuth2-authenticatie.");

        // versiondog verwacht domein als prefix: "DOMEIN\gebruiker"
        // Als de gebruikersnaam al een \ bevat (DOMAIN\user ingevoerd in GUI),
        // gebruik dan de gebruikersnaam as-is om dubbele prefix te vermijden.
        var effectiveUser = (!string.IsNullOrEmpty(config.Domain) && !config.User.Contains('\\'))
            ? $"{config.Domain}\\{config.User}"
            : config.User;

        using var handler = new HttpClientHandler();
        if (!config.SslVerify)
            handler.ServerCertificateCustomValidationCallback =
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator;

        using var http = new HttpClient(handler);

        var body = new FormUrlEncodedContent(new Dictionary<string, string>
        {
            ["grant_type"]    = "password",
            ["username"]      = effectiveUser,
            ["password"]      = config.Password,
            ["client_id"]     = ClientId,
            ["client_secret"] = ClientSecret,
        });

        HttpResponseMessage resp;
        try
        {
            resp = await http.PostAsync($"{config.Server}/v1/oauth2/token", body);
        }
        catch (HttpRequestException ex)
        {
            throw new AuthException($"Verbinding mislukt met de OctoPlant server: {ex.Message}");
        }

        if (!resp.IsSuccessStatusCode)
        {
            // De ruwe serverrespons wordt NIET opgenomen: die kan credentials bevatten.
            throw new AuthException(
                $"Login mislukt (HTTP {(int)resp.StatusCode}). " +
                "Controleer gebruikersnaam, wachtwoord en OCTOPLANT_SERVER.");
        }

        var json = JsonDocument.Parse(await resp.Content.ReadAsStringAsync());
        if (!json.RootElement.TryGetProperty("access_token", out var tokenEl)
            || string.IsNullOrWhiteSpace(tokenEl.GetString()))
            throw new AuthException("Geen 'access_token' in het antwoord van de server.");

        _cachedToken = tokenEl.GetString()!;
        return _cachedToken;
    }

    /// <summary>Verifieer login — geeft uitsluitend exitcode terug (0 = OK, 1000 = mislukt).</summary>
    public static async Task<int> VerifyAsync(AppConfig config)
    {
        try
        {
            await GetTokenAsync(config);
            return 0;
        }
        catch (AuthException)
        {
            return 1000;
        }
    }

    public static void InvalidateToken() => _cachedToken = null;
}

internal sealed class AuthException : Exception
{
    public AuthException(string message) : base(message) { }
}