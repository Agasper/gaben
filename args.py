import argparse
from io import StringIO

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        with StringIO() as msg:
            self.print_help(msg)
            msg.write("\r\n" + message)
            raise Exception(msg.getvalue())