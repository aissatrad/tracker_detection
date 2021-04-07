class TrackerDetail:
    id = ""
    name = ""
    description = ""
    creation_date = ""
    code_signature = ""
    network_signature = ""
    website = ""
    categories = []

    def __init__(self, id,name,description,creation_date,code_signature,network_signature,website,categories):
        self.id = id
        self.name = name
        self.description = description
        self.creation_date = creation_date
        self.code_signature = code_signature
        self.network_signature = network_signature
        self.website = website
        self.categories = categories