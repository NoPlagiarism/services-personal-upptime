"""pip install PyGithub"""
import os
from collections import defaultdict
from typing import Iterable, Union
import time

from github import Github
from github.Issue import Issue
from github.Label import Label

GITHUB_REPO = "NoPlagiarism/services-personal-upptime"

ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
API_PATH = os.path.join(ROOT_PATH, 'api')


class GitHuby:
    EXCLUDED_LABELS = ('status', )

    def __init__(self):
        self.api = self.auth()
        self.repo = self.api.get_repo(GITHUB_REPO)

    def auth(self) -> Github:
        try:
            token = os.environ["GH_PAT"]
        except KeyError:
            print("Pleas insert token onto environ")
            exit(-1)
            return  # Just IDE moment.
        return Github(token)
        # return Github(token, base_url="http://127.0.0.1:8000")

    @staticmethod
    def _check_label_in_list(label: Union[Label, str], excluded):
        if isinstance(label, Label):
            return label.name not in excluded
        else:
            return label not in excluded

    @classmethod
    def _check_label_in_excluded(cls, label):
        return cls._check_label_in_list(label, cls.EXCLUDED_LABELS)

    @staticmethod
    def _transfer_label_to_str(label: Union[Label, str]):
        if isinstance(label, str):
            return label
        elif isinstance(label, Label):
            return label.name
        return str(label)

    def _get_labels_not_excluded(self, labels: Iterable[Union[Label, str]], return_str=False):
        res = tuple(filter(self._check_label_in_excluded, labels))
        if return_str:
            return tuple(map(self._transfer_label_to_str, res))
        return res

    def get_open_status_issue_tags_n_issues(self):
        result = defaultdict(list)
        resp = self.repo.get_issues(labels=['status'], state='open')
        if isinstance(resp, Issue):
            resp = [resp]
        for x in resp:
            result[self._get_labels_not_excluded(x.labels, return_str=True)[0]].append(x)
        return result

    def _close_issue(self, issue: Union[int, Issue]):
        if isinstance(issue, int):
            issue = self.repo.get_issue(issue)
        try:
            issue.create_comment("Closing due removing from instance list")
        except Exception:
            print("Can't create comment")
        issue.edit(state="closed")
        return

    def close_issues(self, issues: Iterable[Union[int, Issue]], _timeout=1):
        for issue in issues:
            self._close_issue(issue)
            time.sleep(_timeout)


def get_all_directories(path) -> tuple:
    return tuple(filter(lambda x: os.path.isdir(os.path.join(path, x)), os.listdir(path)))


def main():
    gh = GitHuby()
    labels_issues = gh.get_open_status_issue_tags_n_issues()

    old_labels = set(labels_issues.keys())
    new_labels = set(get_all_directories(API_PATH))
    deleted_labels = old_labels - new_labels

    issues_to_delete = list()
    for x in deleted_labels:
        issues_to_delete.extend(labels_issues[x])
    gh.close_issues(issues_to_delete)


if __name__ == '__main__':
    main()
