import sys
import os
import shutil
import json
from enum import IntEnum, auto
from subprocess import call

import gitlab
import github

from utils import align


# tilde expansion
path = os.path.expanduser("~/")

# URLs
gitlab_url = "https://gitlab.com"
github_url = "https://github.com"


def create_folder(folder_name):
	proj_dir = path + folder_name
	if not os.path.exists(proj_dir):
		os.makedirs(proj_dir)
		print("Folder: " + folder_name + " created")
	else:
		print("Folder: " + folder_name + " already exists")

# Not used for now
def delete_folder(folder_name):
	proj_dir = path + folder_name
	if os.path.exists(proj_dir):
		shutil.rmtree(proj_dir)
		print("Folder: " + folder_name + " deleted")
	else:
		print("Folder: " + folder_name + " not exists")

def git_initial_commit(git_url, username, repo_name):
	os.chdir(path + "/" + repo_name)
	call(["git",
		"init"])
	call(["git",
		"remote",
		"add",
		"origin", "{0}/{1}/{2}.git".format(
						git_url,
						username,
						repo_name.replace(' ', '-'))])
	call(["touch",
		"README.md"])
	call(["git",
		"add", "."])
	call(["git",
		"commit",
		"-m", "Initial commit"])
	call(["git",
		"push", "-u", "origin", "master"])

def show_projs(projs):
	print(align("Project name", length=30),
		align("Project ID", length=12),
		align("Visibility", length=12),
		"Created at")
	print("-" * 67)
	for proj in projs:
		if settings.git_host == "github":
			print(align(proj.name, length=30),
				align(str(proj.id), length=12),
				align(Visibility.private if proj.private else Visibility.public, length=12),
				proj.created_at)
		else:
			date = proj.created_at.split('T')[0]
			time = proj.created_at.split('T')[1].split('.')[0]
			print(align(proj.name, length=30),
				align(str(proj.id), length=12),
				align(proj.visibility, length=12),
				"{0} {1}".format(date, time))

class Settings:
	def __init__(self):
		with open("settings.json", "r+") as settings_file:
			settings_obj = json.load(settings_file)
		self.git_host = settings_obj["git_host"]
		self.token = settings_obj["gitlab"]["token"]
		self.username = settings_obj["github"]["username"]
		self.password = settings_obj["github"]["password"]
	def set_git_host(self, git_host):
		with open("settings.json", "r+") as settings_file:
			settings = json.load(settings_file)
			settings["git_host"] = git_host
			# Write
			settings_file.seek(0)  # rewind
			json.dump(settings, settings_file, sort_keys=True, indent='\t')
			settings_file.truncate()

class Visibility:
	public = "public"
	internal = "internal"
	private = "private"
	default = private

class GitLab():
	def __init__(self):
		if settings.token == "":
			print("Please set GitLab Personal Access Token in settings file")
			exit(0)
		self.__gl = gitlab.Gitlab("https://gitlab.com/", private_token=settings.token)
		self.__gl.auth()

	def show(self):
		# Show owned projects
		gl = self.__gl
		all_owned_projects = gl.projects.list(owned=True, all=True)
		show_projs(all_owned_projects)

	def create(self, proj_name, visibility=Visibility.default):
		gl = self.__gl
		current_user = gl.user
		username = current_user.username
		url = gitlab_url

		# Create folder
		create_folder(proj_name)

		# Create project in GitLab
		project = gl.projects.create({
				"name": proj_name,
				"visibility": visibility})
		print("Project: {0} created".format(project.name))

		# Initial commit with existing folder
		git_initial_commit(url, username, proj_name)

	def delete(self, proj_id):
		"""Delete project by id.

		Parameters
		----------
		proj_id : int
		    ID of the target project.
		"""
		gl = self.__gl
		try:
			project = gl.projects.get(proj_id)
			project.delete()
			print("Project: {0} deleted".format(project.name))
		except Exception as e:
			print("Error: Project not found")

class GitHub():
	def __init__(self):
		if settings.username == "" or settings.password == "":
			print("Please set GitHub username and password in settings file")
			exit(0)
		self.__gh = github.Github(settings.username, settings.password)
		self.__user = self.__gh.get_user()
		self.__user.login

	def show(self):
		# Show user's repository
		user = self.__user
		repos = user.get_repos()
		show_projs(repos)

	def create(self, repo_name, visibility=Visibility.default):
		user = self.__user
		url = github_url

		# Create folder
		create_folder(repo_name)

		# Create repository in GitHub
		repo = user.create_repo(repo_name)
		if visibility == Visibility.private:
			repo.edit(private=True)
		print("Repository: {0} created".format(repo.name))

		# Initial commit with existing folder
		git_initial_commit(url, settings.username, repo_name)

	def delete(self, repo_id):
		"""Delete repository by id.

		Parameters
		----------
		repo_id : int
		    ID of the target repository.
		"""
		gh = self.__gh
		try:
			repo = gh.get_repo(repo_id)
			repo.delete()
			print("Repository: {0} deleted".format(repo.name))
		except Exception as e:
			print("Error: Repository not found")

def git_host_init():
	if settings.git_host == "github":
		git_host = GitHub()
	else:
		git_host = GitLab()
	return git_host

# Status code of command_handler
class Status(IntEnum):
	OK = auto()
	FAIL = auto()

# Help message of commands
cmd_help = (
	"proj (using GitLab)\n"
	"    gitlab|github             Switch Git hosting\n"
	"    show                      Show owned projects\n"
	"    create <proj_name>        Create new project\n"
	"    delete <proj_id>          Delete project\n"), (
	"proj (using GitHub)\n"
	"    gitlab|github             Switch Git hosting\n"
	"    show                      Show owned repositories\n"
	"    create <repo_name>        Create new repository\n"
	"    delete <repo_id>          Delete repository\n")

def show_cmd_help():
	if settings.git_host == "github":
		print(cmd_help[1])
	else:
		print(cmd_help[0])

def command_handler(cmd):
	cmd.pop(0)
	if len(cmd) == 0:
		show_cmd_help()
		return Status.FAIL

	tok = cmd.pop(0)
	if tok == "gitlab" or tok == "github":
		settings.set_git_host(tok)
		print("Git hosting set to {0}".format(tok))
		return Status.OK
	elif tok == "show":
		git_host_init().show()
		return Status.OK
	elif tok == "create":
		if len(cmd) > 0:
			name = " ".join(cmd)
			git_host_init().create(name)
			return Status.OK
		else:
			return Status.FAIL
	elif tok == "delete":
		if len(cmd) > 0:
			id = int(cmd.pop(0))
			git_host_init().delete(id)
			return Status.OK
		else:
			return Status.FAIL
	elif tok == "test":
		return Status.OK
	else:
		show_cmd_help()
		return Status.FAIL

if __name__ == "__main__":
	settings = Settings()

	command_handler(sys.argv)
