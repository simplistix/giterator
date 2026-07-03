from argparse import ArgumentParser, Namespace


class Command:

    def add_args(self, parser: ArgumentParser):
        pass

    def __call__(self, args: Namespace):
        pass


class Pack(Command):
    pass


class Unpack(Command):
    pass


def parse_args() -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True
    for command_class in Command.__subclasses__():
        command_parser = subparsers.add_parser(command_class.__name__.lower())
        command = command_class()
        command.add_args(command_parser)
        command_parser.set_defaults(command=command)
    return parser.parse_args()


def main():
    args = parse_args()
    args.command(args)
