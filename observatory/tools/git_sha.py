import os

def get_sha():
    if os.path.isfile("./commit.sha"):
        gitrev = open('./commit.sha', 'r')
        sha = gitrev.read().replace('\n', '')
    else:
        import git
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
    return sha


