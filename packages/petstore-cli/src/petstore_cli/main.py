import argparse
import json
import os
import sys

from petstore_cli.client import PetstoreClient

DEFAULT_BASE_URL = 'http://localhost:8000/api'


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def _add_pet_fields(parser: argparse.ArgumentParser, *, name_required: bool) -> None:
    parser.add_argument('--name', required=name_required)
    parser.add_argument('--category')
    parser.add_argument('--photo-urls', help='comma-separated')
    parser.add_argument('--tags', help='comma-separated')
    parser.add_argument('--status', default='available')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='petstore-cli')
    parser.add_argument(
        '--base-url',
        default=os.environ.get('PETSTORE_API_URL', DEFAULT_BASE_URL),
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    list_parser = subparsers.add_parser('list', help='list pets')
    list_parser.add_argument('--status')

    get_parser = subparsers.add_parser('get', help='get a pet by id')
    get_parser.add_argument('pet_id', type=int)

    create_parser = subparsers.add_parser('create', help='create a pet')
    _add_pet_fields(create_parser, name_required=True)

    update_parser = subparsers.add_parser('update', help='update a pet')
    update_parser.add_argument('pet_id', type=int)
    _add_pet_fields(update_parser, name_required=True)

    delete_parser = subparsers.add_parser('delete', help='delete a pet by id')
    delete_parser.add_argument('pet_id', type=int)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    with PetstoreClient(args.base_url) as client:
        if args.command == 'list':
            print(json.dumps(client.list_pets(args.status), indent=2))
        elif args.command == 'get':
            print(json.dumps(client.get_pet(args.pet_id), indent=2))
        elif args.command == 'create':
            result = client.create_pet(
                name=args.name,
                category=args.category,
                photo_urls=args.photo_urls,
                tags=args.tags,
                status=args.status,
            )
            print(json.dumps(result, indent=2))
        elif args.command == 'update':
            result = client.update_pet(
                args.pet_id,
                name=args.name,
                category=args.category,
                photo_urls=_split_csv(args.photo_urls),
                tags=_split_csv(args.tags),
                status=args.status,
            )
            print(json.dumps(result, indent=2))
        elif args.command == 'delete':
            client.delete_pet(args.pet_id)
            print(f'deleted pet {args.pet_id}')


if __name__ == '__main__':
    sys.exit(main())
