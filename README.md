# Project Manager
- Manage repository/project on github/gitlab
	- `show`: Show owned repos/projects
	- `create`: Create new repo/project (default visibility will be `private`) and folder under home directory
	- `delete`: Delete repo/project by ID

## Setup Authentication info
- Setup in `settings.json` file
	- GitHub: username, password
	- GitLab: [GitLab Personal Access Tokens](https://gitlab.com/profile/personal_access_tokens)

## Setup enviroment 
```sh
source my_command.sh
source venv_setup.sh
```

## Usage
```sh
proj <command>
```

## Exit
```sh
deactivate
```
