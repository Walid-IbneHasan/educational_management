from rest_framework import serializers
from user_management.models.authentication import InstitutionMembership
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()


class GlobalCurriculumTrackSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = GlobalCurriculumTrack
        fields = [
            "id",
            "name",
            "description",
            "institution_type",
            "institution_type_display",
            "is_active",
        ]


class GlobalStreamSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = GlobalStream
        fields = [
            "id",
            "name",
            "description",
            "institution_type",
            "institution_type_display",
            "is_active",
        ]


class GlobalSubjectSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = GlobalSubject
        fields = [
            "id",
            "name",
            "code",
            "description",
            "institution_type",
            "institution_type_display",
            "is_active",
        ]


class GlobalModuleSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = GlobalModule
        fields = [
            "id",
            "title",
            "description",
            "institution_type",
            "institution_type_display",
            "is_active",
        ]


class GlobalUnitSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = GlobalUnit
        fields = [
            "id",
            "title",
            "description",
            "institution_type",
            "institution_type_display",
            "is_active",
        ]


class GlobalLessonSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = GlobalLesson
        fields = [
            "id",
            "title",
            "institution_type",
            "institution_type_display",
            "is_active",
        ]


class GlobalMicroLessonSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = GlobalMicroLesson
        fields = [
            "id",
            "title",
            "content_type",
            "institution_type",
            "institution_type_display",
            "is_active",
        ]


class InstitutionInfoSerializer(serializers.ModelSerializer):
    institution_type_display = serializers.CharField(
        source="get_institution_type_display", read_only=True
    )

    class Meta:
        model = InstitutionInfo
        fields = [
            "id",
            "name",
            "description",
            "short_code",
            "address",
            "institution_type",
            "institution_type_display",
            "is_active",
            "admin",
        ]


class CurriculumTrackSerializer(serializers.ModelSerializer):
    institution_info = serializers.PrimaryKeyRelatedField(
        queryset=InstitutionInfo.objects.all(), required=False
    )
    name = serializers.PrimaryKeyRelatedField(
        queryset=GlobalCurriculumTrack.objects.all()
    )
    name_detail = serializers.SlugRelatedField(
        source="name", slug_field="name", read_only=True
    )

    class Meta:
        model = CurriculumTrack
        fields = ["id", "institution_info", "name", "name_detail", "is_active", "order"]
        read_only_fields = ["id"]

    def validate(self, data):
        institution = self.context.get("institution") or data.get("institution_info")
        if not institution:
            raise serializers.ValidationError(
                {"institution_info": "Institution info is required."}
            )
        if institution.admin != self.context["request"].user:
            raise serializers.ValidationError(
                {"institution_info": "You do not have permission to this institution."}
            )
        if not data.get("name"):
            raise serializers.ValidationError(
                {"name": "Global curriculum track is required."}
            )
        return data

    def create(self, validated_data):
        institution = validated_data.pop(
            "institution_info", self.context["institution"]
        )
        validated_data["institution_info"] = institution
        return CurriculumTrack.objects.create(**validated_data)


class SectionSerializer(serializers.ModelSerializer):
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=CurriculumTrack.objects.all()
    )
    curriculum_track_name = serializers.SlugRelatedField(
        source="curriculum_track.name", slug_field="name", read_only=True
    )
    enrollment_id = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            "id",
            "curriculum_track",
            "curriculum_track_name",
            "name",
            "is_active",
            "order",
            "enrollment_id",
        ]
        read_only_fields = ["id"]

    def get_enrollment_id(self, obj):
        user = self.context["request"].user
        if user.is_student:
            enrollment = StudentEnrollment.objects.filter(
                user=user, section=obj, is_active=True
            ).first()
            return str(enrollment.id) if enrollment else None
        elif user.is_teacher:
            enrollment = TeacherEnrollment.objects.filter(
                user=user, section=obj, is_active=True
            ).first()
            return str(enrollment.id) if enrollment else None
        return None

    def validate(self, data):
        institution = self.context.get("institution")
        curriculum_track = data.get("curriculum_track")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        if curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {
                    "curriculum_track": "Curriculum track does not belong to this institution."
                }
            )
        if not data.get("name"):
            raise serializers.ValidationError({"name": "Section name is required."})
        return data


