import os
import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class Project:
    def __init__(self, url, keystore_filename, keystore_pwd, key, key_pwd, name=""):
        if name is None or len(name) == 0:
            self.name = self.get_name_from_url(url)
        else:
            self.name = name
        self.url = url
        self.keystore_filename = keystore_filename
        self.keystore_pwd = keystore_pwd
        self.key = key
        self.key_pwd = key_pwd

    def __str__(self):
        return "%s: %s" % (self.name, self.url)

    def get_name_from_url(self, url):
        splitted = url.split("/")
        return os.path.splitext(splitted[-1])[0]


class Store:
    def __init__(self):
        try:
            with open("./projects.yml", "r") as f:
                self._data = yaml.load(f, Loader=Loader)
            self.save()
        except Exception as ex:
            print("Failed to load projects.yml! " + str(ex))
            self._data = {}
            self.save()

    def get_data(self):
        return self._data

    def is_url_exists(self, url):
        for p in self._data:
            if url.lower() == p.url.lower():
                return True
        return False

    def search(self, sentence):
        projects = []
        for value in self._data:
            if value.name.lower().find(sentence.lower()) >= 0 and value not in projects:
                projects.append(value)
            if value.url.lower().find(sentence.lower()) >= 0 and value not in projects:
                projects.append(value)

        if len(projects) > 1:
            raise Exception("Ambiguous name detected: " + ", ".join([str(p) for p in projects]))
        if len(projects) == 0:
            raise Exception("Project not found")

        return projects[0]

    def remove_project(self, project):
        self._data.remove(project)
        self.save()

    def save(self):
        with open("./projects.yml", "w") as f:
            yaml.dump(self._data, f, allow_unicode=True)

    def add_project(self, project):
        self._data.append(project)
        self.save()