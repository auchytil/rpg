from rpg.command import Command


class Subpackage(dict):
    # list of tuple (src_file, tag, attr)
    # e.g. %config, %doc, %ghost, %dir
    files = []

    # list of generated translation files
    files_translations = []

    # names of 'single' keys
    _singles = ["Name",
                "Version",
                "Release",
                "Summary"
                "Group"
                "License"
                "URL"
                "BuildArch"
                "BuildRoot"]

    # names of scripts
    _scripts = ["prep",
                "build",
                "pre",
                "install",
                "check",
                "post",
                "preun",
                "postun",
                "pretrans",
                "posttrans",
                "clean",
                "changelog"]

    # lists that could be appended
    _appendants = ["Requires",
                   "BuildRequires",
                   "Provides"]

    def __init__(self):
        tags = {"Name": "", "Version": "", "Release": "", "Summary": "",
                "Group": "", "License": "", "URL": "", "Source": "",
                "Patch": "", "BuildArch": "", "BuildRoot": "",
                "Obsoletes": "", "Conflicts": "", "Vendor": "",
                "Packager": "",
                "description": "",
                "package": "",
                "BuildRequires": [], "Requires": [], "Provides": [],
                "prep": Command(),
                "build": Command(),
                "pre": Command(),
                "install": Command(),
                "check": Command(),
                "post": Command(),
                "preun": Command(),
                "postun": Command(),
                "pretrans": Command(),
                "posttrans": Command(),
                "clean": Command(),
                "changelog": Command()
                }
        dict.__init__(self, tags)

    def __getattr__(self, key):
        ''' Returns attribute of chosen key from dict '''
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        ''' Set's attribute to key in dict '''
        try:
            if key in self._singles:
                if not isinstance(value, str):
                    raise TypeError(value)

            if key not in self._scripts and isinstance(value, type(Command())):
                raise TypeError(value)

            if not isinstance(value, (list, str, type(Command()))):
                raise TypeError(value)

            self.__getattr__(key)  # raises AttributeError
            if key in self._scripts:
                if isinstance(value, type(Command())):
                    self.__setitem__(key, value)
                else:
                    self.__setitem__(key, Command(value))
            else:
                self.__setitem__(key, value)
        except KeyError:
            raise AttributeError(key)

    def _write_tags(self, out):
        patch_index = 1   # Used for patch numbering
        for tag in self.tag_keywords:
            if tag in self.tags.keys():
                tag_value = self.tags.get(tag)
                value_type = type(tag_value)
                if value_type is list:
                    if tag in self._single_value_tags:
                        return -1
                    for val in tag_value:

                        # Patches aren't usually contained in subpackages.
                        if type(self) is Spec and tag == "Patch":
                            print("{}: {}".format(tag + str(patch_index), val),
                                  file=out)
                            patch_index += 1
                        else:
                            print("{}: {}".format(tag, val), file=out)

                # If the object is of class Subpackage, its header needs to be
                # handled separately.
                elif type(self) is Subpackage and tag == "Name":
                    print("\n%package {}".format(tag_value), file=out)

                else:    # Item is a single value
                    print("{}: {}".format(tag, tag_value), file=out)

    def _write_scripts(self, out):
        for script in self.script_keywords:
            if script in self.scripts.keys():
                print("\n{}\n{}".format(script + " " + self.tags['Name'],
                                        self.scripts.get(script)), file=out)

    def _write_files(self, out):
        if not self.files:
            return

        self.files = self._files_remove_duplicity()

        files_suffixes = ""
        for sfx in self.files_translations:
            files_suffixes += "-f " + sfx + " "

        print("\n%files {name} {suffixes}".format(name=self.tags.get("Name"),
                                                  suffixes=files_suffixes),
              file=out)

        for file in self.files:
            if file[2] is not None:  # file does have explicit attributes
                print("%attr" + str(file[2]), file=out, end=" ")
            if file[1] is not [] and file[1] is not None:
                for tag in file[1]:
                    print(tag, file=out, end=" ")
            print(file[0], file=out)

    def write(self, out):
        """Default write method used for packages. Packages usually do not use
        all the tags nor scripts available, e.g. patches, thus these are
        omitted from the writing process."""

        self._write_tags(out)
        self._write_scripts(out)

    def mark_doc(self, file):
        """Helper function for GUI to mark additional files as documentation.
        Function adds '%doc' attribute to a specific file or creates a new
        entry in the set of files."""

        for f in self.files:
            if f[0] == file:
                f[1].append("%doc")
                break
        else:
            self.files.append((file, ["%doc"], None))


class Spec(Subpackage):
    """SPEC properties holder"""
    subpackages = []
    changelogs = []

    def __init__(self):
        super(Spec, self).__init__()

    def __str__(self):
        out = ''
        for key, value in self.items():
            str_key = str(key)
            block = ''
            if isinstance(value, (list, Command)) and str(value) is not "":
                if str_key in self._scripts:
                    block = '\n' + str_key + '\n' + str(value) + '\n'
                elif str_key in self._appendants:
                    for part in value:
                        block += str_key + ':' + '\t' + part + '\n'
            elif isinstance(value, (str, Command)) and str(value) is not "":
                block = '\n' + str_key + '\n' + str(value) + '\n'
            if value is not Command('') and value is not "":
                out += block
        return out.strip()

    def _write_tags(self, out):
        return super(Spec, self)._write_tags(out)

    def _write_scripts(self, out):
        for script in self.script_keywords:
            if script == "%package":
                for package in self.subpackages:
                    package.write(out)

            if script in self.scripts.keys():
                print("\n{}\n{}".format(script, self.scripts.get(script)),
                      file=out)

    def _write_changelog(self, out):
        print("\n%changelog", file=out)
        for changelog in self.changelogs:
            print("{}\n".format(changelog), file=out)

    def _write_files(self, out):
        if not self.files:
            return

        self.files = self._files_remove_duplicity()

        files_suffixes = ""
        for sfx in self.files_translations:
            files_suffixes += "-f " + sfx + " "

        print("\n%files {suffixes}".format(suffixes=files_suffixes),
              file=out)

        for file in self.files:
            if file[2] is not None:  # file does have explicit attributes
                print("%attr" + str(file[2]), file=out, end=" ")
            if file[1] is not [] and file[1] is not None:
                for tag in file[1]:
                    print(tag, file=out, end=" ")
            print(file[0], file=out)

    def load(source_file):
        pass

    def write(self, out):
        """Modified inherited write method. See Subpackage.write() for more
        information."""

        # first tags need to written
        self._write_tags(out)

        # second packages and scripts need to be written
        self._write_scripts(out)

        # next all the files and appropriate attributes need to written
        self._write_files(out)

        # Print all files related to subpackages
        for subpkg in self.subpackages:
            subpkg._write_files(out)

        # Changelog is the last to be written at the end of file
        self._write_changelog(out)

    class Changelog:
        _weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        _months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                   "Sep", "Oct", "Nov", "Dec"]

        def __init__(self, date, author, email, *message):
            self.date = date
            self.author = author
            self.email = email
            self.message = message

        def __str__(self):
            msg = ""
            if type(self.message) is tuple:
                for m in self.message:
                    msg += "- " + m + "\n"
            else:
                msg = "- " + str(self.message) + "\n"

            return "* {} {} {} {} <{}>\n{}".format(
                self._weekdays[self.date.weekday()],
                self._months[self.date.month],
                self.date.year,
                self.author,
                self.email,
                msg)
