# Frozen MRC project snapshot

These files are a frozen snapshot of the production templates at
`892c4b72ee4eb3537310b0694d5fb73cb6a18d53`, which was master HEAD when the
fixture was created:
`kivy_ios/tools/templates/{{ cookiecutter.project_name }}-ios/`.
At that revision, the templates use manual memory management (MRC); the
[proposed ARC/PyConfig migration](https://github.com/kivy/kivy-ios/pull/1009)
has not landed. This snapshot guards saved projects across that upcoming
migration and future template changes. Tests must not regenerate it from
the current templates.

The updater at the pinned revision does not change ARC/modules settings.
The compiler-setting tests establish that preservation contract for future
updater changes; they do not demonstrate a regression in current master.
The `legacy` name identifies the saved-project fixture, not an older upstream
template revision.

The one-time rendering substitutions were:

- `cookiecutter.project_name`: `legacy`
- `cookiecutter.project_dir`: `/ci/legacy-app`
- `cookiecutter.dist_dir`: `/ci/legacy-dist` (including the template's
  nonbreaking-space variant in the hostpython compile command)

The only project customization is the additional `custom_helper` native target,
with independent Debug/Release configurations and fixed `C100...` object IDs.
The original app target, configuration lists, build phases, references and
settings are retained. `main.m` and `bridge.m` retain the snapshot's manual
memory management, including the autorelease pool and explicit releases,
and are byte-identical to the pinned sources after the substitutions above.
Whitespace-only lines are retained intentionally to preserve that provenance.

This is a parser/updater fixture, not a complete native-build fixture: resources,
headers, application code and distribution artifacts are intentionally absent.
The helper target need not build. Tests supplying explicit ARC/modules `YES`
check only preservation and scalar serialization; they do not claim these MRC
sources compile with ARC enabled.
