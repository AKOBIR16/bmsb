from modeltranslation.translator import translator, TranslationOptions

from .models import PortalFAQ, PortalSettings, RatingPeriod


class PortalSettingsTranslationOptions(TranslationOptions):
    fields = ('address',)
    required_languages = ('uz',)


class PortalFAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')
    required_languages = ('uz',)


class RatingPeriodTranslationOptions(TranslationOptions):
    fields = ('title',)


translator.register(PortalSettings, PortalSettingsTranslationOptions)
translator.register(PortalFAQ, PortalFAQTranslationOptions)
translator.register(RatingPeriod, RatingPeriodTranslationOptions)
