using System;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;

namespace VDogCheckOut;

/// <summary>
/// VDogCheckOut -- OctoPlant/versiondog checkout wrapper.
///
/// Subcommands:
///   login                   Test OAuth2-verbinding
///   token                   Haal een Bearer-token op (stdout, geen label)
///   checkout [options]      Component uitchecken (standaard subcommand)
///
/// Gebruik:
///   VDogCheckOut.exe login
///   VDogCheckOut.exe token
///   VDogCheckOut.exe checkout &lt;component_path&gt;
///   VDogCheckOut.exe checkout --id &lt;component_id&gt;
///   VDogCheckOut.exe checkout --all
///   VDogCheckOut.exe &lt;component_path&gt;           (checkout impliciet)
///
/// Opties (checkout):
///   --id &lt;id&gt;           Component-ID (alternatief voor pad)
///   --all               Alle componenten uitchecken
///   --backups           Backups meenemen (/WithBackups:Y)
///   --archives &lt;n&gt;      Aantal archives (0 = alle, standaard 0)
///   --std-libs          Standaardbibliotheken meenemen (/WithStdLibs:Y)
///   --version &lt;n&gt;       Specifiek versienummer
///   --comment &lt;text&gt;    Opmerking in het CheckIn-CheckOut-Log
///   --skip-mirror       Geen robocopy-stap na checkout
///   --json              Uitvoer als JSON (voor machineverwerking)
///
/// Algemene opties:
///   --env &lt;path&gt;        Pad naar .env (override)
///   --help, -h          Toon help
///
/// Exit codes:
///   0     Succes
///   1     Algemene fout
///   2     Geen componenten gevonden
///   10    Config-fout (configuratie)
///   1000  Login-fout
/// </summary>
internal static class Program
{
    private const int ExitOk     = 0;
    private const int ExitError  = 1;
    private const int ExitConfig = 10;

