using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Data.Sqlite;

namespace VDogCheckOut;

/// <summary>Gecombineerde applicatieconfiguratie uit .env en de access-rights database.</summary>
internal sealed record AppConfig(
    string User,
    string Password,
    string Domain,
    string Server,
    bool   SslVerify,
    string ArchivePath,
    string CheckoutPath,
    string VdogClientPath,
    string ProjectRoot
);

internal static class ConfigLoader
{
    /// <summary>
    /// Laad configuratie. Alle paden worden RELATIEF bepaald:
    ///
    ///   .env             -- walk-up vanaf CWD
    ///   access-rights.db -- pad via ACCESS_RIGHTS_DB_PATH in .env,
    ///                       of automatisch gevonden als sibling van de workspace
    ///   VdogClientPath   -- OCTOPLANT_VDOG_CLIENT_PATH in .env,
    ///                       anders auto-discover (exe-map, gangbare installatiemap, PATH)
    ///   app-naam         -- ACCESS_RIGHTS_APP_NAME in .env (standaard: Octoplant)
    /// </summary>
    public static AppConfig Load(string? envPath = null)
    {
        var envFile = envPath ?? FindFileUpward(".env")
            ?? throw new ConfigException(
                ".env bestand niet gevonden.\n" +
                "Start VDogCheckOut vanuit de Octoplant projectmap " +
                "of geef het pad op via --env <pad>.");

        var env         = LoadEnvFile(envFile);
        var projectRoot = Path.GetFullPath(Path.GetDirectoryName(envFile)!);

        var dbPath  = ResolveDbPath(env, projectRoot);
        var appName = env.GetValueOrDefault("ACCESS_RIGHTS_APP_NAME", "Octoplant");

        MigrateSchema(dbPath);

        var (user, dbDomain, password) = LoadCredentialsFromDb(dbPath, appName);

        var domain = !string.IsNullOrWhiteSpace(dbDomain)
            ? dbDomain
            : env.GetValueOrDefault("OCTOPLANT_DOMAIN", "");

        var vdogClientPath = ResolveVdogClientPath(env, projectRoot);

        var archivePath = ResolvePath(GetRequired(env, "OCTOPLANT_ARCHIVE_PATH"), projectRoot);
        var server      = env.GetValueOrDefault("OCTOPLANT_SERVER", "");
        var sslVerify   = !string.Equals(
            env.GetValueOrDefault("OCTOPLANT_SSL_VERIFY", "true"),
            "false", StringComparison.OrdinalIgnoreCase);

        var checkoutPath = env.TryGetValue("OCTOPLANT_CHECKOUT_PATH", out var cp)
                           && !string.IsNullOrWhiteSpace(cp)
            ? ResolvePath(cp, projectRoot)
            : Path.Combine(projectRoot, "octoPlantCheckouts");

        return new AppConfig(
            user, password, domain, server, sslVerify,
            archivePath, checkoutPath, vdogClientPath, projectRoot);
    }

    /// <summary>
    /// Voegt ontbrekende kolommen toe aan een bestaande database
    /// (compatibiliteit met oudere schema-versies).
    /// </summary>
    private static void MigrateSchema(string dbPath)
    {
        using var connection = new SqliteConnection($"Data Source={dbPath}");
        connection.Open();

        var migrations = new (string check, string alter)[]
        {
            ("domain",
             "ALTER TABLE user_access ADD COLUMN domain TEXT NOT NULL DEFAULT ''")
        };

        foreach (var (col, alter) in migrations)
        {
            using var check = new SqliteCommand(
                $"SELECT COUNT(*) FROM pragma_table_info('user_access') WHERE name = '{col}';",
                connection);
            if (Convert.ToInt32(check.ExecuteScalar()) == 0)
            {
                using var alterCmd = new SqliteCommand(alter, connection);
                alterCmd.ExecuteNonQuery();
            }
        }
    }

    private static string ResolveDbPath(Dictionary<string, string> env, string projectRoot)
    {
        if (env.TryGetValue("ACCESS_RIGHTS_DB_PATH", out var cfgDb)
            && !string.IsNullOrWhiteSpace(cfgDb))
        {
            var resolved = ResolvePath(cfgDb, projectRoot);
            if (File.Exists(resolved)) return resolved;
            throw new ConfigException(
                $"access-rights database niet gevonden op geconfigureerd pad:\n  {resolved}\n" +
                "Controleer ACCESS_RIGHTS_DB_PATH in .env.");
        }

        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var appData      = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        var workspaceParent = Path.GetDirectoryName(projectRoot) ?? projectRoot;

        var candidates = new[]
        {
            // User-level standaardlocatie (portable over toestellen/users)
            Path.Combine(localAppData, "Octoplant", "access-rights.db"),
            Path.Combine(appData,      "Octoplant", "access-rights.db"),
            // Sibling van de workspace (backwards compatibility)
            Path.Combine(workspaceParent, "AccessRightsManager", "publish", "access-rights.db"),
            Path.Combine(workspaceParent, "AccessRightsManager", "access-rights.db"),
        };

        foreach (var candidate in candidates)
            if (File.Exists(candidate)) return candidate;

        throw new ConfigException(
            "access-rights database niet gevonden.\n" +
            "Stel ACCESS_RIGHTS_DB_PATH in .env in (bijv. %LOCALAPPDATA%\\Octoplant\\access-rights.db).\n\n" +
            "Gezochte locaties:\n" +
            string.Join("\n", candidates.Select(c => "  " + c)));
    }

