"""Bundle explicitly named W1 artifacts and project config; does not execute Git."""
import argparse
import json
from pathlib import Path
import integration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path, required=True)
    parser.add_argument('--acceptance', nargs=3, action='append', required=True,
                        metavar=('ROLE', 'REQUEST_FILE', 'REPORT_FILE'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = json.loads(args.configuration.read_text())
    value['acceptance'] = [{'role': role, 'request_text': Path(request).read_bytes().decode('utf-8'),
                            'report': json.loads(Path(report).read_text())}
                           for role, request, report in args.acceptance]
    integration.validate(value)
    args.output.write_bytes(integration.w1.encoded(value) + b'\n')
    print(integration.w1.digest(args.output.read_bytes()))


if __name__ == '__main__':
    main()