class StreamSerializer(serializers.ModelSerializer):
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=CurriculumTrack.objects.all()
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), required=False, allow_null=True
    )
    name = serializers.PrimaryKeyRelatedField(queryset=GlobalStream.objects.all())
    curriculum_track_name = serializers.SlugRelatedField(
        source="curriculum_track.name", slug_field="name", read_only=True
    )
    section_name = serializers.CharField(
        source="section.name", read_only=True, allow_null=True
    )
    name_detail = serializers.CharField(source="name.name", read_only=True)

    class Meta:
        model = Stream
        fields = [
            "id",
            "curriculum_track",
            "curriculum_track_name",
            "section",
            "section_name",
            "name",
            "name_detail",
            "is_active",
            "order",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        institution = self.context.get("institution")
        curriculum_track = data.get("curriculum_track")
        section = data.get("section")
        name = data.get("name")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        if curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {
                    "curriculum_track": "Curriculum track does not belong to this institution."
                }
            )
        if section and section.curriculum_track != curriculum_track:
            raise serializers.ValidationError(
                {
                    "section": "Section does not belong to the specified curriculum track."
                }
            )
        if not name:
            raise serializers.ValidationError({"name": "Global stream is required."})
        return data


class SubjectSerializer(serializers.ModelSerializer):
    stream = serializers.PrimaryKeyRelatedField(queryset=Stream.objects.all())
    name = serializers.PrimaryKeyRelatedField(queryset=GlobalSubject.objects.all())
    stream_name = serializers.SlugRelatedField(
        source="stream.name", slug_field="name", read_only=True
    )
    name_detail = serializers.SlugRelatedField(
        source="name", slug_field="name", read_only=True
    )

    class Meta:
        model = Subject
        fields = [
            "id",
            "stream",
            "stream_name",
            "name",
            "name_detail",
            "is_active",
            "order",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        institution = self.context.get("institution")
        stream = data.get("stream")
        name = data.get("name")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        if stream.curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {"stream": "Stream does not belong to this institution."}
            )
        if not name:
            raise serializers.ValidationError({"name": "Global subject is required."})
        return data


class ModuleSerializer(serializers.ModelSerializer):
    subject = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all())
    title = serializers.PrimaryKeyRelatedField(queryset=GlobalModule.objects.all())
    subject_name = serializers.SlugRelatedField(
        source="subject.name", slug_field="name", read_only=True
    )
    title_detail = serializers.SlugRelatedField(
        source="title", slug_field="title", read_only=True
    )

    class Meta:
        model = Module
        fields = [
            "id",
            "subject",
            "subject_name",
            "title",
            "title_detail",
            "is_active",
            "order",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        institution = self.context.get("institution")
        subject = data.get("subject")
        title = data.get("title")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        if subject.stream.curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {"subject": "Subject does not belong to this institution."}
            )
        if not title:
            raise serializers.ValidationError({"title": "Global module is required."})
        return data


class UnitSerializer(serializers.ModelSerializer):
    module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())
    title = serializers.PrimaryKeyRelatedField(queryset=GlobalUnit.objects.all())
    module_title = serializers.SlugRelatedField(
        source="module.title", slug_field="title", read_only=True
    )
    title_detail = serializers.SlugRelatedField(
        source="title", slug_field="title", read_only=True
    )

    class Meta:
        model = Unit
        fields = [
            "id",
            "module",
            "module_title",
            "title",
            "title_detail",
            "is_active",
            "order",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        institution = self.context.get("institution")
        module = data.get("module")
        title = data.get("title")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        if module.subject.stream.curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {"module": "Module does not belong to this institution."}
            )
        if not title:
            raise serializers.ValidationError({"title": "Global unit is required."})
        return data


