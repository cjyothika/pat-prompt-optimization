import openai

openai.api_key = "abcd"  # Replace with your OpenAI API key

def get_pat_code_part(scenario, stage, current_code=""):
    # Choose the correct instructional prompt based on stage
    if stage == "constants":
        user_prompt = f"""
Let's model a scenario in PAT CSP language together. The main components of PAT are constant definitions, variable definitions, process definitions and assertion definitions. To model this scenario:
{scenario}
What definitions would you need? Only write the code portion related to the constant definitions. Don't reuse existing names for constructs.
Here are syntax examples for writing a constant definition:
#define MAX 5;
#define MIN 1;
#define isFactual false;
#define isFact true;
#define checkxgreaterthan2 if(x > 2){{ a = 4; }} else {{a = 2;}};
"""
    elif stage == "variables":
        user_prompt = f"""
This is the code we have so far:
{current_code}
Let's model a scenario in PAT CSP language together. The main components of PAT are constant definitions, variable definitions, process definitions and assertion definitions. To model this scenario:
{scenario}
What variable definitions would you need? Only write the code portion related to the variables. Don't reuse existing names for constructs.
Here are syntax examples for writing a definition:
var x = 5;
var x = true;
var x = y * z;
var arr = [1, 2, 3, 4];
var arr2 = [1, 2(3), 5, 6]; // [1, 3, 3, 5, 6]
channel c 0; // A channel named c of size 0 for synchronous communication 
channel abc[2] 1; // A channel array named abc of size 2 channels of size 1 each for asynchronous communication
"""
    elif stage == "processes":
        user_prompt = f"""
This is the code we have so far:
{current_code}
Let's model a scenario in PAT CSP language together. The main components of PAT are constant definitions, variable definitions, process definitions and assertion definitions. To model this scenario:
{scenario}
What process definitions would you need? Only write the code portion related to the processes. Don't reuse existing names for constructs.
Here are syntax examples for writing a definition:
"P = a{{ y = 7 + v; x++; }} -> P; // A simple recursive process named P with 1 event a and a statement block that executes with event a",
"P = b -> Q [] a -> Q; // A simple process P with 2 choice sequences of events to the next process",
"P = if (x > 0) {{a -> P}} else {{b -> Q}};",
"P = [x < 0] a -> b -> P [] [x >= 0] c -> d -> P;",
"P = a?x -> P; // Send value of variable x to channel named a when recursive process named P is executed",
"P(y) = a!x -> P(x); // Receive a value in process-local variable x to channel named a when recursive process named P is executed with 1 parameter y",
"P = (a -> b -> Stop) ||| (c -> d -> Stop); // P is a process consisting of 2 concurrent processes",
"""
    elif stage == "assertions":
        user_prompt = f"""
This is the code we have so far:
{current_code}
Let's model a scenario in PAT CSP language together. The main components of PAT are constant definitions, variable definitions, process definitions and assertion definitions. To model this scenario:
{scenario}
can you add some assertions? Don't reuse existing names for constructs.
These are some syntax examples for the assertions:
#assert System |=[] xlessthan2; // given #define xlessthan2 x < 2; is written before this line, it checks if x is always less than 2 for all states in the System process
#assert System |=<> xlessthan2; // this checks if x is less than 2 in some state along the chosen execution path of System
#assert System deadlockfree;
#assert System divergencefree;
#assert System reaches xlessthan2; // reaches is the same as |=<> in LTL format
"""
    else:
        raise ValueError("Invalid stage")

    # Send to OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a PAT CSP model generator. Only return valid PAT CSP code with no extra commentary."},
            {"role": "user", "content": user_prompt.strip()}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()


# Main runner
def build_pat_model(scenario):
    full_code = ""

    print("🧱 Generating Constant Definitions...")
    constants = get_pat_code_part(scenario, "constants")
    full_code += "// ===== Constant Definitions =====\n" + constants + "\n\n"
    print(constants, "\n")

    print("📦 Generating Variable Definitions...")
    variables = get_pat_code_part(scenario, "variables", full_code)
    full_code += "// ===== Variable Definitions =====\n" + variables + "\n\n"
    print(variables, "\n")

    print("⚙️ Generating Process Definitions...")
    processes = get_pat_code_part(scenario, "processes", full_code)
    full_code += "// ===== Process Definitions =====\n" + processes + "\n\n"
    print(processes, "\n")

    print("🔍 Generating Assertion Definitions...")
    assertions = get_pat_code_part(scenario, "assertions", full_code)
    full_code += "// ===== Assertion Definitions =====\n" + assertions + "\n"
    print(assertions)

    return full_code


# Example usage
if __name__ == "__main__":
    scenario_input = input("📝 Describe your scenario:\n> ").strip()
    full_model_code = build_pat_model(scenario_input)

    # Optional: save to file
    with open("generated_model.csp", "w") as f:
        f.write(full_model_code)

    print("\n✅ Full PAT model saved to 'generated_model.csp'")
