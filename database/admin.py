from sqladmin import ModelView

from database.models import Options, Course


class OptionsAdmin(ModelView, model=Options):
    column_list = [Options.id, Options.option_name]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Option"
    name_plural = "Options"
    icon = "fa-solid fa-cog"
    category = "accounts"


class CourseAdmin(ModelView, model=Course):
    column_list = [Course.id, Course.course_name, Course.course_code, Course.credit, Course.location,
                   Course.description, Course.antirequisites, Course.corequisites, Course.prerequisites]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    name = "Course"
    name_plural = "Courses"
    icon = "fa-solid fa-book"
    category = "courses"


# class CoursePrerequisitesAdmin(ModelView, model=course_prerequisites):
#     column_list = [course_prerequisites.  .id, course_prerequisites.course_id, course_prerequisites.prerequisite_id]
#     can_create = True
#     can_edit = True
#     can_delete = True
#     can_view_details = True
#     name = "Course Prerequisite"
#     name_plural = "Course Prerequisites"
#     icon = "fa-solid fa-book"
#     category = "courses"
#
#
# class CourseCorequisitesAdmin(ModelView, model=course_corequisites):
#     column_list = [course_corequisites.id, course_corequisites.course_id, course_corequisites.corequisite_id]
#     can_create = True
#     can_edit = True
#     can_delete = True
#     can_view_details = True
#     name = "Course Corequisite"
#     name_plural = "Course Corequisites"
#     icon = "fa-solid fa-book"
#     category = "courses"
#
#
# class CourseAntirequisitesAdmin(ModelView, model=course_antirequisites):
#     column_list = [course_antirequisites.id, course_antirequisites.course_id, course_antirequisites.antirequisite_id]
#     can_create = True
#     can_edit = True
#     can_delete = True
#     can_view_details = True
#     name = "Course Antirequisite"
#     name_plural = "Course Antirequisites"
#     icon = "fa-solid fa-book"
#     category = "courses"


admin_views = [OptionsAdmin, CourseAdmin]