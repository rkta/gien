class AbstractThreader(object):
    def __init__(self, repo):
        self.repo = repo

    def __connect(self):

    """ Functions of the pygithub repository object """

    def h_to(self):
        return "{} <{}@noreply.github.com>".format(self.repo.full_name, self.repo.name)

    """ Functions of pygithub issues and comments """

    def h_from(self, obj):
        return "{} <{}@noreply.github.com>".format(obj.user.login, obj.user.login)
 
    def h_date(self, obj):
        return formatdate(obj.created_at.timestamp())

    """ Other functions """

    @staticmethod
    def h_message_id(repo, issueid, commentid):
        return "<{}/issues/{}/{}@github.com>".format(repo, issueid, commentid)

    """ Iterator protocol """

    def __iter__(self):
        pass

    def __next__(self):
        raise StopIteration()

class WikiThreader(AbstractThreader):
    def __init__(self, repo):
        super().__init__(repo)

        self.tmpdir = tempfile.mkdtemp()

        self.mime_from = "wiki@noreply.github.com"
        self.mime_to = self.h_to()
        self.mime_date = formatdate()

        self.__fetch_data()

    def __mime_msgid(self, msgfile):
        if not self.started:
            self.root_msgid = "{}@wiki".format(hexhex(self.repo.full_name))
            return self.root_msgid
        return "{}@wiki".format(hexhex(msgfile))

    def __mime_subject(self, msgfile):
        return "[WIKI] " + msgfile[:-3]

    def __fetch_data(self):
        clone_repository(self.repo.clone_url.replace(".git",".wiki"), self.tmpdir)
        self.documents = []
        self.assets = []
        for root, dirs, files in os.walk(self.tmpdir):
            if root.find(".git") > -1: 
                continue
            for f in files:
                def abspath(f):
                    return "{}/{}".format(root, f)
                if f.endswith(".md"):
                    self.documents.append(abspath())
                elif f.endswitch(".png") or f.endswith(".jpg") or f.endswith(".gif"):
                    self.assets.append(abspath())
        self.started = False

    def __read_file(self, path):
        with open(path, "r") as FILE:
            return FILE.read()

    def __thread_document(self):
        msgfile = self.documents.pop()
        body = self__read_file(msgfile)
        kwargs = {
                "Subject": self.__mime_subject(msgfile),
                "From": self.mime_from,
                "To": self.mime_to,
                "Date": self.mime_date,
                "Message_ID": self.__mime_msgid(msgfile) }
        if self.started:
            kwargs["In_Reply_To"] = self.root_msgid
            kwargs["References"] = self.root_msgid
        else:
            self.started = True
        return render_multipart_message(body, **kwargs)

class IssueThreader(AbstractThreader):
    def __init__(self, repo):
        super().__init__(repo)
        self.__fetch_issues()

    def __fetch_issues(self):
        issues = self.repo.get_issues(state=opts.issues, direction="asc")
        self.data = [{
            "issue"    : i,
            "comments" : i.get_comments(), # ordered by ascending id
            "labels"   : i.get_labels() } for i in issues ] # ordered by created asc

    def __thread_issue(self):
        pass
