#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from slackclient import SlackClient
from store import Store, Project
from builder import Builder
from io import StringIO
from args import ArgumentParser

import time
import re
import json
import config
import os
import shlex

#to be useful
#https://docs.python.org/2/howto/argparse.html

class Gaben:
    def __init__(self, api_key, rep_directory):
        self.api_key = api_key
        self.slack = SlackClient(api_key)
        self.store = Store()
        self.builder = Builder(rep_directory)

    def run(self):
        if self.slack.rtm_connect(auto_reconnect=True):
            print("Gabe is ready!")
            while True:
                data_list = self.slack.rtm_read()
                for data in data_list:
                    if "type" in data and "subtype" not in data and data["type"] == "message":
                        self.incoming_im(data)
                time.sleep(1)
        else:
            print("Slack connection failed...")

    def get_user_info(self, data):
        return self.slack.api_call("users.info", user=data["user"])

    def incoming_im(self, data):
        text = data["text"].strip().replace("“", "\"").replace("”", "\"")
        user_info = self.get_user_info(data)
        if user_info["user"]["name"] == self.slack.server.username:
            return

        print ("%s: %s" % (user_info["user"]["name"], text))

        if text[:3].lower() == "add":
            self.incoming_add(data, text)
        elif text[:6].lower() == "remove":
            self.incoming_remove(data, text)
        elif text.strip().lower() == "projects":
            self.incoming_projects(data)
        elif text[:5].lower() == "build":
            self.incoming_build(data, text)
        elif text[:5].lower() == "alter":
            self.incoming_alter(data, text)
        elif text[:4].lower() == "jobs":
            self.incoming_jobs(data)
        else:
            if data["channel"] not in config.DONT_PRINT_USAGE_FOR:
                self.send_usage(data)

    def send_usage(self, data):
        self.send_msg(data, """Usage:
add - add a new project
remove - remove a project and clean it's data
alter - change parameters of the project
projects - get list of all projects
build - build a project
jobs - show current tasks and projects statuses""")

    def send_msg(self, data, text):
        self.slack.rtm_send_message(data["channel"], text)

    def incoming_alter(self, data, text):
        cmd = shlex.split(text)[1:]
        parser = ArgumentParser(prog="alter", description='Alter an existing project')
        parser.add_argument("name", help="Name or url of the project")
        parser.add_argument("--keystore", help="Path of the keystore file relative to the project root", default="")
        parser.add_argument("--keystore_pwd", help="Keystore password", default="")
        parser.add_argument("--key", help="Keystore key", default="")
        parser.add_argument("--key_pwd", help="Keystore key password", default="")
    
        try:
            args = parser.parse_args(cmd)
            project = self.store.search(args.name)

            if len(args.keystore) > 0:
                project.keystore_filename = args.keystore
            if len(args.keystore_pwd) > 0:
                project.keystore_pwd = args.keystore_pwd
            if len(args.key) > 0:
                project.key = args.key
            if len(args.key_pwd) > 0:
                project.key_pwd = args.key_pwd

            self.store.save()
            self.send_msg(data, "Project altered")

        except Exception as ex:
           self.send_msg(data, str(ex))

                
            

    def incoming_add(self, data, text):
        cmd = shlex.split(text)[1:]
        parser = ArgumentParser(prog="add", description='Add a new project')
        parser.add_argument("url", help="Git url of the repository")
        parser.add_argument("--keystore", help="Path to the keystore file relative to the project root", default="")
        parser.add_argument("--keystore_pwd", help="Keystore password", default="")
        parser.add_argument("--key", help="Keystore key", default="")
        parser.add_argument("--key_pwd", help="Keystore key password", default="")
        parser.add_argument("--name", help="Name of the project (optional)", default="")
        
        try:
            args = parser.parse_args(cmd)
            args.url = re.sub(r"<mailto:(.+)\|(.+)>", lambda m: m.group(1), args.url)

            if self.store.is_url_exists(args.url):
                raise Exception("Project with url %s already exists" % args.url)
        
            project = Project(args.url, args.keystore, args.keystore_pwd, args.key, args.key_pwd, args.name)
            self.store.add_project(project)
            self.send_msg(data, """Project added with parameters:
*Url:* %s
*Keystore file path:* %s
*Keystore password:* %s
*Key:* %s
*Key password:* %s
*Name:* %s
""" % (project.url, project.keystore_filename, project.keystore_pwd, project.key, project.key_pwd, project.name))
        except Exception as ex:
           self.send_msg(data, str(ex))

    def incoming_remove(self, data, text):
        cmd = shlex.split(text)[1:]
        parser = ArgumentParser(prog="remove", description='Remove project')
        parser.add_argument("name", help="Name or url of the project")

        try:
            args = parser.parse_args(cmd)
            project = self.store.search(args.name)
            self.builder.clean_project(project)
            self.store.remove_project(project)
            self.send_msg(data, "Project *%s* removed" % str(project))
        except Exception as ex:
            self.send_msg(data, str(ex))
            return


    def incoming_projects(self, data):
        projects = self.store.get_data()
        result = ""
        for project in projects:
            result += "*%s:* %s keystore=%s key=%s\r\n" % (project.name, project.url, project.keystore_filename, project.key)

        if len(result) == 0:
            self.send_msg(data, "No projects added")
        else:
            self.send_msg(data, result)


    def incoming_build(self, data, text):
        platforms = ["Win", "Win64", "OSXUniversal", "Linux", "Linux64", "LinuxUniversal", "iOS", "Android"]
        scripting_backengs = ["il2cpp","mono"]
        cmd = shlex.split(text)[1:]
        parser = ArgumentParser(prog="build", description='Build the project')
        parser.add_argument("name", help="Name or url of the project")
        parser.add_argument("branch", help="Branch of the repositary")
        parser.add_argument("platform", help="Platform: " + ",".join(platforms))
        parser.add_argument("--log", action="store_true", help="Always keep log, even if build was successful")
        parser.add_argument("--clean", action="store_true", help="Make a clean build (remove unity cache)")
        parser.add_argument("--backend", help="Override scripting backend: " + ",".join(scripting_backengs), default="")
        parser.add_argument("--build", type=int, help="Override build number", default=-1)
        parser.add_argument("--version", help="Override build version", default="")
        parser.add_argument("--development", action="store_true", help="Make a developement build (default is Release)")
        parser.add_argument("--profiler", action="store_true", help="Autoconnect profiler")
        parser.add_argument("--donotsign", action="store_true", help="(Android only) Do not sign build")
        parser.add_argument("--split", action="store_true", help="(Android only) Split APK (default is single APK)")
        try:
            args = parser.parse_args(cmd)
            project = self.store.search(args.name)
            if args.platform not in platforms:
                raise Exception("Unknown platform %s. Possible options: %s" % (args.platform, ",".join(platforms)))
            if args.backend not in scripting_backengs and len(args.backend) > 0:
                raise Exception("Unknown scripting backend %s. Possible options: %s" % (args.backend, ",".join(scripting_backengs)))
            if args.backend == "il2cpp" and args.platform in ["Win", "Win64", "OSXUniversal", "Linux", "Linux64", "LinuxUniversal"]:
                raise Exception("%s backend doesn't work on platform %s" % (args.backend, args.platform))
            if args.backend == "mono" and args.platform == "iOS":
                raise Exception("%s backend doesn't work on platform %s" % (args.backend, args.platform))
            self.builder.start(project, args.branch, args.platform, args.backend, not args.donotsign, \
                    args.split, args.log, args.clean, args.build, args.version, args.development, args.profiler, data, self.builder_callback)
            self.send_msg(data, config.get_random_quote())
        except Exception as ex:
            self.send_msg(data, str(ex))
            return
            
    def incoming_jobs(self, data):
        jobs = self.builder.get_jobs()
        if len(jobs) == 0:
            self.send_msg(data, "No jobs at the moment (uploading your build is not a job)")
            return
        result = "*Current jobs:*\r\n"
        for job in jobs:
            result += "*%s* -> %s\r\n" % (job.project.name, str(job.pipeline.get_current_job()) if job.pipeline is not None else "Finishing")
        self.send_msg(data, result)

    def builder_callback(self, data, project, status, file_path):
        size = os.path.getsize(file_path)
        MAX_MB = config.MAX_UPLOAD_SIZE_MB
        if size > 1024*1024*MAX_MB:
            self.send_msg(data, "Build completed, but it's exceeds %dMb size! :neutral_face:\nYou can grab build locally in %s" % (MAX_MB, file_path))
            return

        with open(file_path, "rb") as f:
            self.slack.api_call(
                'files.upload', 
                channels=data["channel"], 
                as_user=True, 
                filename=os.path.basename(file_path), 
                file=f,
            )

        if status:
            self.send_msg(data, "Build of %s completed! :+1:" % project.name)
        else:
            self.send_msg(data, ":octagonal_sign: Build of %s failed! " % project.name)
    

if __name__ == "__main__":
    Gaben(config.API_KEY, config.REP_DIRECTORY).run()