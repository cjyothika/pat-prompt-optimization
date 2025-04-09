import clr
from System.Reflection import Assembly

dll_path = r"C:\Program Files (x86)\Process Analysis Toolkit\Process Analysis Toolkit 3.4.3\PAT.Common.dll"
output_file = "pat_common_methods.txt"

assembly = Assembly.LoadFrom(dll_path)

interfaces = []
assertion_methods = []
trace_methods = []

for typ in assembly.GetTypes():
    if typ.IsInterface:
        interfaces.append(typ.FullName)
    for method in typ.GetMethods():
        name = method.Name.lower()
        if "assertion" in name:
            assertion_methods.append(f"{typ.FullName}.{method.Name}")
        if "trace" in name or "simulation" in name:
            trace_methods.append(f"{typ.FullName}.{method.Name}")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== Interfaces ===\n")
    for i in interfaces:
        f.write(i + "\n")

    f.write("\n=== Methods related to assertions ===\n")
    for m in assertion_methods:
        f.write(m + "\n")

    f.write("\n=== Methods related to trace or simulation ===\n")
    for m in trace_methods:
        f.write(m + "\n")

print(f"✅ Method list saved to: {output_file}")
