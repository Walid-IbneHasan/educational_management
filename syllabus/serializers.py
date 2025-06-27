from institution.models import CurriculumTrack, InstitutionInfo, Lesson, MicroLesson, Module, Section, Subject, Unit
from rest_framework import serializers
from .models import Syllabus
from institution.serializers import (
    CurriculumTrackSerializer,
    SectionSerializer,
    SubjectSerializer,
    ModuleSerializer,
    UnitSerializer,
    LessonSerializer,
    MicroLessonSerializer,
)
from user_management.serializers.authentication import UserSerializer


class SyllabusSerializer(serializers.ModelSerializer):
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=CurriculumTrack.objects.all()
    )
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    modules = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all(), many=True, required=False
    )
    units = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), many=True, required=False
    )
    lessons = serializers.PrimaryKeyRelatedField(
        queryset=Lesson.objects.all(), many=True, required=False
    )
    micro_lessons = serializers.PrimaryKeyRelatedField(
        queryset=MicroLesson.objects.all(), many=True, required=False
    )
    created_by = UserSerializer(read_only=True)
    curriculum_track_detail = CurriculumTrackSerializer(
        source="curriculum_track", read_only=True
    )
    section_detail = SectionSerializer(source="section", read_only=True)
    subject_detail = SubjectSerializer(source="subject", read_only=True)
    modules_detail = ModuleSerializer(source="modules", many=True, read_only=True)
    units_detail = UnitSerializer(source="units", many=True, read_only=True)
    lessons_detail = LessonSerializer(source="lessons", many=True, read_only=True)
    micro_lessons_detail = MicroLessonSerializer(
        source="micro_lessons", many=True, read_only=True
    )

    class Meta:
        model = Syllabus
        fields = [
            "id",
            "institution",
            "curriculum_track",
            "curriculum_track_detail",
            "section",
            "section_detail",
            "subject",
            "subject_detail",
            "title",
            "purpose",
            "modules",
            "modules_detail",
            "units",
            "units_detail",
            "lessons",
            "lessons_detail",
            "micro_lessons",
            "micro_lessons_detail",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "institution",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        request = self.context["request"]
        curriculum_track = data.get("curriculum_track")
        section = data.get("section")
        subject = data.get("subject")
        modules = data.get("modules", [])
        units = data.get("units", [])
        lessons = data.get("lessons", [])
        micro_lessons = data.get("micro_lessons", [])

        # Validate teacher enrollment
        if not request.user.is_teacher:
            raise serializers.ValidationError(
                {"non_field_errors": "Only teachers can create or update syllabi."}
            )

        # Fix: Use institution_curriculum_tracks instead of curriculum_tracks
        institution = InstitutionInfo.objects.filter(
            institution_curriculum_tracks=curriculum_track
        ).first()
        if not institution:
            raise serializers.ValidationError(
                {"curriculum_track": "Invalid curriculum track."}
            )

        # Validate section belongs to curriculum track
        if section.curriculum_track != curriculum_track:
            raise serializers.ValidationError(
                {
                    "section": "Section does not belong to the specified curriculum track."
                }
            )

        # Validate subject belongs to curriculum track
        if subject.stream.curriculum_track != curriculum_track:
            raise serializers.ValidationError(
                {
                    "subject": "Subject does not belong to the specified curriculum track."
                }
            )

        # Validate teacher is enrolled
        if not request.user.teacher_enrollments.filter(
            institution=institution,
            curriculum_track=curriculum_track,
            section=section,
            subjects=subject,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": "You are not enrolled to teach this subject in this section."
                }
            )

        # Validate modules
        for module in modules:
            if module.subject != subject:
                raise serializers.ValidationError(
                    {
                        "modules": f"Module {module} does not belong to the specified subject."
                    }
                )

        # Validate units
        for unit in units:
            if unit.module.subject != subject:
                raise serializers.ValidationError(
                    {"units": f"Unit {unit} does not belong to the specified subject."}
                )

        # Validate lessons
        for lesson in lessons:
            if lesson.unit.module.subject != subject:
                raise serializers.ValidationError(
                    {
                        "lessons": f"Lesson {lesson} does not belong to the specified subject."
                    }
                )

        # Validate micro lessons
        for micro_lesson in micro_lessons:
            if micro_lesson.lesson.unit.module.subject != subject:
                raise serializers.ValidationError(
                    {
                        "micro_lessons": f"Micro lesson {micro_lesson} does not belong to the specified subject."
                    }
                )

        return data

    def create(self, validated_data):
        modules = validated_data.pop("modules", [])
        units = validated_data.pop("units", [])
        lessons = validated_data.pop("lessons", [])
        micro_lessons = validated_data.pop("micro_lessons", [])
        curriculum_track = validated_data.get("curriculum_track")
        # Fix: Use institution_curriculum_tracks for consistency
        institution = InstitutionInfo.objects.filter(
            institution_curriculum_tracks=curriculum_track
        ).first()
        validated_data["institution"] = institution
        validated_data["created_by"] = self.context["request"].user
        syllabus = Syllabus.objects.create(**validated_data)
        syllabus.modules.set(modules)
        syllabus.units.set(units)
        syllabus.lessons.set(lessons)
        syllabus.micro_lessons.set(micro_lessons)
        return syllabus

    def update(self, instance, validated_data):
        modules = validated_data.pop("modules", None)
        units = validated_data.pop("units", None)
        lessons = validated_data.pop("lessons", None)
        micro_lessons = validated_data.pop("micro_lessons", None)
        instance = super().update(instance, validated_data)
        if modules is not None:
            instance.modules.set(modules)
        if units is not None:
            instance.units.set(units)
        if lessons is not None:
            instance.lessons.set(lessons)
        if micro_lessons is not None:
            instance.micro_lessons.set(micro_lessons)
        return instance
