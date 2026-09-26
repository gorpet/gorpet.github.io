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

## Layout

- `repo/repository.cobric/` – the repository add-on itself
- `repo/service.subtitles.*` – add-on sources, as git submodules
- `repo/zips/` – generated output that Kodi reads (`addons.xml`, `addons.xml.md5`, per-add-on zips)
- `repository.cobric-x.y.z.zip` + `index.html` – the installable repository zip linked from the Pages site

## Releasing an add-on update

1. Push the change to the add-on's own repo, with a bumped `version="..."` in its `addon.xml` (the generator skips versions it has already built).
2. Either bump the submodule here (`git submodule update --remote && git commit -am "..." && git push`), or run the **Build repository** workflow from the Actions tab, which pulls every submodule to its latest commit.

The [Build repository](.github/workflows/build.yml) workflow runs on every push to `master`. It runs `_repo_generator.py`, keeps the root `repository.cobric-x.y.z.zip` and `index.html` in sync with the repository add-on's version, and commits the output back. It fails if the generator reports an error, and warns when an add-on's sources changed without a version bump.

To build locally instead: `python3 _repo_generator.py`.

Based on [drinfernoo/repository.example](https://github.com/drinfernoo/repository.example).
