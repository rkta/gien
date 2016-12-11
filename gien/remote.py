from github import Github, GithubException

def fetch_rate_limit(api):
    limit = api.get_rate_limit()
    return "{}/{} requests, last reset at {} (UTC)".format(limit.rate.remaining,
            limit.rate.limit, limit.rate.reset)

def fetch_issues(opts):
    data = []
    repo = None

    api = Github(opts.user, opts.password)
    print("Rate limit:", fetch_rate_limit(api))

    repo = api.get_repo(opts.repository)
    issues = repo.get_issues(state=opts.issues, direction="asc")
    data = [{
        "issue"    : i,
        "comments" : i.get_comments(), # ordered by ascending id
        "labels"   : i.get_labels() } for i in issues ] # ordered by created asc

    return data, repo
