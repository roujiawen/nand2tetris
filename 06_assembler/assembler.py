import argparse

from typing_extensions import override


class SymbolResolver:
    def __init__(self):
        self.var_map: dict[str, int] = {
            "SP": 0x0000,
            "LCL": 0x0001,
            "ARG": 0x0002,
            "THIS": 0x0003,
            "THAT": 0x0004,
            "SCREEN": 0x4000,
            "KBD": 0x6000,
        } | {"R" + str(i): i for i in range(16)}
        self.label_map: dict[str, int] = {}
        self.empty_address: int = 16

    def add_label(self, label: str, line_num: int):
        self.label_map[label] = line_num

    def resolve(self, symbol: str) -> int:
        assert not (symbol in self.var_map and symbol in self.label_map), (
            "variable and label have the same name"
        )

        if symbol in self.label_map:
            return self.label_map[symbol]

        if symbol not in self.var_map:
            assert self.empty_address < 0x4000, "check memory address not overflowing"
            self.var_map[symbol] = self.empty_address
            self.empty_address += 1

        return self.var_map[symbol]


class AInstruction:
    def __init__(self, asm_line: str, resolver: SymbolResolver):
        self.asm_line: str = asm_line
        self.value: int = 0
        self.symbol: str = ""
        self.resolver: SymbolResolver = resolver
        self.parse()

    def parse(self):
        assert self.asm_line[0] == "@", "assert first char equals `@`"
        assert len(self.asm_line) > 1, "assert value is not empty"
        try:
            # integer case
            self.value = int(self.asm_line[1:])
        except ValueError:
            # symbol case
            self.symbol = self.asm_line[1:]
            self.value = self.resolver.resolve(self.symbol)

    @property
    def binary(self) -> str:
        assert (self.value < 0b1000000000000000) and (self.value >= 0), (
            "A-instruction value in range"
        )
        return format(self.value, "016b")

    @override
    def __str__(self) -> str:
        return (f"A: {self.value} (symbol: {self.symbol})") + f"\n {self.binary}"


class CInstruction:
    def __init__(self, asm_line: str):
        self.asm_line: str = asm_line
        self.dest_asm: str
        self.comp_asm: str
        self.jump_asm: str
        self.dest: int
        self.comp: int
        self.jump: int
        self.parse()

    def parse_dest(self):
        MAPPING = {
            "null": 0b000,
            "M": 0b001,
            "D": 0b010,
            "MD": 0b011,
            "A": 0b100,
            "AM": 0b101,
            "AD": 0b110,
            "AMD": 0b111,
        }
        self.dest = MAPPING[self.dest_asm]

    def parse_comp(self):
        MAPPING = {
            "0": 0b101010,
            "1": 0b111111,
            "-1": 0b111010,
            "D": 0b001100,
            "A": 0b110000,
            "!D": 0b001101,
            "!A": 0b110001,
            "-D": 0b001111,
            "-A": 0b110011,
            "D+1": 0b011111,
            "A+1": 0b110111,
            "D-1": 0b001110,
            "A-1": 0b110010,
            "D+A": 0b000010,
            "D-A": 0b010011,
            "A-D": 0b000111,
            "D&A": 0b000000,
            "D|A": 0b010101,
        }
        if "M" in self.comp_asm:
            self.comp = 0b1000000 + MAPPING[self.comp_asm.replace("M", "A")]
        else:
            self.comp = MAPPING[self.comp_asm]

    def parse_jump(self):
        MAPPING = {
            "null": 0b000,
            "JGT": 0b001,
            "JEQ": 0b010,
            "JGE": 0b011,
            "JLT": 0b100,
            "JNE": 0b101,
            "JLE": 0b110,
            "JMP": 0b111,
        }
        self.jump = MAPPING[self.jump_asm]

    def parse(self):
        # Parse (dest=)comp(;jump)
        splitted = self.asm_line.split("=")
        if len(splitted) == 1:
            self.dest_asm = "null"
            compjump = splitted[0]
        elif len(splitted) == 2:
            self.dest_asm = splitted[0]
            compjump = splitted[1]
        else:
            assert False, "CInstruction splitting by `=` exception"

        splitted = compjump.split(";")
        if len(splitted) == 1:
            self.comp_asm = splitted[0]
            self.jump_asm = "null"
        elif len(splitted) == 2:
            self.comp_asm = splitted[0]
            self.jump_asm = splitted[1]
        else:
            assert False, "CInstruction splitting by `;` exception"

        self.parse_dest()
        self.parse_comp()
        self.parse_jump()

    @property
    def binary(self) -> str:
        return format(
            (0b111 << 13) + (self.comp << 6) + (self.dest << 3) + self.jump, "016b"
        )

    @override
    def __str__(self) -> str:
        return f"C: c{self.comp:07b} d{self.dest:03b} j{self.jump:03b} ({self.asm_line}) \n {self.binary}"


class Translator:
    def __init__(self):
        self.assembly_code: str = ""
        self.assembly_lines: list[str] = []
        self.machine_code: str = ""
        self.filename_root: str = ""
        self.instructions: list[AInstruction | CInstruction] = []
        self.resolver: SymbolResolver = SymbolResolver()

    def from_file(self, filename: str):
        self.filename_root, ext = filename.split(".")
        assert ext == "asm", "input file does not have an .asm extension"
        with open(filename, "r") as f:
            self.assembly_code = f.read()
        self.assembly_lines = self.assembly_code.split("\n")
        print(f"Loaded file {filename}")

    def clean_up(self):
        # strip spaces and comments
        self.assembly_lines = [
            line.replace(" ", "").replace("\t", "").split("//", 1)[0]
            for line in self.assembly_lines
        ]
        # strip empty lines
        self.assembly_lines = [line for line in self.assembly_lines if line]

    def parse_lines(self):
        # Process labels first
        line_num = 0
        for line in self.assembly_lines:
            if line[0] == "(":
                assert line[-1] == ")", "both brackets () present"
                label_name = line[1:-1]
                self.resolver.add_label(label_name, line_num)
            else:
                line_num += 1
        # Process A and C Instructions
        for line in self.assembly_lines:
            if line[0] == "@":
                self.instructions.append(AInstruction(line, self.resolver))
            elif line[0] != "(":
                self.instructions.append(CInstruction(line))

    def translate(self):
        print("Removing white spaces and comments...")
        self.clean_up()
        print("Parsing each line...")
        self.parse_lines()
        print("Formatting to binary strings...")
        self.to_machine_code()

        # print("<Debug printout begins>")
        # for each in self.instructions:
        #     print(each)
        # print("<Debug printout ends>")
        # print("--------------------------------------")
        # print("<Tranlated program begins>")
        # print(self.machine_code)
        # print("<Tranlated program ends>")

    def to_machine_code(self):
        self.machine_code = "\n".join(ins.binary for ins in self.instructions)

    def to_file(self):
        assert self.filename_root, "filename empty"
        out_filename = f"{self.filename_root}.hack"
        with open(out_filename, "w") as f:
            f.write(self.machine_code)
        print(f"Written to file {out_filename}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    args = parser.parse_args()

    translator = Translator()
    translator.from_file(args.input_filename)
    translator.translate()
    translator.to_file()


if __name__ == "__main__":
    main()
