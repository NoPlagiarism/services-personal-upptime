"""
pip install ruamel.yaml httpx
"""
import os
from typing import Optional, Union
import json

import httpx
from ruamel.yaml import YAML, yaml_object, CommentedSeq

HEADERS = {"User-Agent": "@NoPlagiarism / services-personal-upptime"}
ALL_JSON_URL = "https://raw.githubusercontent.com/NoPlagiarism/frontend-instances-list/master/instances/all.json"
UPPTIMERC_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".upptimerc.yml")

SERVICES = ("proxitok", "gothub", "wikiless", "librarian (discontinued)")


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
                 icon: Optional[str] = None, expected_status_codes: Optional[tuple] = None, **kwargs):
        self.data = dict(name=name, url=url)
        for name, value in dict(method=method, port=port, body=body, icon=icon,
                                expected_status_codes=expected_status_codes, **kwargs).items():
            if value is not None:
                self.data[name] = value

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
            new_sites.append(Site(name=f"{name} {domain}", url=get_url_from_domain(domain)))
    old_sites = Site.from_tuple(upptime_cfg.get_sites())
    if old_sites == new_sites:
        return
    upptime_cfg.set_sites(list(map(Site.to_json, new_sites)))
    upptime_cfg.save()


if __name__ == '__main__':
    main()
