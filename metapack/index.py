# Copyright (c) 2017 Civic Knowledge. This file is licensed under the terms of the
# Revised BSD License, included in this distribution as LICENSE

"""

"""

import json
from os import rename
from shutil import copy
from os.path import exists
from os import rename


def search_index_file():
    """Return the default local index file, from the download cache"""
    from metapack import Downloader
    from os import environ

    return environ.get('METAPACK_SEARCH_INDEX',
                       Downloader().cache.getsyspath('index.json'))

class SearchIndex(object):

    pkg_format_priority = {
        'fs': 5,
        'zip': 4,
        'xlsx': 3,
        'csv': 2,
        'source': 1
    }

    def __init__(self, path):
        self.path = path

        self._db = None

    def open(self):
        if not self._db:
            try:
                with open(self.path) as f:
                    self._db = json.load(f)
            except FileNotFoundError:
                self._db = {}

    def clear(self):

        self._db = {}
        self.write()

    def write(self):
        """Safely write the index data to the index file """
        index_file = self.path
        new_index_file = index_file + '.new'
        bak_index_file = index_file + '.bak'

        with open(new_index_file, 'w') as f:
            json.dump(self._db, f, indent=4)

        if exists(index_file):
            copy(index_file, bak_index_file)

        rename(new_index_file, index_file)

    def _make_package_entry(self, ident, name, nvname, version, format, url):
        """

        """

        self.open()

        try:
            version = 'V'+str(int(version)).zfill(10)
        except ValueError:
            pass

        if format is None:
            format = 'fs'

        self._db[ident] = {'t':'ident', 'ref':nvname } # these should always be equivalent

        self._db[name] = {'t':'name',  'ref': nvname, 'version': version , 'ident': ident}

        if not nvname in self._db:
            self._db[nvname] = {
                't': 'nvname',
                'packages': {}
            }

        key = '{}-{}'.format(name, format)

        self._db[nvname]['packages'][key] = {
            'name': name,
            'nvname': nvname,
            'version': version,
            'format': format,
            'ident': ident,
            'url': url
        }

    def add_package(self, pkg):
        from os.path import abspath

        from metapack.package import open_package
        ref_url = pkg.package_url.clone()
        ref_url.path = abspath(ref_url.path)

        ref = str(ref_url)

        nv_name = pkg._generate_identity_name(mod_version=None)  # Non versioned-name, for the latest package
        name = pkg.name
        version = pkg.get_value('Root.Version')
        identifier = pkg.get_value('Root.Identifier')

        if not pkg.get_value('Root.Issued'):
            format = 'source'
        else:
            format = ref_url.get_resource().get_target().target_format

        self._make_package_entry(identifier, name, nv_name, version, format, ref)

    def add_entry(self, ident, name, nvname, version, format, url):
        self._make_package_entry(ident, name, nvname, version, format, url)

    def update(self,o):
        """Update from another index or index dict"""

        self.open()

        try:
            self._db.update(o._db)
        except AttributeError:
            self._db.update(o)


    def list(self):

        packages = []

        self.open()

        for k, v in  self._db.items():
            if v.get('t') == 'nvname':
                for pkey, e in v.get('packages').items():
                    packages.append(e)

        return list(reversed(sorted(packages, key=lambda x: (x['name'], x['version'], self.pkg_format_priority[x['format']]))))

    def records(self):
        self.open()
        for k,v in self._db.items():
            if v['t'] == 'nvname':
                for pk, pv in v['packages'].items():
                    yield [pv['name'], pv['nvname'], pv['version'], pv['format'], pv['url']]

    def search(self, key, format='issued'):
        from rowgenerators import parse_app_url

        url = parse_app_url(key)

        search_term = url.path

        self.open()

        if format == 'all':
            format = None
        elif format == 'issued':
            format = ['zip','csv','xlsx','fs']

        if format and not isinstance(format, (list, tuple)):
            format = [format]

        record = self._db.get(search_term) # Case when the term is a name, nvname, or ident

        if record:
            records = [record]
            match_type = 'exact'
        else:
            records = [ record for k, record in self._db.items() if search_term in k]
            match_type = 'subset'

        packages = []
        seen = set()
        for e in records:

            key_type = e['t']

            if key_type == 'ident':
                match_key = 'nvname'
                match_value = e['ref']
            else:
                match_key = key_type
                match_value = search_term

            if e.get('ref'):
                e = self._db[e['ref']]

            for pkey, p in e['packages'].items():

                if (match_type == 'exact' and p[match_key] == match_value) or \
                   (match_type == 'subset' and search_term in p[match_key]):
                    if (format and p['format'] in format) or format is None:
                        if not (p['format'],p['name']) in seen:
                            packages.append(p)
                            seen.add((p['format'],p['name']))

        return list(reversed(sorted(packages, key=lambda x: (x['version'], self.pkg_format_priority[x['format']]) )))