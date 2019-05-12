# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# MIT License, included in this distribution as LICENSE

import sys
from metapack import Downloader
from metapack.cli.core import prt, err

from rowgenerators import parse_app_url
from rowgenerators.exceptions import AppUrlError
from metapack.index import SearchIndex, search_index_file
from textwrap import dedent
import json

downloader = Downloader.get_instance()

def search(subparsers):

    parser = subparsers.add_parser(
        'search',
        description=dedent("""
        Index packages for searching. 

        The index file is a JSON file, which is by default index.json in the cache. 
        The file can be moved by setting the METAPACK_SEARCH_INDEX environmental variable.


        """))

    parser.add_argument('-l', '--list', default=False, action='store_true',
                        help="List the packages in the index")

    parser.add_argument('-f', '--format', help='Select a specific package format')

    parser.add_argument('-1', '--one', action='store_true',
                        help='Find only one result, using the same resolution process used when building packages')

    parser.add_argument('-p', '--path', default=False, action='store_true',
                        help="Instead of displaying the Metapack URL, display only the local file path")

    parser.add_argument('-c', '--config', default=False, action='store_true',
                        help="Show the path to the index file")

    parser.add_argument('-j', '--json', default=False, action='store_true',
                       help="Output json for some commands")

    parser.set_defaults(run_command=run_search)

    parser.add_argument('search', nargs='?', help="Path or URL to a metatab file")


def maybe_path(args,e):
    if args.path:
        u = parse_app_url(e).inner
        if u.proto == 'file':
            return u.fspath
        else:
            return ''
    else:
        return e

def run_search(args):

    from tabulate import tabulate

    if args.config:
        prt(search_index_file())
        sys.exit(0)

    if not args.search or args.list:

        idx = SearchIndex(search_index_file())

        if args.json:

            packages = [e for e in idx.list() if args.format is None or args.format == e['format']]

            print(json.dumps(packages))
        else:

            packages = [(e['name'], e['format'], maybe_path(args, e['url'])) for e in idx.list()
                        if args.format is None or args.format == e['format']]

            print(tabulate(packages, headers='Name Format Url'.split()))

    elif args.one:

        if args.search.startswith('index'):
            url_s = args.search
        else:
            url_s = 'index:' + args.search

        try:
            u = parse_app_url(url_s)

            prt(str(maybe_path(args,u.get_resource())))

        except AppUrlError as e:
            err(f"Failed to resolve: {str(u)}; {str(e)}")

    else:

        idx = SearchIndex(search_index_file())

        prt('Index file:', idx.path)

        p = idx.search(args.search, args.format)

        packages = []
        for e in p:
            packages.append((e['name'], e['format'], e['url']))

        print(tabulate(packages, headers='Name Format Url'.split()))




