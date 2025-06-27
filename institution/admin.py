from django.contrib import admin
from .models import *


@admin.register(InstitutionInfo)
class InstitutionInfoAdmin(admin.ModelAdmin):
    list_display = ("name", "short_code", "institution_type", "is_active", "admin")
    search_fields = ("name", "short_code", "institution_type")


@admin.register(GlobalCurriculumTrack)
class GlobalCurriculumTrackAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_type")
    search_fields = ("name", "institution_type")


@admin.register(GlobalStream)
class GlobalStreamAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_type")
    search_fields = ("name", "institution_type")


@admin.register(GlobalSubject)
class GlobalSubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "institution_type")
    search_fields = ("name", "code", "institution_type")


@admin.register(GlobalModule)
class GlobalModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "institution_type")
    search_fields = ("title", "institution_type")


@admin.register(GlobalUnit)
class GlobalUnitAdmin(admin.ModelAdmin):
    list_display = ("title", "institution_type")
    search_fields = ("title", "institution_type")


@admin.register(GlobalLesson)
class GlobalLessonAdmin(admin.ModelAdmin):
    list_display = ("title", "institution_type")
    search_fields = ("title", "institution_type")


@admin.register(GlobalMicroLesson)
class GlobalMicroLessonAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "institution_type")
    search_fields = ("title", "institution_type")
    list_filter = ("content_type", "institution_type")


@admin.register(CurriculumTrack)
class CurriculumTrackAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_info")
    search_fields = ("name__name",)
    list_filter = ("institution_info",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "curriculum_track")
    search_fields = ("name",)
    list_filter = ("curriculum_track",)


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "curriculum_track")
    search_fields = ("name__name",)
    list_filter = ("curriculum_track", "section")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "stream")
    search_fields = ("name__name",)
    list_filter = ("stream",)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "subject")
    search_fields = ("title__title",)
    list_filter = ("subject",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "module")
    search_fields = ("title__title",)
    list_filter = ("module",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "unit")
    search_fields = ("title__title",)
    list_filter = ("unit",)


@admin.register(MicroLesson)
class MicroLessonAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "order")
    search_fields = ("title__title",)
    list_filter = ("lesson",)


@admin.register(TeacherEnrollment)
class TeacherEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "institution", "is_active")
    search_fields = ("user__email", "user__phone_number")
    list_filter = ("institution", "is_active")
    filter_horizontal = ("curriculum_track", "section", "subjects")


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "curriculum_track", "section", "institution", "is_active")
    search_fields = (
        "user__email",
        "user__phone_number",
        "curriculum_track__name__name",
    )
    list_filter = ("institution", "section", "is_active")


@admin.register(InstitutionFee)
class InstitutionFeeAdmin(admin.ModelAdmin):
    list_display = (
        "institution",
        "default_fee",
    )
    search_fields = ("institution__name", "default_fee")
    list_filter = ("institution", "default_fee")
    
@admin.register(CurriculumTrackFee)
class CurriculumTrackFeeAdmin(admin.ModelAdmin):
    list_display = ("curriculum_track", "fee")
    search_fields = ("curriculum_track__name__name", "fee")
    list_filter = ("curriculum_track", "fee")

@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display = (
        "student_enrollment",
        "fee",
    )
    search_fields = (
        "student_enrollment__user__email",
        "student_enrollment__user__phone_number",
    )
    list_filter = ["fee"]
    readonly_fields = ("id", "created_at", "updated_at")
