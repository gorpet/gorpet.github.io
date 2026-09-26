""" 
    Put this script in the root folder of your repo and it will
    zip up all addon folders, create a new zip in your zips folder
    and then update the md5 and addons.xml file
"""

import hashlib
import os
import re
import shutil
import sys
import zipfile

from xml.etree import ElementTree

SCRIPT_VERSION = 5
KODI_VERSIONS = ["krypton", "leia", "matrix", "nexus", "repo"]
IGNORE = [
    ".git",
    ".github",
    ".gitignore",
    ".DS_Store",
    "thumbs.db",
    ".idea",
    "venv",
]
# Folders of prebuilt add-on zips (e.g. third-party submodules) to publish
# as-is, keyed by release. Subfolders are searched too, and the newest version
# of each add-on id is used.
PREBUILT = {
    "repo": [
        "vendor/fentasticplus",
        "vendor/repository.addonniss/zips/repository.addonniss",
    ],
}
_COLOR_ESCAPE = "\x1b[{}m"
_COLORS = {
    "black": "30",
    "red": "31",
    "green": "4;32",
    "yellow": "3;33",
    "blue": "34",
    "magenta": "35",
    "cyan": "1;36",
    "grey": "37",
    "endc": "0",
}


def _setup_colors():
    """
    Return True if the running system's terminal supports color,
    and False otherwise.
    """

    def vt_codes_enabled_in_windows_registry():
        """
        Check the Windows registry to see if VT code handling has been enabled by default.
        """
        try:
            import winreg
        except:
            return False
        else:
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Console", access=winreg.KEY_ALL_ACCESS
            )
            try:
                reg_key_value, _ = winreg.QueryValueEx(reg_key, "VirtualTerminalLevel")
            except FileNotFoundError:
                try:
                    winreg.SetValueEx(
                        reg_key, "VirtualTerminalLevel", 0, winreg.KEY_DWORD, 1
                    )
                except:
                    return False
                else:
                    reg_key_value, _ = winreg.QueryValueEx(
                        reg_key, "VirtualTerminalLevel"
                    )
            else:
                return reg_key_value == 1

    def is_a_tty():
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    def legacy_support():
        console = 0
        color = 0
        if sys.platform in ["linux", "linux2", "darwin"]:
            pass
        elif sys.platform == "win32":
            color = os.system("color")

            from ctypes import windll

            k = windll.kernel32
            console = k.SetConsoleMode(k.GetStdHandle(-11), 7)

        return any([color == 1, console == 1])

    return any(
        [
            is_a_tty(),
            sys.platform != "win32",
            "ANSICON" in os.environ,
            "WT_SESSION" in os.environ,
            os.environ.get("TERM_PROGRAM") == "vscode",
            vt_codes_enabled_in_windows_registry(),
            legacy_support(),
        ]
    )


_SUPPORTS_COLOR = _setup_colors()


def color_text(text, color):
    """
    Return an ANSI-colored string, if supported.
    """

    return (
        '{}{}{}'.format(
            _COLOR_ESCAPE.format(_COLORS[color]),
            text,
            _COLOR_ESCAPE.format(_COLORS["endc"]),
        )
        if _SUPPORTS_COLOR
        else text
    )


def version_key(version):
    """
    Sort key for add-on versions: digit runs compare numerically, so
    100.0.33 < 100.0.33a < 100.0.34.
    """
    return [
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in re.findall(r"\d+|\D+", version)
    ]


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


