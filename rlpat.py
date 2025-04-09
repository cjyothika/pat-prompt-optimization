# Step 1: Save this script as `parse_pat_grammar.py`
from lark import Lark, Visitor, Tree, UnexpectedToken, UnexpectedCharacters, UnexpectedInput
import openai

# OpenAI API key setup
openai.api_key = "abcd"

# Load the corrected PAT grammar (subset)
pat_grammar = """
start: (definition | const_def | var_def | library | channel_def | define_stmt)+

// ----- library imports -----
library: "#" ("import" | "include") STRING ";"

// ----- channel declarations -----
channel_def: "channel" ID INT ";"
            | "channel" ID "[" INT "]" INT ";"

// ----- process definition -----
definition: ID "=" channel_expr ";"

channel_expr: channel_expr "[]" channel_expr
            | guard_expr

guard_expr: "[" ID "]" event_expr
          | event_expr

event_expr: ID block? "->" ID

// ----- case expression -----
case_expr: "case" "{" case_condition+ ("default" ":" channel_expr)? "}"

case_condition: ID ":" channel_expr

// ----- if expression -----
if_expr: "if" "(" ID ")" "{" channel_expr "}" ("else" if_block)?

if_block: "{" channel_expr "}" | if_expr

// ----- constants & variables -----
const_def: "#define" ID INT ";"
var_def: "var" ID ("=" expression)? ";"

// ----- define constructs -----
define_stmt: "#" "define" ID ("-"? INT | "true" | "false" | dparameter? dstatement) ";"
dparameter: "(" ID ("," ID)* ")"
dstatement: block | expression

// ----- block and statement constructs -----
block: "{" statement* (expression)? "}"
statement: block
         | local_var_decl
         | if_expr
         | while_expr
         | expression ";"
         | ";"

local_var_decl: "var" ID ("=" expression)? ";"
              | "var" ID "=" record_expr ";"
              | "var" ID ("[" expression "]")+ ("=" record_expr)? ";"

expression: conditional_or_expr ("=" expression)?
conditional_or_expr: conditional_and_expr ("||" conditional_and_expr)*
conditional_and_expr: conditional_xor_expr ("&&" conditional_xor_expr)*
conditional_xor_expr: bitwise_expr ("xor" bitwise_expr)*
bitwise_expr: equality_expr (("&" | "|" | "^") equality_expr)*
equality_expr: relational_expr (("==" | "!=") relational_expr)*
relational_expr: additive_expr (("<" | ">" | "<=" | ">=") additive_expr)*
additive_expr: multiplicative_expr (("+" | "-") multiplicative_expr)*
multiplicative_expr: unary_expr (("*" | "/" | "%") unary_expr)*

unary_expr: ("+" | "-" | "!")? unary_expr_not_pm
          | unary_expr_not_pm "++"
          | unary_expr_not_pm "--"

unary_expr_not_pm: INT
                  | "true"
                  | "false"
                  | "call" "(" ID ("," argument_expr)* ")"
                  | "new" ID "(" (argument_expr ("," argument_expr)*)? ")"
                  | ID method_call?
                  | array_expr method_call?
                  | array_expr
                  | "(" conditional_or_expr ")"

array_expr: ID ("[" conditional_or_expr "]")+

method_call: "." ID ("(" (argument_expr ("," argument_expr)*)? ")")?
            | "$" ID

record_expr: "[" record_element ("," record_element)* "]"
record_element: expression ("(" expression ")")? | expression ".." expression

argument_expr: conditional_or_expr | record_expr

while_expr: "while" "(" expression ")" statement

// ----- terminals -----
ID: /[a-zA-Z_][a-zA-Z0-9_]*/
INT: /[0-9]+/
STRING: ESCAPED_STRING

%import common.ESCAPED_STRING
%import common.WS
%ignore WS
"""

# Initialize the parser
parser = Lark(pat_grammar, start="start", parser="lalr")

# Sample PAT code to parse
sample_pat_code = """
#define N 5;
var ready = true;
var currTemp = 30;
#define bestTemp 35;

Heater = [ready] heat -> WarmRoom [] [tooHot] cool -> Cooler;
"""

# Parse the PAT code into a syntax tree
tree = parser.parse(sample_pat_code)
print(tree.pretty())