    private static string ResolveVdogClientPath(Dictionary<string, string> env, string projectRoot)
    {
        if (env.TryGetValue("OCTOPLANT_VDOG_CLIENT_PATH", out var cfgVdog)
            && !string.IsNullOrWhiteSpace(cfgVdog))
        {
            var configured = ResolvePath(cfgVdog, projectRoot);
            if (File.Exists(Path.Combine(configured, "VDogAutoCheckOut.exe")))
                return configured;
            throw new ConfigException(
                $"VDogAutoCheckOut.exe niet gevonden in OCTOPLANT_VDOG_CLIENT_PATH:\n  {configured}");
        }

        var exeDir = AppContext.BaseDirectory;
        var candidates = new List<string>
        {
            exeDir,
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "vdogClient"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "vdogClient"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "vdogClient"),
        };

        var pathVar = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
        foreach (var part in pathVar.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
            candidates.Add(part.Trim());

        foreach (var candidate in candidates.Where(c => !string.IsNullOrWhiteSpace(c)).Distinct(StringComparer.OrdinalIgnoreCase))
        {
            try
            {
                var full = Path.GetFullPath(candidate);
                if (File.Exists(Path.Combine(full, "VDogAutoCheckOut.exe")))
                    return full;
            }
            catch
            {
                // Ongeldig PATH-fragment negeren.
            }
        }

        throw new ConfigException(
            "VDogAutoCheckOut.exe niet gevonden via auto-discover.\n" +
            "Stel OCTOPLANT_VDOG_CLIENT_PATH in .env in indien de tool op een niet-standaardlocatie staat.");
    }

    private static (string UserName, string Domain, string Password) LoadCredentialsFromDb(
        string dbPath, string appName)
    {
        const string query = """
            SELECT ua.user_name, ua.domain, ua.password_hash
            FROM user_access ua
            JOIN applications a ON ua.application_id = a.id
            WHERE LOWER(a.name) = LOWER($appName)
            ORDER BY ua.id
            LIMIT 1;
            """;

        using var connection = new SqliteConnection($"Data Source={dbPath}");
        connection.Open();
        using var cmd = new SqliteCommand(query, connection);
        cmd.Parameters.AddWithValue("$appName", appName);
        using var reader = cmd.ExecuteReader();

        if (!reader.Read())
            throw new ConfigException(
                $"Geen gebruiker gevonden voor toepassing '{appName}' in de database.\n" +
                "Voeg een user toe via de AccessRightsManager GUI.");

        var userName  = reader.GetString(0);
        var domain    = reader.IsDBNull(1) ? string.Empty : reader.GetString(1);
        var encrypted = reader.GetString(2);

        string password;
        try
        {
            var encBytes = Convert.FromBase64String(encrypted);
            var pwBytes  = ProtectedData.Unprotect(encBytes, null, DataProtectionScope.LocalMachine);
            password     = Encoding.UTF8.GetString(pwBytes);
        }
        catch (Exception ex)
        {
            throw new ConfigException(
                $"Wachtwoord voor de geconfigureerde gebruiker kon niet ontsleuteld worden: {ex.Message}\n" +
                "Verwijder de user in de GUI en voeg hem opnieuw toe.\n" +
                "(Wachtwoorden opgeslagen voor de GUI-update zijn niet compatibel.)");
        }

        return (userName, domain, password);
    }

    private static string? FindFileUpward(string fileName)
    {
        var dir = new DirectoryInfo(Directory.GetCurrentDirectory());
        while (dir is not null)
        {
            var candidate = Path.Combine(dir.FullName, fileName);
            if (File.Exists(candidate)) return candidate;
            dir = dir.Parent;
        }
        return null;
    }

    private static Dictionary<string, string> LoadEnvFile(string path)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var line in File.ReadAllLines(path))
        {
            var trimmed = line.Trim();
            if (trimmed.StartsWith('#') || !trimmed.Contains('=')) continue;
            var idx   = trimmed.IndexOf('=');
            var key   = trimmed[..idx].Trim();
            var value = trimmed[(idx + 1)..].Trim();
            if (!string.IsNullOrEmpty(key)) result[key] = value;
        }
        return result;
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
        if (env.TryGetValue(key, out var val) && !string.IsNullOrWhiteSpace(val))
            return val;
        throw new ConfigException($"Verplichte variabele '{key}' ontbreekt of is leeg in .env.");
    }
}

internal sealed class ConfigException : Exception
{
    public ConfigException(string message) : base(message) { }
}