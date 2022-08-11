from dptools.cli import BaseCLI
from dptools.utils import Converter

class CLI(BaseCLI):
    help_info = "Convert between structure file types (e.g., .xml to .db)"
    def add_args(self):
        self.parser.add_argument(
            "inputs",
            nargs="+",
            metavar="input",
            help="Input files (with extensions) to convert. Multiple inputs are concatenated into output",
        )
        self.parser.add_argument(
            "output",
            nargs=1,
            help="Output file name to write conversion to (with extension)",
        )
        self.parser.add_argument("-i", "--indices", type=str, default=":",
                help="Indices of input files to read. E.g., :10, -3:, :100:5")

    def main(self, args):
        converter = Converter(args.inputs, args.output[0], args.indices)
        converter.convert()
