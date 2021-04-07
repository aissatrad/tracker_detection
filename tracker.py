import glob
import io
import itertools
import json
import os
import platform
import re
import shutil
import subprocess
from collections import namedtuple

from settings import JAVA_DIRECTORY, BACKSMALI_BINARY
from trackerdetail import TrackerDetail


def is_file_exists(file_path):
    if os.path.isfile(file_path):
        return True
    # This fix situation where a user just typed "adb" or another executable
    # inside settings.py
    if shutil.which(file_path):
        return True
    else:
        return False


def is_dir_exists(dir_path):
    if os.path.isdir(dir_path):
        return True
    else:
        return False


def find_java_binary():
    """Find Java."""
    # Respect user settings
    if platform.system() == 'Windows':
        jbin = 'java.exe'
    else:
        jbin = 'java'
    if is_dir_exists(JAVA_DIRECTORY):
        if JAVA_DIRECTORY.endswith('/'):
            return JAVA_DIRECTORY + jbin
        elif JAVA_DIRECTORY.endswith('\\'):
            return JAVA_DIRECTORY + jbin
        else:
            return JAVA_DIRECTORY + '/' + jbin
    if os.getenv('JAVA_HOME'):
        java = os.path.join(
            os.getenv('JAVA_HOME'),
            'bin',
            jbin)
        if is_file_exists(java):
            return java
    return 'java'


class Trackers:
    def __init__(self, apk_dir, tools_dir):
        self.apk = None
        self.apk_dir = apk_dir
        self.tracker_db = "ex_trackers.json"
        self.signatures = None
        with open(self.tracker_db, 'r') as f:
            self.nb_trackers_signature = len(json.load(f)['trackers'].keys())
        self.compiled_tracker_signature = None
        self.classes = None
        self.tools_dir = tools_dir

    def _compile_signatures(self):
        self.compiled_tracker_signature = []
        try:
            self.compiled_tracker_signature = [re.compile(track.code_signature)
                                               for track in self.signatures]
        except TypeError:
            print('compiling tracker signature failed')

    def load_trackers_signatures(self):

        self.signatures = []
        with io.open(self.tracker_db,
                     mode='r',
                     encoding='utf8',
                     errors='ignore') as flip:
            data = json.loads(flip.read())
        for elm in data['trackers']:
            self.signatures.append(
                namedtuple('tracker',
                           data['trackers'][elm].keys())(
                    *data['trackers'][elm].values()))
        self._compile_signatures()
        self.nb_trackers_signature = len(self.signatures)

    def get_embedded_classes(self):
        if self.classes is not None:
            return self.classes
        for dex_file in glob.iglob(os.path.join(self.apk_dir, '*.dex')):
            if (len(BACKSMALI_BINARY) > 0
                    and is_file_exists(BACKSMALI_BINARY)):
                bs_path = BACKSMALI_BINARY
            else:
                bs_path = os.path.join(self.tools_dir, 'baksmali-2.4.0.jar')
            args = [find_java_binary(), '-jar',
                    bs_path, 'list', 'classes', dex_file]
            classes = subprocess.check_output(
                args, universal_newlines=True).splitlines()
            if self.classes is not None:
                self.classes = self.classes + classes
            else:
                self.classes = classes
        return self.classes

    def detect_trackers_in_list(self, class_list):
        if self.signatures is None:
            self.load_trackers_signatures()

        def _detect_tracker(sig, tracker, class_list):
            for clazz in class_list:
                if sig.search(clazz):
                    return tracker
            return None

        results = []
        args = [(self.compiled_tracker_signature[index], tracker, class_list)
                for (index, tracker) in enumerate(self.signatures) if
                len(tracker.code_signature) > 3]

        for res in itertools.starmap(_detect_tracker, args):
            if res:
                results.append(res)

        trackers = [t for t in results if t is not None]
        trackers = sorted(trackers, key=lambda trackers: trackers.name)
        return trackers

    def detect_trackers(self) -> list:
        if self.signatures is None:
            self.load_trackers_signatures()
        eclasses = self.get_embedded_classes()
        if eclasses:
            return self.detect_trackers_in_list(eclasses)
        return []

    def get_trackers(self):
        trackers = self.detect_trackers()
        return [TrackerDetail(*trk) for trk in trackers]