# Step 2: Define a visitor to collect valid next steps
class PATNextTokenVisitor(Visitor):
    def __init__(self):
        self.valid_next_tokens = set()

    def start(self, tree):
        print("[In start] → You can now define another spec_body")
        self.valid_next_tokens.update(["definition"])

    def sequential_expr(self, tree):
        print("[In sequential_expr] → You can now use guard_expr")
        self.valid_next_tokens.update(["guard_expr"])

    def guard_expr(self, tree):
        print("[In guard_expr] → You can now use channel_expr or [condition] channel_expr")
        self.valid_next_tokens.update(["channel_expr", "[condition] channel_expr"])

    def channel_expr(self, tree):
        print("[In channel_expr] → You can use event, Skip, Stop, or another channel_expr")
        self.valid_next_tokens.update(["event", "Skip", "Stop"])

# Step 3: Traverse and collect next token suggestions
visitor = PATNextTokenVisitor()
visitor.visit(tree)
print("\n✅ Valid next tokens:", visitor.valid_next_tokens)

# Step 4: Generate prompt for GPT
# prompt_template = """
# You are writing a PAT model. The current code is:
# {partial_code}

# From the grammar, the next valid constructs are: {valid_tokens}.
# Only return the next line of code that follows the grammar.
# """

# partial_code = sample_pat_code.strip()
# valid_tokens = ", ".join(visitor.valid_next_tokens)

# prompt = prompt_template.format(partial_code=partial_code, valid_tokens=valid_tokens)
# print("\n🧠 Prompt to GPT:\n", prompt)

# Optional: Call GPT (Uncomment below if desired)
# response = openai.ChatCompletion.create(
#     model="gpt-4",
#     messages=[
#         {"role": "system", "content": "You are a PAT modeling expert."},
#         {"role": "user", "content": prompt}
#     ],
#     temperature=0.2
# )
# print("\n🤖 GPT Suggestion:", response['choices'][0]['message']['content'].strip())
parser = Lark(pat_grammar, start="start", parser="lalr")
current_code = ""
# Get all terminals (token definitions)
token_map = {}

for term in parser.terminals:
    name = term.name
    pattern = term.pattern.value

    # Try to make patterns more human-readable
    if pattern.startswith('"') and pattern.endswith('"'):
        readable = pattern.strip('"')
    elif name == 'STRING':
        readable = """'(~('\\'|'"'))*'"""
    elif name == 'ID':
        readable = "[a-zA-Z_][a-zA-Z0-9_]*"
    elif name == 'INT':
        readable = "[0-9]+"
    else:
        readable = pattern

    token_map[name] = readable

parsed_lines = []
current_code = ""
line_count = 0
MAX_LINES = 100

while line_count < MAX_LINES:
    try:
        parser.parse(current_code)
        print("✅ Parsing complete.")
        parsed_lines.append(current_code.strip())
        line_count += 1
        current_code = ""  # Clear for next line
        prompt = f"""
You are writing a PAT CSP model for this scenario:
When Temperature Sensor is turned on, current temperature is detected/simulated and room is either heated or cooled until choice temperature.
The current code is:
{code if code else "<empty>"}

From the grammar, the next valid tokens are: {', '.join(readable_tokens)}.
Only return the 1 next token from the valid tokens (follow the regex syntax where given) and nothing else.
Do not return Python, more than 1 token or explanations.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a PAT modeling expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        next_line = response['choices'][0]['message']['content'].strip()

        if next_line.lower() == "done":
            print("✅ GPT indicated completion.")
            break

        print("\n🤖 GPT Suggestion:", next_line)
        current_code += " " + next_line
        if next_line == ";":
            line_count += 1
            current_code += "\n"
    except UnexpectedInput as e:
        # Convert token names to readable syntax
        valid_tokens = list(e.expected) if hasattr(e, 'expected') else []
        readable_tokens = [token_map.get(t, t.lower()) for t in valid_tokens]

        print("\n📘 Current Code So Far:\n", current_code.strip())
        print("\n🔮 Valid next tokens (syntax):", readable_tokens)
        code = "\n".join(parsed_lines) + current_code.strip()
        # Ask GPT for next line
        prompt = f"""
You are writing a PAT CSP model for this scenario:
When Temperature Sensor is turned on, current temperature is detected/simulated and room is either heated or cooled until choice temperature.
The current code is:
{code if code else "<empty>"}

From the grammar, the next valid tokens are: {', '.join(readable_tokens)}.
Only return the 1 next token from the valid tokens (follow the regex syntax where given) and nothing else.
Do not return Python or explanations.
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a PAT modeling expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        next_line = response['choices'][0]['message']['content'].strip()

        if next_line.lower() == "done":
            print("✅ GPT indicated completion.")
            break

        print("\n🤖 GPT Suggestion:", next_line)
        current_code += " " + next_line
        if next_line == ";":
            line_count += 1
            current_code += "\n"