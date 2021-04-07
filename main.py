import hashlib
import zipfile
from os.path import isdir
from tracker import Trackers
import apkutils
from apk_info import app_category

# Tracker Types & scores map (Example)
tracker_types = {
    # "Tracker Type Name" : "Example Privacy score"
    # "We add "Unknown" because some tracker in exodus DB they haven't a type
    "Unknown": 5,
    # 6 Types by exodus tracker database
    "Crash reporting": 1,
    "Analytics": 10,
    "Profiling": 10,
    "Identification": 10,
    "Advertisement": 10,
    "Location": 10}


def get_md5(data):
    return hashlib.md5(data).hexdigest()


def unzip(app_path):
    files = []
    with open('app.apk', 'rb') as f:
        name = f"unzipped/{get_md5(f.read())}"
    if not isdir(name):
        print(f"Unzip {app_path} ...")
        with zipfile.ZipFile(app_path, 'r') as zipptr:
            for file_info in zipptr.infolist():
                filename = file_info.filename
                if not isinstance(filename, str):
                    filename = str(filename, encoding='utf-8', errors='replace')
                files.append(filename)

                zipptr.extract(filename, name)
        print(f"{app_path} unzipped in {name}")
        return name
    else:
        print("Using existing zipped")
        return name


def detect_trackers(apk):
    app_dir = unzip(apk)
    tr = Trackers(app_dir, "tools")
    print("Number of known trackers", tr.nb_trackers_signature)
    print("Getting trackers")
    trackers = tr.get_trackers()
    trackers_num = len(trackers)
    print(f"We found {trackers_num} trackers:")
    score = 0
    for tracker in trackers:
        if len(tracker.categories) == 0:
            score += tracker_types["Unknown"]
        for cat in tracker.categories:
            score += tracker_types[cat]
        print(tracker.name, tracker.categories)
    print("Trackers score", round(score / trackers_num, 2))


apk_path = "app.apk"
apk = apkutils.APK(apk_path)
print("APK CATEGORY:", app_category(apk.get_manifest()["@package"]))
detect_trackers(apk_path)


