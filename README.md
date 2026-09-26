# Cobric's Kodi repository

Kodi add-on repository (`repository.cobric`) hosted on GitHub Pages at https://gorpet.github.io.

## Installing in Kodi

1. **Settings → File manager → Add source**, enter `https://gorpet.github.io` and name it e.g. `cobric`.
2. **Settings → Add-ons → Install from zip file**, choose the `cobric` source and select `repository.cobric-x.y.z.zip`.
3. **Install from repository → Cobric's Kodi repository** and pick the add-ons you want.

## Add-ons

| Add-on | Description |
|---|---|
| [`service.subtitles.titlovi-cobric`](https://github.com/gorpet/service.subtitles.titlovi-cobric) | Subtitles from Titlovi.com |
| [`service.subtitles.prijevodi-online-org`](https://github.com/gorpet/service.subtitles.prijevodi-online-org) | Subtitles from Prijevodi-online.org (requires an account) |
| [`service.subtitles.bazarr`](https://github.com/gorpet/service.subtitles.bazarr) | Subtitles via your own Bazarr server |
| [`skin.fentastic`](https://github.com/Zaxxon709/fentasticplus) | FENtastic Plus skin (third-party, by Zaxxon709) |
| [`script.fentastic.helper`](https://github.com/Zaxxon709/fentasticplus) | Helper for the FENtastic Plus skin (third-party, by Zaxxon709) |
| [`repository.addonniss`](https://github.com/Addonniss/repository.addonniss) | Addonniss Repository (third-party) – install it, then get Translatarr, Skip.Intro.Next and KodiARR Instant from it |

## Layout

- `repo/repository.cobric/` – the repository add-on itself
- `repo/service.subtitles.*` – add-on sources, as git submodules
- `vendor/` – third-party repos with prebuilt add-on zips, as git submodules (`fentasticplus`, `repository.addonniss`; the zip folders to publish are listed in `PREBUILT` in `_repo_generator.py`)
- `repo/zips/` – generated output that Kodi reads (`addons.xml`, `addons.xml.md5`, per-add-on zips)
- `repository.cobric-x.y.z.zip` + `index.html` – the installable repository zip linked from the Pages site

## Releasing an add-on update

1. Push the change to the add-on's own repo, with a bumped `version="..."` in its `addon.xml` (the generator skips versions it has already built).
2. Either bump the submodule here (`git submodule update --remote && git commit -am "..." && git push`), or run the **Build repository** workflow from the Actions tab, which pulls every submodule to its latest commit.

The [Build repository](.github/workflows/build.yml) workflow runs on every push to `master`. It runs `_repo_generator.py`, keeps the root `repository.cobric-x.y.z.zip` and `index.html` in sync with the repository add-on's version, and commits the output back. It fails if the generator reports an error, and warns when an add-on's sources changed without a version bump.

To build locally instead: `python3 _repo_generator.py`.

## Third-party add-ons

Add-ons from `vendor/` are published from their upstream release zips as-is: the generator copies the newest zip of each add-on id (searching subfolders) into `repo/zips/` and adds it to `addons.xml`. The workflow runs daily and pulls the `vendor/` submodules to their latest commit, so new upstream releases are published automatically. To add another, `git submodule add <url> vendor/<name>` and list the folder in `PREBUILT`.

Based on [drinfernoo/repository.example](https://github.com/drinfernoo/repository.example).
