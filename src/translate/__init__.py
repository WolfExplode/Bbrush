import bpy

from . import zh_CN

# If RNA lookup fails, register() still needs identifiers that may appear in builds
# we target (zh_CN vs zh_HANS split).
_FALLBACK_LANGUAGES = (
    "DEFAULT",
    "en_US",
    "zh_CN",
    "zh_HANS",
    "zh_TW",
)


def get_language_list() -> list[str]:
    """Return UI language identifiers for this Blender build.

    Uses the same source as the invalid-assignment hack did: the enum of allowed
    values for preferences view language — but via RNA ``enum_items``, so there is
    no dependence on TypeError message wording and no silent ``None`` on success.
    """
    try:
        prop = bpy.types.PreferencesView.bl_rna.properties.get("language")
        if prop is not None and getattr(prop, "type", None) == "ENUM":
            items = prop.enum_items
            if items:
                return [item.identifier for item in items]
    except Exception:
        pass
    return list(_FALLBACK_LANGUAGES)


class TranslationHelper:
    def __init__(self, name: str, data: dict, lang='zh_CN'):
        self.name = name
        self.translations_dict = dict()

        for src, src_trans in data.items():
            key = ("Operator", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans
            key = ("*", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans

    def register(self):
        bpy.app.translations.register(self.name, self.translations_dict)

    def unregister(self):
        bpy.app.translations.unregister(self.name)


translate = None


def register():
    global translate

    language = "zh_CN"
    all_language = get_language_list()
    if language not in all_language:
        if language == "zh_CN":
            language = "zh_HANS"
        elif language == "zh_HANS":
            language = "zh_CN"
    translate = TranslationHelper(f"BBrush_{language}", zh_CN.data, lang=language)
    translate.register()


def unregister():
    global translate
    translate.unregister()
    translate = None
