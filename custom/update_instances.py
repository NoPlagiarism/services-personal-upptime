"""
pip install ruamel.yaml httpx
"""
import os
from typing import Optional, Union
import json

import httpx
from ruamel.yaml import YAML, yaml_object, CommentedSeq


def make_seq_inline(x):
    # https://stackoverflow.com/questions/56937691/making-yaml-ruamel-yaml-always-dump-lists-inline#56939573
    x.fa.set_flow_style()
    return x


HEADERS = {"User-Agent": "@NoPlagiarism / services-personal-upptime"}
ALL_JSON_URL = "https://raw.githubusercontent.com/NoPlagiarism/instances-list/master/instances/all.json"
UPPTIMERC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".upptimerc.yml")

SERVICES = ("proxitok", "gothub", "wikiless", "librarian (discontinued)", "anonymousoverflow", "libreddit", "breezewiki", "rimgo", "ryd-proxy", "cloudtube")
SERVICE_ICONS = {"proxitok": "https://raw.githubusercontent.com/pablouser1/ProxiTok/master/favicon-32x32.png",
                 "gothub": "https://codeberg.org/gothub/gothub/raw/branch/dev/public/assets/favicon.ico",
                 "wikiless": "https://gitea.slowb.ro/ticoombs/Wikiless/raw/branch/main/static/wikiless-favicon.ico",
                 "librarian (discontinued)": "https://codeberg.org/librarian/librarian/raw/branch/main/static/favicon/mstile-70x70.png",
                 "anonymousoverflow": "https://raw.githubusercontent.com/httpjamesm/AnonymousOverflow/main/public/codecircles.png",
                 "libreddit": "https://raw.githubusercontent.com/libreddit/libreddit/master/static/favicon.png",
                 "breezewiki": "https://gitdab.com/cadence/breezewiki/raw/branch/main/static/breezewiki-icon-color.svg",
                 "rimgo": "https://codeberg.org/video-prize-ranch/rimgo/raw/branch/main/static/img/rimgo.svg",
                 "ryd-proxy": "https://raw.githubusercontent.com/Anarios/return-youtube-dislike/main/Icons/128x128_transparent.jpg",
                 "cloudtube": "https://git.sr.ht/~cadence/cloudtube/blob/main/html/static/images/favicon-32x32.png"}
EXPECTED_STATUS_CODES = [200, 201, 202, 203, 200, 204, 205, 206, 207, 208, 226,
                         404,  # RYD-Proxy moment
                         403]  # CloudFlare moment


def get_url_from_domain(domain):
    return "https://" + domain


def get_domain_from_url(url):
    return httpx.URL(url).host


class InstanceData:
    def __init__(self, url):
        self.raw_data = httpx.get(url, headers=HEADERS).json()

    def get_clearnet_instances_by_id(self, service_id: str):
        return self.raw_data[service_id]['instances']

    def get_name_by_id(self, service_id: str):
        return self.raw_data[service_id]['name']

    def get_clearnet_and_names_by_id(self, service_id: str):
        return {"name": self.raw_data[service_id]['name'],
                "instances": self.raw_data[service_id]['instances']}


class SitesUpptime:
    def __init__(self):
        self.yaml = YAML()
        self.data = self.load()

    def load(self, filepath=None):
        if filepath is None:
            filepath = UPPTIMERC_PATH
        with open(filepath, encoding="utf-8", mode="r") as f:
            return self.yaml.load(f)

    def save(self, data=None, filepath=None):
        if data is None:
            data = self.data
        if filepath is None:
            filepath = UPPTIMERC_PATH
        with open(filepath, encoding="utf-8", mode="w") as f:
            return self.yaml.dump(data, f)

    def get_sites(self) -> list:
        return list(self.data['sites'])

    def append_site(self, name: str, url: str, **kwargs):
        self.data['sites'].append(dict(name=name, url=url, **kwargs))

    def extend_site(self, new_sites):
        self.data['sites'].extend(new_sites)

    def set_sites(self, new_sites: list):
        self.data['sites'].clear()
        self.data['sites'].extend(new_sites)


class Site:
    def __init__(self, name: str, url: str, method: Optional[str] = None, port: Optional[int] = None, body: Optional[str] = None,
                 icon: Optional[str] = None, expected_status_codes: Optional[list] = None, **kwargs):
        self.data = dict(name=name, url=url)
        for name, value in dict(method=method, port=port, body=body, icon=icon, **kwargs).items():
            if value is not None:
                self.data[name] = value
        for name, value in dict(expectedStatusCodes=expected_status_codes).items():
            if value is not None:
                self.add_property_list(name, value)

    @classmethod
    def from_dict(cls, data: dict):
        return Site(**data)

    @classmethod
    def from_tuple(cls, data: Union[tuple, list, set]) -> list:
        return list(map(lambda x: Site(**x), data))

    def update(self, other: Union["Site", dict]):
        if isinstance(other, Site):
            self.data.update(other.data)
        else:
            self.data.update(other)

    def add_property_list(self, name, value, is_inline_value=True):
        self.data[name] = CommentedSeq()
        self.data[name].extend(value)
        if is_inline_value:
            self.data[name] = make_seq_inline(self.data[name])

    def __getitem__(self, item):
        return self.data.get(item)

    def __setitem__(self, key, value):
        self.data[key] = value

    def is_same_url(self, other):
        return self['url'] == other['url']

    def __eq__(self, other):
        return self.data == other.data

    def __repr__(self):
        return json.dumps(self.data)

    def to_json(self):
        return self.data


def main():
    instance_data = InstanceData(ALL_JSON_URL)
    upptime_cfg = SitesUpptime()

    new_sites = list()
    for service in SERVICES:
        name = instance_data.get_name_by_id(service)
        for domain in instance_data.get_clearnet_instances_by_id(service):
            new_sites.append(Site(name=f"{name} {domain}", url=get_url_from_domain(domain),
                                  icon=SERVICE_ICONS.get(name), expected_status_codes=EXPECTED_STATUS_CODES))
    old_sites = Site.from_tuple(upptime_cfg.get_sites())
    if old_sites == new_sites:
        return
    upptime_cfg.set_sites(list(map(Site.to_json, new_sites)))
    upptime_cfg.save()


if __name__ == '__main__':
    main()