    private static async Task<int> Main(string[] args)
    {
        string? envOverride = null;

        var remaining = new System.Collections.Generic.List<string>();
        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i].ToLowerInvariant())
            {
                case "--env":
                    envOverride = Next(args, ref i, "--env");
                    break;
                default:
                    remaining.Add(args[i]);
                    break;
            }
        }

        if (remaining.Count == 0
            || remaining[0] is "--help" or "-h"
            || (remaining.Count > 1 && remaining[1] is "--help" or "-h"))
        {
            PrintHelp();
            return ExitOk;
        }

        string subcommand;
        int argStart;
        if (remaining[0].ToLowerInvariant() is "login" or "checkout" or "token")
        {
            subcommand = remaining[0].ToLowerInvariant();
            argStart   = 1;
        }
        else
        {
            subcommand = "checkout";
            argStart   = 0;
        }

        AppConfig config;
        try
        {
            config = ConfigLoader.Load(envOverride);
        }
        catch (ConfigException)
        {
            return ExitConfig;
        }
        catch
        {
            return ExitConfig;
        }

        return subcommand switch
        {
            "login"    => await RunLoginAsync(config),
            "token"    => await RunTokenAsync(config),
            "checkout" => await RunCheckoutAsync(config, remaining, argStart),
            _          => ExitError,
        };
    }

    private static async Task<int> RunLoginAsync(AppConfig config)
    {
        try
        {
            return await Authenticator.VerifyAsync(config);
        }
        catch
        {
            return ExitError;
        }
    }

    /// <summary>
    /// Schrijft uitsluitend de Bearer-token naar stdout (geen label, geen newline).
    /// Bedoeld voor machineverwerking door de Python MCP-server.
    /// Exit 0 = succes, 1000 = authenticatiefout.
    /// </summary>
    private static async Task<int> RunTokenAsync(AppConfig config)
    {
        try
        {
            var token = await Authenticator.GetTokenAsync(config);
            Console.Write(token);
            return ExitOk;
        }
        catch (AuthException)
        {
            return 1000;
        }
        catch
        {
            return ExitError;
        }
    }

    private static async Task<int> RunCheckoutAsync(
        AppConfig config,
        System.Collections.Generic.List<string> args,
        int start)
    {
        string? componentPath = null;
        string? componentId   = null;
        bool allComponents    = false;
        bool withBackups      = false;
        bool withStdLibs      = false;
        int  numberOfArchives = 0;
        int? version          = null;
        string? comment       = null;
        bool skipMirror       = false;
        bool jsonOutput       = false;

        for (int i = start; i < args.Count; i++)
        {
            switch (args[i].ToLowerInvariant())
            {
                case "--id":
                    componentId = NextL(args, ref i, "--id");
                    break;
                case "--all":
                    allComponents = true;
                    break;
                case "--backups":
                    withBackups = true;
                    break;
                case "--std-libs":
                    withStdLibs = true;
                    break;
                case "--archives":
                    var aStr = NextL(args, ref i, "--archives");
                    if (!int.TryParse(aStr, out numberOfArchives))
                    {
                        Console.Error.WriteLine(
                            $"Fout: --archives verwacht een geheel getal, niet '{aStr}'.");
                        return ExitError;
                    }
                    break;
                case "--version":
                    var vStr = NextL(args, ref i, "--version");
                    if (!int.TryParse(vStr, out var v))
                    {
                        Console.Error.WriteLine(
                            $"Fout: --version verwacht een geheel getal, niet '{vStr}'.");
                        return ExitError;
                    }
                    version = v;
                    break;
                case "--comment":
                    comment = NextL(args, ref i, "--comment");
                    break;
                case "--skip-mirror":
                    skipMirror = true;
                    break;
                case "--json":
                    jsonOutput = true;
                    break;
                default:
                    if (args[i].StartsWith('-'))
                    {
                        Console.Error.WriteLine($"Onbekende optie: {args[i]}");
                        Console.Error.WriteLine("Gebruik --help voor meer informatie.");
                        return ExitError;
                    }
                    if (componentPath is not null)
                    {
                        Console.Error.WriteLine("Fout: meer dan een componentpad opgegeven.");
                        return ExitError;
                    }
                    componentPath = args[i];
                    break;
            }
        }

        var targetCount = (componentPath is not null ? 1 : 0)
                        + (componentId   is not null ? 1 : 0)
                        + (allComponents             ? 1 : 0);

        if (targetCount == 0)
        {
            Console.Error.WriteLine("Fout: geef een componentpad, --id of --all op.");
            Console.Error.WriteLine("Gebruik --help voor meer informatie.");
            return ExitError;
        }
        if (targetCount > 1)
        {
            Console.Error.WriteLine("Fout: combineer niet meerdere doelopties tegelijk.");
            return ExitError;
        }

        CheckOutResult result;
        try
        {
            result = await CheckOutRunner.RunAsync(
                config,
                componentPath:    allComponents ? null : componentPath,
                componentId:      componentId,
                withBackups:      withBackups,
                numberOfArchives: numberOfArchives,
                withStdLibs:      withStdLibs,
                version:          version,
                comment:          comment,
                skipMirror:       skipMirror);
        }
        catch (FileNotFoundException)
        {
            return ExitConfig;
        }
        catch
        {
            return ExitError;
        }

        if (jsonOutput)
            PrintCheckoutResultJson(result);
        else
            PrintCheckoutResult(result);

        return result.ReturnCode;
    }

    private static void PrintCheckoutResult(CheckOutResult r)
    {
        var ok = r.ReturnCode == 0;
        Console.WriteLine($"[{(ok ? "OK" : "FOUT")}] {r.Status}");
        Console.WriteLine($"  Checkout-map : {r.CheckoutPath}");

        if (r.SyncResult is { } s)
        {
            Console.WriteLine($"  Mirror  : {(s.Success ? "OK" : "FOUT")} (rc={s.ReturnCode})");
            Console.WriteLine($"    Van   : {s.Source}");
            Console.WriteLine($"    Naar  : {s.Destination}");
        }
    }

    private static void PrintCheckoutResultJson(CheckOutResult r)
    {
        var obj = new
        {
            returncode    = r.ReturnCode,
            status        = r.Status,
            checkout_path = r.CheckoutPath,
            sync_result   = r.SyncResult is null ? null : (object)new
            {
                success     = r.SyncResult.Success,
                returncode  = r.SyncResult.ReturnCode,
                source      = r.SyncResult.Source,
                destination = r.SyncResult.Destination,
            },
        };
        Console.WriteLine(JsonSerializer.Serialize(obj));
    }

    private static void PrintHelp()
    {
        Console.WriteLine("""
            VDogCheckOut -- OctoPlant/versiondog checkout wrapper
            ======================================================

            Subcommands:
              login                Test OAuth2-verbinding
              token                Haal Bearer-token op (stdout, geen label)
              checkout             Component uitchecken (standaard als weggelaten)

            Gebruik:
              VDogCheckOut.exe login
              VDogCheckOut.exe token
              VDogCheckOut.exe checkout <component_path>
              VDogCheckOut.exe checkout --id <component_id>
              VDogCheckOut.exe checkout --all
              VDogCheckOut.exe <component_path>          (checkout impliciet)

            Checkout-opties:
              <component_path>    Relatief componentpad
                                  (bijv. "RWZI's\100026 - Dendermonde\...")
              --id <id>           Component-ID als alternatief voor pad
              --all               Alle beschikbare componenten uitchecken
              --backups           Backups meenemen (/WithBackups:Y)
              --archives <n>      Aantal archives (0 = alle, standaard 0)
              --std-libs          Standaardbibliotheken meenemen (/WithStdLibs:Y)
              --version <n>       Specifiek versienummer uitchecken
              --comment <text>    Opmerking in het CheckIn-CheckOut-Log
              --skip-mirror       Geen robocopy-stap na checkout
              --json              Uitvoer als JSON (voor machineverwerking)

            Algemene opties:
              --env <path>        Pad naar .env (override)
              --help, -h          Toon deze help

            Exit codes:
              0     Succes
              1     Algemene fout
              2     Geen componenten gevonden
              10    Config-fout
              1000  Login-fout
            """);
    }

    private static string Next(string[] a, ref int i, string flag)
    {
        i++;
        if (i >= a.Length) Die($"{flag} vereist een waarde.");
        return a[i];
    }

    private static string NextL(
        System.Collections.Generic.List<string> a, ref int i, string flag)
    {
        i++;
        if (i >= a.Count) Die($"{flag} vereist een waarde.");
        return a[i];
    }

    private static void Die(string msg)
    {
        Console.Error.WriteLine($"Fout: {msg}");
        Environment.Exit(ExitError);
    }
}