class Generator:
    """
    Generates a new addons.xml file from each addons addon.xml file
    and a new addons.xml.md5 hash file. Must be run from the root of
    the checked-out repo.
    """

    def __init__(self, release):
        self.release_path = release
        self.zips_path = os.path.join(self.release_path, "zips")
        addons_xml_path = os.path.join(self.zips_path, "addons.xml")
        md5_path = os.path.join(self.zips_path, "addons.xml.md5")

        if not os.path.exists(self.zips_path):
            os.makedirs(self.zips_path)

        self._remove_binaries()

        if self._generate_addons_file(addons_xml_path):
            print(
                "Successfully updated {}".format(color_text(addons_xml_path, 'yellow'))
            )

            if self._generate_md5_file(addons_xml_path, md5_path):
                print("Successfully updated {}".format(color_text(md5_path, 'yellow')))

    def _remove_binaries(self):
        """
        Removes any and all compiled Python files before operations.
        """

        for parent, dirnames, filenames in os.walk(self.release_path):
            for fn in filenames:
                if fn.lower().endswith("pyo") or fn.lower().endswith("pyc"):
                    compiled = os.path.join(parent, fn)
                    try:
                        os.remove(compiled)
                        print(
                            "Removed compiled python file: {}".format(
                                color_text(compiled, 'green')
                            )
                        )
                    except:
                        print(
                            "Failed to remove compiled python file: {}".format(
                                color_text(compiled, 'red')
                            )
                        )
            for dir in dirnames:
                if "pycache" in dir.lower():
                    compiled = os.path.join(parent, dir)
                    try:
                        shutil.rmtree(compiled)
                        print(
                            "Removed __pycache__ cache folder: {}".format(
                                color_text(compiled, 'green')
                            )
                        )
                    except:
                        print(
                            "Failed to remove __pycache__ cache folder:  {}".format(
                                color_text(compiled, 'red')
                            )
                        )

    def _create_zip(self, folder, addon_id, version):
        """
        Creates a zip file in the zips directory for the given addon.
        """
        addon_folder = os.path.join(self.release_path, folder)
        zip_folder = os.path.join(self.zips_path, addon_id)
        if not os.path.exists(zip_folder):
            os.makedirs(zip_folder)

        final_zip = os.path.join(zip_folder, "{0}-{1}.zip".format(addon_id, version))
        if not os.path.exists(final_zip):
            zip = zipfile.ZipFile(final_zip, "w", compression=zipfile.ZIP_DEFLATED)
            root_len = len(os.path.dirname(os.path.abspath(addon_folder)))

            for root, dirs, files in os.walk(addon_folder):
                # remove any unneeded artifacts
                for i in IGNORE:
                    if i in dirs:
                        try:
                            dirs.remove(i)
                        except:
                            pass
                    for f in files:
                        if f.startswith(i):
                            try:
                                files.remove(f)
                            except:
                                pass

                archive_root = os.path.abspath(root)[root_len:]

                for f in files:
                    fullpath = os.path.join(root, f)
                    archive_name = os.path.join(archive_root, f)
                    zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)

            zip.close()
            size = convert_bytes(os.path.getsize(final_zip))
            print(
                "Zip created for {} ({}) - {}".format(
                    color_text(addon_id, 'cyan'),
                    color_text(version, 'green'),
                    color_text(size, 'yellow'),
                )
            )

    def _copy_meta_files(self, addon_id, addon_folder):
        """
        Copy the addon.xml and relevant art files into the relevant folders in the repository.
        """

        tree = ElementTree.parse(os.path.join(self.release_path, addon_id, "addon.xml"))
        root = tree.getroot()

        copyfiles = ["addon.xml"]
        for ext in root.findall("extension"):
            if ext.get("point") in ["xbmc.addon.metadata", "kodi.addon.metadata"]:
                assets = ext.find("assets")
                if not assets:
                    continue
                for art in [a for a in assets if a.text]:
                    copyfiles.append(os.path.normpath(art.text))

        src_folder = os.path.join(self.release_path, addon_id)
        for file in copyfiles:
            addon_path = os.path.join(src_folder, file)
            if not os.path.exists(addon_path):
                continue

            zips_path = os.path.join(addon_folder, file)
            asset_path = os.path.split(zips_path)[0]
            if not os.path.exists(asset_path):
                os.makedirs(asset_path)

            shutil.copy(addon_path, zips_path)

    def _generate_addons_file(self, addons_xml_path):
        """
        Generates a zip for each found addon, and updates the addons.xml file accordingly.
        """
        if not os.path.exists(addons_xml_path):
            addons_root = ElementTree.Element('addons')
            addons_xml = ElementTree.ElementTree(addons_root)
        else:
            addons_xml = ElementTree.parse(addons_xml_path)
            addons_root = addons_xml.getroot()

        folders = [
            i
            for i in os.listdir(self.release_path)
            if os.path.isdir(os.path.join(self.release_path, i))
            and i != "zips"
            and not i.startswith(".")
            and os.path.exists(os.path.join(self.release_path, i, "addon.xml"))
        ]

        changed = self._import_prebuilt(addons_root)
        for addon in folders:
            try:
                addon_xml_path = os.path.join(self.release_path, addon, "addon.xml")
                addon_xml = ElementTree.parse(addon_xml_path)
                addon_root = addon_xml.getroot()
                id = addon_root.get('id')
                version = addon_root.get('version')

                if self._update_entry(addons_root, addon_root):
                    changed = True
                    # Create the zip files
                    self._create_zip(addon, id, version)
                    self._copy_meta_files(addon, os.path.join(self.zips_path, id))
            except Exception as e:
                print(
                    "Excluding {}: {}".format(
                        color_text(addon, 'yellow'), color_text(e, 'red')
                    )
                )

        if changed:
            addons_root[:] = sorted(addons_root, key=lambda addon: addon.get('id'))
            try:
                addons_xml.write(
                    addons_xml_path, encoding="utf-8", xml_declaration=True
                )

                return changed
            except Exception as e:
                print(
                    "An error occurred updating {}!\n{}".format(
                        color_text(addons_xml_path, 'yellow'), color_text(e, 'red')
                    )
                )

    def _update_entry(self, addons_root, addon_root):
        """
        Adds or replaces the addons.xml entry for an add-on. Returns True if
        the entry was missing or had a different version.
        """
        addon_entry = addons_root.find("addon[@id='{}']".format(addon_root.get('id')))
        if addon_entry is None:
            addons_root.append(addon_root)
            return True
        if addon_entry.get('version') != addon_root.get('version'):
            index = addons_root.findall('addon').index(addon_entry)
            addons_root.remove(addon_entry)
            addons_root.insert(index, addon_root)
            return True
        return False

    def _import_prebuilt(self, addons_root):
        """
        Publishes the newest zip of each add-on found in this release's
        PREBUILT folders, copying the zip unchanged along with its addon.xml
        and art files.
        """
        newest = {}
        for folder in PREBUILT.get(os.path.basename(os.path.normpath(self.release_path)), []):
            if not os.path.isdir(folder):
                print("Excluding {}: {}".format(
                    color_text(folder, 'yellow'), color_text("folder not found", 'red')))
                continue
            paths = []
            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                paths.extend(os.path.join(root, f) for f in files if f.endswith(".zip"))
            for path in sorted(paths):
                try:
                    with zipfile.ZipFile(path) as zf:
                        xml_name = next(n for n in zf.namelist()
                                        if n.count("/") == 1 and n.endswith("/addon.xml"))
                        addon_root = ElementTree.fromstring(zf.read(xml_name))
                    id = addon_root.get('id')
                    version = addon_root.get('version')
                    if xml_name.split("/")[0] != id:
                        raise ValueError("zip folder does not match add-on id {}".format(id))
                    if id not in newest or version_key(version) > version_key(newest[id][1].get('version')):
                        newest[id] = (path, addon_root)
                except Exception as e:
                    print("Excluding {}: {}".format(color_text(path, 'yellow'), color_text(e, 'red')))

        changed = False
        for id, (path, addon_root) in sorted(newest.items()):
            version = addon_root.get('version')
            zip_folder = os.path.join(self.zips_path, id)
            final_zip = os.path.join(zip_folder, "{0}-{1}.zip".format(id, version))
            if not self._update_entry(addons_root, addon_root) and os.path.exists(final_zip):
                continue
            changed = True
            if not os.path.exists(zip_folder):
                os.makedirs(zip_folder)
            shutil.copy(path, final_zip)
            self._copy_prebuilt_meta_files(final_zip, addon_root, zip_folder)
            print(
                "Zip imported for {} ({}) - {}".format(
                    color_text(id, 'cyan'),
                    color_text(version, 'green'),
                    color_text(convert_bytes(os.path.getsize(final_zip)), 'yellow'),
                )
            )
        return changed

    def _copy_prebuilt_meta_files(self, zip_path, addon_root, addon_folder):
        """
        Extracts the addon.xml and art files of a prebuilt zip into the
        add-on's folder in the repository.
        """
        # Without an <assets> element Kodi falls back to icon.png and fanart.jpg
        copyfiles = ["addon.xml", "icon.png", "fanart.jpg"]
        for ext in addon_root.findall("extension"):
            if ext.get("point") in ["xbmc.addon.metadata", "kodi.addon.metadata"]:
                assets = ext.find("assets")
                if assets is None:
                    continue
                copyfiles.extend(a.text.strip() for a in assets if a.text and a.text.strip())

        id = addon_root.get('id')
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            for file in copyfiles:
                member = "{}/{}".format(id, file.replace(os.sep, "/"))
                if member not in names:
                    continue
                target = os.path.join(addon_folder, os.path.normpath(file))
                if not os.path.abspath(target).startswith(os.path.abspath(addon_folder) + os.sep):
                    continue
                if not os.path.exists(os.path.dirname(target)):
                    os.makedirs(os.path.dirname(target))
                with open(target, "wb") as f:
                    f.write(zf.read(member))

    def _generate_md5_file(self, addons_xml_path, md5_path):
        """
        Generates a new addons.xml.md5 file.
        """
        try:
            with open(addons_xml_path, "r", encoding="utf-8") as f:
                m = hashlib.md5(f.read().encode("utf-8")).hexdigest()
                self._save_file(m, file=md5_path)

            return True
        except Exception as e:
            print(
                "An error occurred updating {}!\n{}".format(
                    color_text(md5_path, 'yellow'), color_text(e, 'red')
                )
            )

    def _save_file(self, data, file):
        """
        Saves a file.
        """
        try:
            with open(file, "w") as f:
                f.write(data)
        except Exception as e:
            print(
                "An error occurred saving {}!\n{}".format(
                    color_text(file, 'yellow'), color_text(e, 'red')
                )
            )


if __name__ == "__main__":
    for release in [r for r in KODI_VERSIONS if os.path.exists(r)]:
        Generator(release)
