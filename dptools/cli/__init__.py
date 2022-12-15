import argparse
import re
from importlib import import_module
from textwrap import dedent, fill

from dptools import __version__

commands = (
    "input",
    "train",
    "parity",
    "run",
    "sample",
    "convert",
    "set",
    "get",
    "reset",
    "info",
    "shake",
)

class BaseCLI:
    """
    Base class for CLI commands. More or less just a template for reference.

    Args:
        parser (argparse.ArgumentParser): argparse parser for parsing CLI command arguments
    """
    help_info = ""

    def __init__(self, parser):
        self.parser = parser

    def add_args(self):
        '''Command specific arguments'''
        return

    def main(self, args):
        '''Command specific main method'''
        return


class MyFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """
    HelpFormatter that replaces reST refs in docstrings with readthedocs URLs
    to print to console. Also dedents and retains docstring format.
    """

    def _fill_text(self, text, width, indent):
        # replaces e.g. :doc:`text<ref_path>`
        pattern = r":[a-z]+:`[\w ]+<[.\w/]+>`"
        subpattern_link = r"<../[a-z/]+>"
        subpattern_text = r"`[\w ]+<"

        url = ": https://dptools.rtfd.io/en/latest/"

        matches = re.findall(pattern, text)
        for match in matches:
            keep = re.search(subpattern_text, match).group()[1:-1]
            sub = re.search(subpattern_link, match).group()[4:-1]
            new = f"{keep}{url}{sub}.html"
            text = text.replace(match, new)

        # replaces e.g. .. command:: text
        pattern = r"[ ]*[.]{2} [\w-]+::[\w ]*\n\n"
        while re.search(pattern, text):
            text = re.sub(pattern, "", text)

        return dedent(text)


def main():
    parser = argparse.ArgumentParser(prog="dptools",
                                     description="DPTools CLI for doing stuff with deepmd-kit\n\n"\
                                             "Complete documentation available at: "\
                                             "https://dptools.rtfd.io",
                                     formatter_class=MyFormatter,
                                     )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(title="commands", dest="command")
    # TODO: Add logging
    command_clis = {}
    for comm in commands:
        mod = "dptools.cli." + comm
        CLI = import_module(mod).CLI
        doc = CLI.__doc__
        subparser = subparsers.add_parser(comm, help=CLI.help_info, description=doc,
                formatter_class=MyFormatter)
        cli = CLI(subparser)
        cli.add_args()
        command_clis[comm] = cli

    parsed_args = parser.parse_args()
    command_clis[parsed_args.command].main(parsed_args)
