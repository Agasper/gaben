from subprocess import call, check_output, PIPE, Popen

import os
import traceback
import sys
import config
import hashlib
import threading
import shutil
import zipfile

class Builder():
    def __init__(self, rep_directory):
        self.rep_directory = rep_directory
        self.project_builds = []


    def get_jobs(self):
        return self.project_builds

    def start(self, project, branch, platform, s_backend, sign, split, keep_log, clean, build, version, development, profiler, data, callback):
        for proj_builder in self.project_builds:
            if proj_builder.project.url.lower() == project.url.lower():
                raise Exception("Project already in action")

        proj_builder = ProjectBuilder(self, project, branch, platform, s_backend, sign, split, keep_log, clean, build, version, development, profiler, data, callback)
        self.project_builds.append(proj_builder)
        proj_builder.build()
        
    def build_finished(self, proj_builder):
        self.project_builds.remove(proj_builder)

    def get_url_hash(self, url):
        md5 = hashlib.md5(url.encode("utf-8"))
        return md5.hexdigest()

    def get_project_dir(self, url, platform=None):
        hash_ = self.get_url_hash(url)
        dir_ = os.path.join(self.rep_directory, hash_)
        if platform is None:
            return dir_
        else:
            return os.path.join(dir_, platform)

    def get_project_temp_dir(self, url):
        hash_ = self.get_url_hash(url)
        return os.path.join(self.rep_directory, hash_ + "_logs")

    def clean_project(self, project):
        shutil.rmtree(self.get_project_dir(project.url))
        shutil.rmtree(self.get_project_temp_dir(project.url))



