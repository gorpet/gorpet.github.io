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

```sh
git submodule update --remote          # pull latest add-on sources
# bump version="..." in the add-on's addon.xml (the generator skips unchanged versions)
python3 _repo_generator.py              # builds zips, updates addons.xml + md5
git add -A && git commit && git push
```

When the repository add-on itself changes, bump its version in `repo/repository.cobric/addon.xml`, then copy the new zip from `repo/zips/repository.cobric/` to the root and update the link in `index.html`.

Based on [drinfernoo/repository.example](https://github.com/drinfernoo/repository.example).
