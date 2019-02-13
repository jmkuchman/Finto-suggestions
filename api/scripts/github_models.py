### temp models

class GithubBodyModel(object):
  def __init__(self):
    self.type = ''
    self.preferred_labels = {}
    self.alternative_labels = ''
    self.related = []
    self.description = ''
    self.reason = ''
    self.scopeNote = ''
    self.groups = []
    self.organization = ''
    self.yse_term = {}

class GithubMeetingModel(object):
  def __init__(self, name, created_date):
    self.name = name
    self.created_date = created_date

class GithubIssueModel(object):
  def __init__(self, name, status, meeting, created, modified, closed, body):
    self.name = name
    self.status = status
    self.meeting = meeting
    self.created = created
    self.modified = modified
    self.closed = closed
    self.body = body
    self.tags = []