class ProjectBuilder():
    def __init__(self, parent, project, branch, platform, s_backend, sign, split, keep_log, clean, build, version, development, profiler, data, callback):
        self.parent = parent
        self.project = project
        self.branch = branch
        self.platform = platform
        self.s_backend = s_backend
        self.data = data
        self.sign = sign
        self.split = split
        self.keep_log = keep_log
        self.callback = callback
        self.clean = clean
        self.build_number = build
        self.version = version
        self.development = development
        self.profiler = profiler

        self.temp_dir = self.parent.get_project_temp_dir(self.project.url)
        self.project_dir = self.parent.get_project_dir(self.project.url, platform)
        self.bin_dir = os.path.join(self.project_dir, "bin")
        self.build_log = os.path.join(self.temp_dir, "build_log.txt")
        self.unity_build_log = os.path.join(self.temp_dir, "unity_build_log.txt")

        self.pipeline = None
        self.unity_path = None

        
    def build(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.mkdir(self.temp_dir)

        self.pipeline = Pipeline(self.pipeline_finished)
        if not os.path.isdir(self.project_dir):
            self.pipeline.add_job(ShellJob(["git", "clone", self.project.url, self.project_dir]))
    
        if self.clean:
            self.pipeline.add_job(ShellJob(["git", "clean", "-fdx"], self.project_dir))
        else:
            self.pipeline.add_job(ShellJob(["git", "clean", "-fd"], self.project_dir))
        self.pipeline.add_job(ShellJob(["git", "checkout", "."], self.project_dir))
        self.pipeline.add_job(ShellJob(["git", "fetch", "origin", self.branch], self.project_dir))
        self.pipeline.add_job(ShellJob(["git", "checkout", self.branch], self.project_dir))
        self.pipeline.add_job(ShellJob(["git", "pull", "origin", self.branch], self.project_dir))

        script_path = os.path.join(self.project_dir, "Assets", "BatchBuild.cs")
        self.pipeline.add_job(ShellJob(["cp", "-f", "./BatchBuild.cs", script_path]))
        self.pipeline.add_job(PythonJob(self.prepare_vars, script_path))
        self.pipeline.add_job(PythonJob(self.get_unity_version))
        self.pipeline.add_job(PythonJob(self.generate_build_job))

        self.pipeline.start()

    def generate_build_job(self):
        self.pipeline.add_job(ShellJob([self.unity_path, "-batchmode", "-buildTarget", self.platform, \
            "-projectPath", self.project_dir, "-executeMethod", "BatchBuild.Build" + self.platform, \
            "-logFile", self.unity_build_log], self.project_dir, output_from_file=self.unity_build_log))

        return "Build job created\r\n", "", 0

    def get_unity_version(self):
        version_file = os.path.join(self.project_dir, "ProjectSettings", "ProjectVersion.txt")
        with open(version_file, "r") as f:
            content = f.read()
        splitted = content.split(":")
        unity_version = splitted[1].strip()

        if unity_version not in config.UNITY:
            raise Exception("Unity version %s not found" % unity_version)
        self.unity_path = config.UNITY[unity_version]

        return "Detected unity version " + unity_version + "\r\n", "", 0


    def prepare_vars(self, script_path):
        self.cleanup(True)

        text = ""
        keystore_path = os.path.join(self.project_dir, self.project.keystore_filename)
        with open(script_path, "r") as f:
            text = f.read()
        text = text.replace("{BUILD_PATH}", self.bin_dir.replace("\\", "\\\\"))
        text = text.replace("{SBACKEND}", self.s_backend)
        text = text.replace("{BUILD_NUMBER}", str(self.build_number))
        text = text.replace("{VERSION}", self.version)
        text = text.replace("{DEVELOPMENT}", str(self.development).lower())
        text = text.replace("{PROFILER}", str(self.profiler).lower())

        if self.sign:
            text = text.replace("{KEYSTORE}", keystore_path.replace("\\", "/"))
            text = text.replace("{KEYSTORE_PWD}", self.project.keystore_pwd)
            text = text.replace("{KEY}", self.project.key)
            text = text.replace("{KEY_PWD}", self.project.key_pwd)
        else:
            text = text.replace("{KEYSTORE}", "")
            text = text.replace("{KEYSTORE_PWD}", "")
            text = text.replace("{KEY}", "")
            text = text.replace("{KEY_PWD}", "")

        text = text.replace("{SPLIT}", str(self.split).lower())

        with open(script_path, "w") as f:
            f.write(text)

        return "Variables prepared\r\n", "", 0


    def pipeline_finished(self, pipeline):

        with open(self.build_log, "w") as f:
            f.write(pipeline.get_output_log())
        
        if os.path.exists(self.bin_dir):
            #remove symbols
            for f in os.listdir(self.bin_dir):
                if os.path.isfile(os.path.join(self.bin_dir, f)) and f.endswith(".symbols.zip"):
                    os.remove(os.path.join(self.bin_dir, f))
            files = os.listdir(self.bin_dir)
        else:
            files = []

        if self.keep_log and os.path.exists(self.bin_dir) and not pipeline.failed:
            shutil.copyfile(self.build_log, os.path.join(self.bin_dir, "build_log.txt"))
            files.append("build_log.txt")
        
        if len(files) > 1 or (len(files) == 1 and os.path.isdir(os.path.join(self.bin_dir, files[0]))):
            build_path = os.path.join(self.temp_dir, self.project.name)
            shutil.make_archive(build_path, 'zip', self.bin_dir)
            build_path += ".zip"
        elif len(files) == 1:
            build_path = os.path.join(self.bin_dir, files[0])
        else:
            build_path = self.build_log
            
        self.callback(self.data, self.project, not pipeline.failed, build_path)
        self.cleanup()
        self.parent.build_finished(self)


    def cleanup(self, recreate=False):
        if os.path.isdir(self.bin_dir):
            shutil.rmtree(self.bin_dir)

        if recreate:
            os.mkdir(self.bin_dir)


class Pipeline(threading.Thread):
    def __init__(self, done_callback):
        super(Pipeline, self).__init__()
        self._jobs = []
        self.done_callback = done_callback
        self.running = False
        self.failed = False

    def get_current_job(self):
        for j in self._jobs:
            if not j.finished:
                return j
        if len(self._jobs) > 0:
            return self._jobs[-1]
        else:
            return None

    def get_output_log(self):
        output = ""
        for j in self._jobs:
            if j.finished:
                output += j.output
        return output

    def add_job(self, job):
        self._jobs.append(job)

    def run(self):
        self.running = True
        for job in self._jobs:
            if job.finished:
                continue
            print("Start %s" % (job,))
            job.do()
            if job.is_failed():
                self.failed = True
                self.done_callback(self)
                return
        self.running = False
        self.done_callback(self)

    
class Job:
    def __init__(self):
        self.finished = False
        self.output = ""
        self.output_error = ""
        self.error_code = 0

    def is_failed(self):
        return self.error_code != 0


class PythonJob(Job):
    def __init__(self, action, *args, **kwargs):
        super(PythonJob, self).__init__()
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return "PythonJob[%s]" % (self.action.__name__)

    def do(self):
        if self.finished:
            raise Exception("Job already finished")
        try:
            self.output, self.output_error, self.error_code = self.action(*self.args, **self.kwargs)
        except Exception as ex:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            formatted_lines = traceback.format_exc().splitlines()
            self.output = str(ex) + "\r\n" + "\r\n".join(formatted_lines)
            self.output_error = self.output
            self.error_code = 1
        self.finished = True

        print("%s finished with %s" % (self, self.error_code))



class ShellJob(Job):
    def __init__(self, cmd, cwd=None, shell=False, output_from_file=None):
        super(ShellJob, self).__init__()
        self.cmd = cmd
        self.cwd = cwd
        self.shell = shell
        self.output_from_file = output_from_file

    def do(self):
        if self.finished:
            raise Exception("Job already finished")
        self.output, self.output_error, self.error_code = self._popen(self.cmd, self.cwd, self.shell)

        try:
            self.output = self.output.decode()
        except AttributeError:
            pass

        try:
            self.output_error = self.output_error.decode()
        except AttributeError:
            pass

        if self.output_from_file is not None:
            with open(self.output_from_file, "r") as f:
                self.output = f.read()

        self.finished = True
        print("%s finished with %s" % (self, self.error_code))
    
    def __str__(self):
        return "ShellJob[cmd=%s, shell=%s]" % (self.cmd, self.shell)
    
    def _popen(self, cmd, cwd=None, shell=False):
        result = Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE, shell=shell)
        out, out_err = result.communicate()
        return out, out_err, result.returncode