class LessonSerializer(serializers.ModelSerializer):
    unit = serializers.PrimaryKeyRelatedField(queryset=Unit.objects.all())
    title = serializers.PrimaryKeyRelatedField(queryset=GlobalLesson.objects.all())
    unit_title = serializers.SlugRelatedField(
        source="unit.title", slug_field="title", read_only=True
    )
    title_detail = serializers.SlugRelatedField(
        source="title", slug_field="title", read_only=True
    )

    class Meta:
        model = Lesson
        fields = [
            "id",
            "unit",
            "unit_title",
            "title",
            "title_detail",
            "is_active",
            "order",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        institution = self.context.get("institution")
        unit = data.get("unit")
        title = data.get("title")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        if unit.module.subject.stream.curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {"unit": "Unit does not belong to this institution."}
            )
        if not title:
            raise serializers.ValidationError({"title": "Global lesson is required."})
        return data


class MicroLessonSerializer(serializers.ModelSerializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    title = serializers.PrimaryKeyRelatedField(queryset=GlobalMicroLesson.objects.all())
    lesson_title = serializers.SlugRelatedField(
        source="lesson.title", slug_field="title", read_only=True
    )
    title_detail = serializers.SlugRelatedField(
        source="title", slug_field="title", read_only=True
    )

    class Meta:
        model = MicroLesson
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "title",
            "title_detail",
            "is_active",
            "order",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        institution = self.context.get("institution")
        lesson = data.get("lesson")
        title = data.get("title")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        if (
            lesson.unit.module.subject.stream.curriculum_track.institution_info
            != institution
        ):
            raise serializers.ValidationError(
                {"lesson": "Lesson does not belong to this institution."}
            )
        if not title:
            raise serializers.ValidationError(
                {"title": "Global micro lesson is required."}
            )
        return data


class TeacherEnrollmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_teacher=True)
    )
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=CurriculumTrack.objects.all(), many=True
    )
    section = serializers.PrimaryKeyRelatedField(
        queryset=Section.objects.all(), many=True, required=False
    )
    subjects = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Subject.objects.all(), required=False
    )
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    curriculum_track_names = serializers.SlugRelatedField(
        source="curriculum_track", slug_field="name__name", read_only=True, many=True
    )
    section_names = serializers.SlugRelatedField(
        source="section", slug_field="name", read_only=True, many=True
    )
    subject_names = serializers.SlugRelatedField(
        source="subjects", slug_field="name__name", read_only=True, many=True
    )

    class Meta:
        model = TeacherEnrollment
        fields = [
            "id",
            "user",
            "curriculum_track",
            "curriculum_track_names",
            "section",
            "section_names",
            "subjects",
            "subject_names",
            "is_active",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id", "institution"]

    def validate(self, data):
        is_partial = self.partial
        user = data.get(
            "user", getattr(self.instance, "user", None) if self.instance else None
        )
        curriculum_track = data.get(
            "curriculum_track",
            getattr(self.instance, "curriculum_track", None) if self.instance else None,
        )
        institution = self.context["institution"]
        if user and not is_partial:
            if not InstitutionMembership.objects.filter(
                user=user, institution=institution, role="teacher"
            ).exists():
                raise serializers.ValidationError(
                    {"user": "User must be a teacher in this institution."}
                )
        for ct in curriculum_track or []:
            if ct.institution_info != institution:
                raise serializers.ValidationError(
                    {
                        "curriculum_track": f"Curriculum track {ct} does not belong to this institution."
                    }
                )
        for section in data.get("section", []) or []:
            if section.curriculum_track not in curriculum_track:
                raise serializers.ValidationError(
                    {
                        "section": f"Section {section} does not belong to the specified curriculum tracks."
                    }
                )
        for subject in data.get("subjects", []) or []:
            if subject.stream.curriculum_track not in curriculum_track:
                raise serializers.ValidationError(
                    {
                        "subjects": f"Subject {subject} does not belong to the specified curriculum tracks."
                    }
                )
        return data

    def create(self, validated_data):
        curriculum_track = validated_data.pop("curriculum_track", [])
        section = validated_data.pop("section", [])
        subjects = validated_data.pop("subjects", [])
        validated_data["institution"] = self.context["institution"]
        enrollment = TeacherEnrollment.objects.create(**validated_data)
        enrollment.curriculum_track.set(curriculum_track)
        enrollment.section.set(section)
        enrollment.subjects.set(subjects)
        return enrollment

    def update(self, instance, validated_data):
        curriculum_track = validated_data.pop("curriculum_track", None)
        section = validated_data.pop("section", None)
        subjects = validated_data.pop("subjects", None)
        instance = super().update(instance, validated_data)
        if curriculum_track is not None:
            instance.curriculum_track.set(curriculum_track)
        if section is not None:
            instance.section.set(section)
        if subjects is not None:
            instance.subjects.set(subjects)
        return instance


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_student=True)
    )
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=CurriculumTrack.objects.all()
    )
    curriculum_track_name = serializers.CharField(
        source="curriculum_track.name.name", read_only=True
    )
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())
    section_name = serializers.CharField(source="section.name", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = [
            "id",
            "user",
            "curriculum_track",
            "curriculum_track_name",
            "section",
            "section_name",
            "is_active",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id", "institution"]

    def validate(self, data):
        is_partial = self.partial
        user = data.get(
            "user", getattr(self.instance, "user", None) if self.instance else None
        )
        curriculum_track = data.get(
            "curriculum_track",
            getattr(self.instance, "curriculum_track", None) if self.instance else None,
        )
        section = data.get(
            "section",
            getattr(self.instance, "section", None) if self.instance else None,
        )
        institution = self.context["institution"]
        if user and not is_partial:
            if not InstitutionMembership.objects.filter(
                user=user, institution=institution, role="student"
            ).exists():
                raise serializers.ValidationError(
                    {"user": "User must be a student in this institution."}
                )
        if curriculum_track and curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {
                    "curriculum_track": "Curriculum track does not belong to this institution."
                }
            )
        if section and section.curriculum_track != curriculum_track:
            raise serializers.ValidationError(
                {
                    "section": "Section does not belong to the specified curriculum track."
                }
            )
        return data

    def create(self, validated_data):
        validated_data["institution"] = self.context["institution"]
        return StudentEnrollment.objects.create(**validated_data)


# .............................#
#   PAYMENT FEE SERIALIZERS
# .............................#


# Institution Fee Serializer


class InstitutionFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionFee
        fields = ["id", "institution", "default_fee", "created_at", "updated_at"]
        read_only_fields = ["institution", "created_at", "updated_at"]

    def validate(self, data):
        institution = self.context.get("institution")
        if not institution:
            raise serializers.ValidationError(
                {"institution": "Institution context is required."}
            )
        return data

    def create(self, validated_data):
        validated_data["institution"] = self.context["institution"]
        return InstitutionFee.objects.create(**validated_data)


class CurriculumTrackFeeSerializer(serializers.ModelSerializer):
    curriculum_track = serializers.PrimaryKeyRelatedField(
        queryset=CurriculumTrack.objects.all()
    )
    curriculum_track_name = serializers.CharField(
        source="curriculum_track.name.name", read_only=True
    )

    class Meta:
        model = CurriculumTrackFee
        fields = [
            "id",
            "curriculum_track",
            "curriculum_track_name",
            "fee",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        institution = self.context.get("institution")
        curriculum_track = data.get("curriculum_track")
        if curriculum_track.institution_info != institution:
            raise serializers.ValidationError(
                {
                    "curriculum_track": "Curriculum track does not belong to this institution."
                }
            )
        return data


class StudentFeeSerializer(serializers.ModelSerializer):
    student_enrollment = serializers.PrimaryKeyRelatedField(
        queryset=StudentEnrollment.objects.all()
    )
    student_name = serializers.CharField(
        source="student_enrollment.user.get_full_name", read_only=True
    )

    class Meta:
        model = StudentFee
        fields = [
            "id",
            "student_enrollment",
            "student_name",
            "fee",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        institution = self.context.get("institution")
        student_enrollment = data.get("student_enrollment")
        if student_enrollment.institution != institution:
            raise serializers.ValidationError(
                {
                    "student_enrollment": "Student enrollment does not belong to this institution."
                }
            )
        return data
