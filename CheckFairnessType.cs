using System;
using System.IO;
using System.Linq;
using System.Reflection;

class CheckPatMethods
{
    static void Main()
    {
        string patDir = @"C:\Program Files (x86)\Process Analysis Toolkit\Process Analysis Toolkit 3.4.3";
        string[] dlls = {
            "PAT.Common.dll",
            "PAT.Module.CSP.dll"
        };

        // Look for UIInitialize method on any AssertionBase-derived types
        Console.WriteLine("=== Checking UIInitialize overloads ===\n");

        foreach (string dll in dlls)
        {
            string path = Path.Combine(patDir, dll);
            if (!File.Exists(path)) continue;

            try
            {
                Assembly asm = Assembly.LoadFrom(path);
                foreach (Type t in asm.GetTypes())
                {
                    if (t.Name.Contains("Assertion"))
                    {
                        var methods = t.GetMethods().Where(m => m.Name == "UIInitialize");
                        foreach (var m in methods)
                        {
                            Console.WriteLine($"In type: {t.FullName}");
                            Console.WriteLine(" → UIInitialize(" + string.Join(", ", m.GetParameters().Select(p => $"{p.ParameterType.Name} {p.Name}")) + ")");
                            Console.WriteLine();
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] {dll}: {ex.Message}");
            }
        }

        Console.WriteLine("\n=== Searching for RuntimeException ===\n");

        foreach (string dll in dlls)
        {
            string path = Path.Combine(patDir, dll);
            if (!File.Exists(path)) continue;

            try
            {
                Assembly asm = Assembly.LoadFrom(path);
                foreach (Type t in asm.GetTypes())
                {
                    if (t.Name == "RuntimeException")
                    {
                        Console.WriteLine($"✔ Found RuntimeException in: {t.FullName}");
                        Console.WriteLine($"   → {dll}\n");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] {dll}: {ex.Message}");
            }
        }
    }
}
