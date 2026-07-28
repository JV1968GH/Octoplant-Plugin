using System;
using System.Runtime.InteropServices;
using System.Text;

namespace VDogCheckOut;

internal sealed record WindowsCredential(string UserName, string Password);

internal static class WindowsCredentialManager
{
    private const uint GenericCredentialType = 1;

    public static WindowsCredential ReadGenericCredential(string target)
    {
        if (!CredRead(target, GenericCredentialType, 0, out var credentialPointer))
            throw new ConfigException("De vereiste Windows-referentie is niet beschikbaar.");

        try
        {
            var credential = Marshal.PtrToStructure<NativeCredential>(credentialPointer);
            if (credential.UserName == IntPtr.Zero
                || credential.CredentialBlob == IntPtr.Zero
                || credential.CredentialBlobSize == 0
                || credential.CredentialBlobSize % sizeof(char) != 0)
            {
                throw new ConfigException("De vereiste Windows-referentie is ongeldig.");
            }

            var userName = Marshal.PtrToStringUni(credential.UserName);
            if (string.IsNullOrWhiteSpace(userName))
                throw new ConfigException("De vereiste Windows-referentie is ongeldig.");

            var passwordBytes = new byte[credential.CredentialBlobSize];
            try
            {
                Marshal.Copy(credential.CredentialBlob, passwordBytes, 0, passwordBytes.Length);
                var password = Encoding.Unicode.GetString(passwordBytes).TrimEnd('\0');
                if (string.IsNullOrEmpty(password))
                    throw new ConfigException("De vereiste Windows-referentie is ongeldig.");

                return new WindowsCredential(userName, password);
            }
            finally
            {
                Array.Clear(passwordBytes, 0, passwordBytes.Length);
            }
        }
        finally
        {
            CredFree(credentialPointer);
        }
    }

    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CredRead(
        string target,
        uint type,
        uint flags,
        out IntPtr credential);

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern void CredFree(IntPtr buffer);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct NativeCredential
    {
        public uint Flags;
        public uint Type;
        public IntPtr TargetName;
        public IntPtr Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public uint CredentialBlobSize;
        public IntPtr CredentialBlob;
        public uint Persist;
        public uint AttributeCount;
        public IntPtr Attributes;
        public IntPtr TargetAlias;
        public IntPtr UserName;
    }
}
