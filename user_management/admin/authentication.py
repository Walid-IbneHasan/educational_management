from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password
from user_management.models.authentication import (
    User,
    InstitutionMembership,
    Invitation,
    ParentChildRelationship,
)


class UserAdminForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=False,
        help_text="Enter a raw password. It will be hashed before saving. Leave blank to keep the existing password during updates.",
    )

    class Meta:
        model = User
        fields = "__all__"

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if self.instance.pk and not password:
            # If updating and password is blank, keep the existing password
            return self.instance.password
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.password = make_password(password)
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    list_display = (
        "id",
        "email",
        "phone_number",
        "first_name",
        "last_name",
        "get_roles",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_institution",
        "is_teacher",
        "is_student",
        "is_parents",
        "is_admission_seeker",
        "is_active",
        "is_staff",
    )
    search_fields = ("email", "phone_number", "first_name", "last_name")
    list_display_links = ("id", "email", "phone_number")
    list_per_page = 25
    save_on_top = True
    readonly_fields = ("id", "created_at")
    fieldsets = (
        (
            "Personal Information",
            {
                "fields": (
                    "email",
                    "phone_number",
                    "first_name",
                    "last_name",
                    "gender",
                    "birth_date",
                    "profile_image",
                ),
            },
        ),
        (
            "Authentication",
            {
                "fields": ("password",),
            },
        ),
        (
            "Role Flags",
            {
                "fields": (
                    "is_institution",
                    "is_teacher",
                    "is_student",
                    "is_parents",
                    "is_admission_seeker",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_at"),
            },
        ),
    )

    def get_roles(self, obj):
        roles = []
        if obj.is_institution:
            roles.append("Institution")
        if obj.is_teacher:
            roles.append("Teacher")
        if obj.is_student:
            roles.append("Student")
        if obj.is_parents:
            roles.append("Parent")
        if obj.is_admission_seeker:
            roles.append("Admission Seeker")
        return ", ".join(roles) or "None"

    get_roles.short_description = "Roles"


class InstitutionMembershipInline(admin.TabularInline):
    model = InstitutionMembership
    extra = 1
    raw_id_fields = ("user",)
    show_change_link = True


class InvitationInline(admin.TabularInline):
    model = Invitation
    extra = 1
    readonly_fields = ("token", "created_at", "expires_at")
    fields = (
        "email",
        "phone_number",
        "role",
        "token",
        "is_used",
        "created_at",
        "expires_at",
    )
    show_change_link = True


@admin.register(InstitutionMembership)
class InstitutionMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_email",
        "user_phone",
        "institution_name",
        "role",
        "created_at",
    )
    list_filter = ("role", "institution", "created_at")
    search_fields = (
        "user__email",
        "user__phone_number",
        "institution__name",
    )
    list_display_links = ("id",)
    list_per_page = 25
    save_on_top = True
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("user", "institution")
    fieldsets = (
        (
            "Membership Details",
            {
                "fields": ("user", "institution", "role"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_at"),
            },
        ),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"

    def user_phone(self, obj):
        return obj.user.phone_number

    user_phone.short_description = "User Phone"

    def institution_name(self, obj):
        return obj.institution.name

    institution_name.short_description = "Institution"


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "phone_number",
        "institution_name",
        "role",
        "is_used",
        "created_at",
        "expires_at",
    )
    list_filter = ("role", "is_used", "institution", "created_at")
    search_fields = ("email", "phone_number", "institution__name")
    list_display_links = ("id", "email", "phone_number")
    list_per_page = 25
    save_on_top = True
    readonly_fields = ("id", "token", "created_at", "expires_at")
    fieldsets = (
        (
            "Invitation Details",
            {
                "fields": (
                    "email",
                    "phone_number",
                    "institution",
                    "role",
                    "token",
                    "is_used",
                ),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_at", "expires_at"),
            },
        ),
    )

    def institution_name(self, obj):
        return obj.institution.name

    institution_name.short_description = "Institution"


@admin.register(ParentChildRelationship)
class ParentChildRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "parent_email",
        "parent_phone",
        "child_email",
        "child_phone",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "parent__email",
        "parent__phone_number",
        "child__email",
        "child__phone_number",
    )
    list_display_links = ("id",)
    list_per_page = 25
    save_on_top = True
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("parent", "child")
    fieldsets = (
        (
            "Relationship Details",
            {
                "fields": ("parent", "child"),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("id", "created_at"),
            },
        ),
    )

    def parent_email(self, obj):
        return obj.parent.email

    parent_email.short_description = "Parent Email"

    def parent_phone(self, obj):
        return obj.parent.phone_number

    parent_phone.short_description = "Parent Phone"

    def child_email(self, obj):
        return obj.child.email

    child_email.short_description = "Child Email"

    def child_phone(self, obj):
        return obj.child.phone_number

    child_phone.short_description = "Child Phone"
