import argparse
from pathlib import Path

from parser import Parser
from code_writer import CodeWriter

def translate_file(vm_path: Path, code_writer: CodeWriter):
    with open(vm_path, "r") as infile:
        parser = Parser(infile)
        code_writer.set_vm_filename(vm_path.stem)
        
        for command in parser:
            code_writer.write(command)

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("vm_filename")
    args = arg_parser.parse_args()
    source_path = Path(args.vm_filename)
    out_filename = f"{source_path.parent}/{source_path.stem}.asm"
    
    with open(out_filename, "w") as outfile:
        code_writer = CodeWriter(outfile)
        if source_path.is_dir():
                for each_vm_path in source_path.glob("*.vm"):
                    translate_file(each_vm_path, code_writer)
        elif source_path.is_file() and source_path.suffix == ".vm":
            print("File")
            translate_file(source_path, code_writer)
        else:
            raise ValueError("input path is invalid (must be either a directory or a .vm file)")

if __name__ == "__main__":
    main()
