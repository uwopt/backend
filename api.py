import functools
from collections import defaultdict
from functools import lru_cache

from sqlalchemy.orm import Session
from sqlalchemy import and_, case, desc, func, or_, text
from db.models import EngineeringDisciplineModel, OptionsModel, EngineeringDisciplineModel, CourseModel, SamplePathModel, PrerequisiteModel
from db.database import SessionLocal
from db.schema import MissingList, MissingReqs, OptionsSchema, OptionRequirement, CoursesTakenIn, DegreeMissingReqs, \
    AdditionalReqCount, SamplePath, DegreeReqs, DegreeRequirement, CourseWithTagsSchema, TagSchema, MinLevel
import re

db = SessionLocal()


def clean_courses(courses):
    res = []
    for course in courses:
        res.append(course.strip())
    return res


def get_all_degrees(db: Session = None) -> dict[str, str]:
    degree_map = {degree.discipline_name.lower().replace(' ', '_'): degree.discipline_name for degree in
                  db.query(EngineeringDisciplineModel.discipline_name).distinct()}
    return degree_map


def is_degree_exist_for_year(degree_name: str, year: str, db: Session):
    return db.query(
        db.query(func.count())
        .filter(
            and_(
                EngineeringDisciplineModel.discipline_name == degree_name,
                EngineeringDisciplineModel.year == year
            )
        )
        .scalar()
    ).scalar() > 0


def is_option_exist_for_year(option_name: str, year: str, db: Session):
    return db.query(
        db.query(func.count())
        .filter(
            and_(
                OptionsModel.option_name == option_name,
                OptionsModel.year == year
            )
        )
        .scalar()
    ).scalar() > 0


def merge_dicts(dict1, dict2):
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result:
            result[key] = result[key].union(value)
        else:
            result[key] = value
    return result

# add logic to select most recent year
def get_degree_reqs(degree_name: str, year: str, db: Session) -> DegreeReqs:
    degree_map = get_all_degrees(db=db)
    degree_formatted_name = degree_map[degree_name]

    if (
            db.query(
                db.query(func.count())
                        .filter(
                    and_(
                        EngineeringDisciplineModel.discipline_name == degree_formatted_name,
                        EngineeringDisciplineModel.year == year
                    )
                )
                        .scalar()
            ).scalar() > 0
    ):
        rows = [{"courses": row.course_codes.split(","), "number_of_courses": row.number_of_courses, "term": row.term}
                for row in
                db.query(EngineeringDisciplineModel)
                .where(and_(EngineeringDisciplineModel.discipline_name == degree_formatted_name,
                            EngineeringDisciplineModel.year == year))
                .all()]
    else:
        latest_year = (
            db.query(func.max(EngineeringDisciplineModel.year))
            .filter(EngineeringDisciplineModel.discipline_name == degree_formatted_name)
            .scalar()
        )
        rows = [{"courses": row.course_codes.split(","), "number_of_courses": row.number_of_courses, "term": row.term}
                for row in
                db.query(EngineeringDisciplineModel)
                .where(and_(EngineeringDisciplineModel.discipline_name == degree_formatted_name,
                            EngineeringDisciplineModel.year == latest_year))
                .all()]

    requirements = DegreeReqs(mandatory_courses=[], additional_reqs={})

    for row in rows:
        if row["term"] != "MLSTN" and row["term"] != "PDENG" and row["term"] != "WKRPT" and row["term"] != "PD":
            courses = clean_courses(row["courses"])
            if len(courses) > 1:
                add_req_dict = DegreeRequirement(courses=[], number_of_courses=row["number_of_courses"])
                add_req_dict.courses = courses
                requirements.additional_reqs[row["term"]] = add_req_dict
            else:
                requirements.mandatory_courses += courses

    return requirements


# def populate_courses_tags(degree_name: str, degree_year: str, courses: list[CourseWithTagsSchema], db: Session, option_name: str = "", option_year: str = "") -> None:
#     """
#     Mutates the courses list to include tags
#     """
#     for course in courses:
#         populate_course_tags(degree_name=degree_name, degree_year=degree_year, course=course, db=db, option_name=option_name, option_year=option_year)


# @lru_cache()
def populate_courses_tags(courses: list[(CourseWithTagsSchema, str)], courses_tag_dict: dict[str, set[str]]) -> None:
    """
    Mutates the course object to include tags
    """
    courses_w_tags = []
    for course_obj in courses:
        course = course_obj[0]
        min_level = course_obj[1]
        print(min_level)
        tags = courses_tag_dict[course.course_code]
        course.tags = []
        course.min_level = MinLevel(max_level="", description="")
        for tag in tags:
            course.tags.append(tag_name_to_object(tag))
        if min_level:
            matches = re.match(r'{([^,]+),"([^"]+)"\}', min_level)
            min_level_instance = MinLevel(max_level=matches[1], description=matches[2])
            course.min_level = min_level_instance
        courses_w_tags.append(course)

    return courses_w_tags

def tag_name_to_object(tag_name: str) -> TagSchema:
    # blue = mandatory major requirement
    # red = TE
    # yellow = other requirement
    # purple = option requirement
    # green = elective
    name_to_schema = {
        "1A": TagSchema(code='1A', color='blue', short_name='1A', long_name='1A'),
        "1B": TagSchema(code='1B', color='blue', short_name='1B', long_name='1B'),
        "2A": TagSchema(code='2A', color='blue', short_name='2A', long_name='2A'),
        "2B": TagSchema(code='2B', color='blue', short_name='2B', long_name='2B'),
        "3A": TagSchema(code='3A', color='blue', short_name='3A', long_name='3A'),
        "3B": TagSchema(code='3B', color='blue', short_name='3B', long_name='3B'),
        "4A": TagSchema(code='4A', color='blue', short_name='4A', long_name='4A'),
        "4B": TagSchema(code='4B', color='blue', short_name='4B', long_name='4B'),
        "ATE": TagSchema(code='ATE', color='red', short_name='ATE', long_name='ATE'),
        "CSE": TagSchema(code='CSE', color='indigo', short_name='CSE', long_name='Complimentary Studies Elective'),
        "ELEC": TagSchema(code='ELEC', color='pink', short_name='ELEC', long_name='Elective'),
        "ETHICS": TagSchema(code='ETHICS', color='purple', short_name='ETHICS', long_name='Ethics'),
        "LE": TagSchema(code='LE', color='yellow', short_name='LE', long_name='Linkage Electives'),
        "MLSTN": TagSchema(code='MLSTN', color='green', short_name='MLSTN', long_name='Milestone'),
        "NSE": TagSchema(code='NSE', color='yellow', short_name='NSE', long_name='Natural Science Elective'),
        "PD": TagSchema(code='PD', color='yellow', short_name='PD', long_name='Professional Development'),
        "PDENG": TagSchema(code='PDENG', color='yellow', short_name='PDENG', long_name='Professional Development'),
        "PRACTICE": TagSchema(code='PRACTICE', color='yellow', short_name='PRACTICE', long_name='Practice'),
        "TE": TagSchema(code='TE', color='rose', short_name='TE', long_name='Technical Elective'),
        "WKRPT": TagSchema(code='WKRPT', color='yellow', short_name='WKRPT', long_name='Work Report'),
        "WKTRM": TagSchema(code='WKTRM', color='yellow', short_name='WKTRM', long_name='Work Term'),
        "WTREF": TagSchema(code='WTREF', color='yellow', short_name='WTREF', long_name='Work Term Reflection'),
        'SCE': TagSchema(code='SCE', color='yellow', short_name='SCE', long_name='Science Elective'),
        "elective": TagSchema(code='elective', color='green', short_name='elective', long_name='Option Elective'),
        "organizational_studies": TagSchema(code='organizational_studies', color='red', short_name='organizational_studies', long_name='Organizational Studies'),
        "eng_econ": TagSchema(code='eng_econ', color='orange', short_name='eng_econ', long_name='Engineering Economics'),
        "opti_1": TagSchema(code='opti_1', color='yellow', short_name='opti_1', long_name='Optimization'),
    }

    return name_to_schema[tag_name]


@functools.cache  # This should never change so we can indefinitely cache it
def get_degree_tags(degree_name: str, degree_year: str, db: Session) -> dict[str, set[str]]:
    # TODO: Implement logic that takes into account the case that 2015 and 2017 are published, but one requests for
    #  2016 (it should return 2015 but currently returns 2017)
    if is_degree_exist_for_year(degree_name, degree_year, db):
        tags = (
            db.query(EngineeringDisciplineModel.discipline_name,
                     EngineeringDisciplineModel.course_codes,
                     EngineeringDisciplineModel.term).filter(
                and_(
                    EngineeringDisciplineModel.discipline_name == degree_name,
                    EngineeringDisciplineModel.year == str(degree_year)
                )
            )).all()
    else:
        latest_year = (
            db.query(func.max(EngineeringDisciplineModel.year))
            .filter(EngineeringDisciplineModel.discipline_name == degree_name)
            .scalar()
        )
        tags = (
            db.query(EngineeringDisciplineModel.discipline_name,
                     EngineeringDisciplineModel.course_codes,
                     EngineeringDisciplineModel.term).filter(
                and_(
                    EngineeringDisciplineModel.discipline_name == degree_name,
                    EngineeringDisciplineModel.year == str(latest_year)
                )
            )).all()

    # [('management_engineering', 'CHE102', '1A'), ('management_engineering', 'MSCI100', '1A'),
    #  ('management_engineering', 'MATH115', '1A'), ('management_engineering', 'CHE102', '1A'),
    #  ('management_engineering', 'MSCI100', '1A'), ('management_engineering', 'MATH115', '1A'),
    #  ('management_engineering', 'MATH116', '1A'), ('management_engineering', 'PHYS115', '1A')]

    # Reduce the tags by course code
    tags_dict = defaultdict(set)
    for tags_tuple in tags:
        for course_code in tags_tuple[1].split(", "):
            tags_dict[course_code].add(tags_tuple[2])
    return tags_dict


@functools.cache  # This should never change so we can indefinitely cache it
def get_option_tags(option_name: str, option_year: str, db: Session) -> dict[str, set[str]]:
    if is_option_exist_for_year(option_name, option_year, db):
        tags = (
            db.query(OptionsModel.option_name,
                     OptionsModel.course_codes,
                     OptionsModel.name).filter(
                and_(
                    OptionsModel.option_name == option_name,
                    OptionsModel.year == str(option_year)
                )
            )).all()
    else:
        latest_year = (
            db.query(func.max(OptionsModel.year))
            .filter(OptionsModel.option_name == option_name)
            .scalar()
        )
        tags = (
            db.query(OptionsModel.option_name,
                     OptionsModel.course_codes,
                     OptionsModel.name).filter(
                and_(
                    OptionsModel.option_name == option_name,
                    OptionsModel.year == str(latest_year)
                )
            )).all()

    # [('management_engineering', 'CHE102', '1A'), ('management_engineering', 'MSCI100', '1A'),
    #  ('management_engineering', 'MATH115', '1A'), ('management_engineering', 'CHE102', '1A'),
    #  ('management_engineering', 'MSCI100', '1A'), ('management_engineering', 'MATH115', '1A'),
    #  ('management_engineering', 'MATH116', '1A'), ('management_engineering', 'PHYS115', '1A')]

    # Reduce the tags by course code
    tags_dict = defaultdict(set)
    for tags_tuple in tags:
        for course_code in tags_tuple[1].split(", "):
            tags_dict[course_code].add(tags_tuple[2])
    return tags_dict


def search_and_populate_courses(q: str, 
                                offset: int, 
                                degree_year: int, 
                                page_size: int, 
                                degree_name: str, 
                                db: Session, 
                                option_name: str = "", 
                                option_year: str = "",
                                tag: str = ""
                            ) -> (list)[CourseWithTagsSchema]:
    q = q.replace(" ", "")
    if tag:
        course_list = []
        tag_filtered =  (
        db.query(EngineeringDisciplineModel.discipline_name,
                EngineeringDisciplineModel.course_codes,
                EngineeringDisciplineModel.term).filter(
            and_(
                EngineeringDisciplineModel.discipline_name == degree_name,
                EngineeringDisciplineModel.year == str(degree_year),
                EngineeringDisciplineModel.term == tag
            )
        )).all()
        
        if not tag_filtered:
            tag_filtered = (
            db.query(OptionsModel.option_name,
                     OptionsModel.course_codes,
                     OptionsModel.name).filter(
                and_(
                    OptionsModel.option_name == option_name,
                    OptionsModel.year == str(option_year),
                    OptionsModel.name == tag
                )
            )).all()
            print(tag_filtered)
            
        for c in tag_filtered:
            course_list += c.course_codes.split(", ")

        courses = db.query(CourseModel, PrerequisiteModel.min_level).outerjoin(CourseModel, PrerequisiteModel.course_id == CourseModel.id).filter(CourseModel.course_code.in_(course_list))
        courses = (
            courses.filter(
            or_(
                CourseModel.course_code.ilike(f'%{q}%'),
                CourseModel.course_name.ilike(f'%{q}%'),
                text("similarity(course_code, :query) > 0.19").params(query=q),
                text("similarity(course_name, :query) > 0.19").params(query=q)
            )
        )
        .order_by(
            desc(text("similarity(course_code, :query)")).params(query=q), 
            CourseModel.course_code,
            desc(text("similarity(course_name, :query)")).params(query=q),
            CourseModel.course_name
            
        )
        .offset(offset)
        .limit(page_size)
        ).all()

    else: 
        courses = (
        db.query(CourseModel, PrerequisiteModel.min_level)
        .filter(
            or_(
                CourseModel.course_code.ilike(f'%{q}%'),
                CourseModel.course_name.ilike(f'%{q}%'),
                text("similarity(course_code, :query) > 0.19").params(query=q),
                text("similarity(course_name, :query) > 0.19").params(query=q)
            )
        )
        .outerjoin(CourseModel, PrerequisiteModel.course_id == CourseModel.id)
        .order_by(
            desc(text("similarity(course_code, :query)")).params(query=q), 
            CourseModel.course_code,
            desc(text("similarity(course_name, :query)")).params(query=q),
            CourseModel.course_name
            
        )
        .offset(offset)
        .limit(page_size)
        ).all()
    courses_w_tags = populate_courses_tags_search(degree_name=degree_name, year=str(degree_year), courses=courses, option_name=option_name, option_year=(option_year), db=db)
    return courses_w_tags

def populate_courses_tags_search(degree_name: str, year: str, courses: list[(CourseWithTagsSchema, str)], db: Session, option_name: str = "", 
                                option_year: str = "") -> None:
    """
    Mutates the course object to include tags
    """
    courses_w_tags = []
    for i, course_obj in enumerate(courses):
        course = course_obj[0]
        min_level = course_obj[1]
        tags = get_degree_tags(degree_name=degree_name, degree_year=year, db=db)
        if option_name and option_year:
            tags = merge_dicts(tags, get_option_tags(option_name, option_year, db))
        # EngineeringDisciplines table has no space in course codes, other tables do
        course_code_no_space = course.course_code.replace(" ", "")
        course_tags = tags[course_code_no_space] if course_code_no_space in tags else ['ELEC']
        course.tags = [tag_name_to_object(tag_name) for tag_name in course_tags]
        course.min_level = MinLevel(max_level="", description="")
        if min_level:
            matches = re.match(r'{([^,]+),"([^"]+)"\}', min_level)
            min_level_instance = MinLevel(max_level=matches[1], description=matches[2])
            course.min_level = min_level_instance

        courses_w_tags.append(course)
    return courses_w_tags

def get_degree_missing_reqs(degree_id: str, courses_taken: CoursesTakenIn, year: str, db: Session) -> DegreeMissingReqs:
    if (
            db.query(
                db.query(func.count())
                        .filter(
                    and_(
                        EngineeringDisciplineModel.discipline_name == degree_id,
                        EngineeringDisciplineModel.year == year
                    )
                )
                        .scalar()
            ).scalar() > 0
    ):
        reqs = (
            db.query(EngineeringDisciplineModel)
            .where(
                and_(EngineeringDisciplineModel.discipline_name == degree_id, EngineeringDisciplineModel.year == year))
            .all()
        )
    else:
        latest_year = (
            db.query(func.max(EngineeringDisciplineModel.year))
            .filter(EngineeringDisciplineModel.discipline_name == degree_id)
            .scalar()
        )
        reqs = (
            db.query(EngineeringDisciplineModel)
            .where(and_(EngineeringDisciplineModel.discipline_name == degree_id,
                        EngineeringDisciplineModel.year == latest_year))
            .all()
        )

    missing_courses = DegreeMissingReqs(mandatory_courses=[], number_of_mandatory_courses=0, tag=tag_name_to_object("1A"), additional_reqs={})

    mandatory_course_count = 0
    for req in reqs:
        if re.match(r'^\d[A-Z]$', req.term):
            mandatory_course_count += 1

    missing_courses.number_of_mandatory_courses = mandatory_course_count

    for req in reqs:
        req_long_name = tag_name_to_object(req.term).long_name
        if req.term != "MLSTN" and req.term != "PDENG" and req.term != "WKRPT" and req.term != "PD":
            if "," in req.course_codes:
                temp_dict = {}
                course_codes = req.course_codes.split(", ")
                count = 0
                for course_code in course_codes:
                    course_code = re.sub(r'[^a-zA-Z0-9]', '', course_code)
                    temp_dict[course_code] = 0
                
                for i, course_taken in reversed(tuple(enumerate(courses_taken))):
                    if course_taken in temp_dict:
                        if re.match(r'^\d[A-Z]$', req.term):
                            course_codes.remove(course_taken)
                        courses_taken.pop(i)
                        count += 1

                if re.match(r'^\d[A-Z]$', req.term):
                    course_codes = ", ".join(course_codes)
                    if count < req.number_of_courses:
                        missing_courses.mandatory_courses.append("(" + course_codes + ")")
                else:
                    if req_long_name not in missing_courses.additional_reqs:
                        missing_courses.additional_reqs[req_long_name] = AdditionalReqCount(completed=str(count),
                                                                                       total=str(req.number_of_courses),
                                                                                       tag=tag_name_to_object(req.term))
                    else:
                        missing_courses.additional_reqs[req_long_name].completed = str(
                            int(missing_courses.additional_reqs[req_long_name].completed) + count)
                        missing_courses.additional_reqs[req_long_name].total = str(
                            int(missing_courses.additional_reqs[req_long_name].total) + int(req.number_of_courses))

            else:
                if req.course_codes not in courses_taken:
                    if re.match(r'^\d[A-Z]$', req.term):
                        missing_courses.mandatory_courses.append(req.course_codes)
                    else:
                        missing_courses.additional_reqs[req_long_name] = AdditionalReqCount(completed="0", total="1", tag=tag_name_to_object(req.term))
    return missing_courses


def get_options_reqs(option_id: str, year: str, db: Session) -> OptionsSchema:
    rows = [{"courses": row.course_codes.split(","), "number_of_courses": row.number_of_courses, "name": row.name} for
            row in
            db.query(OptionsModel).filter(and_(OptionsModel.option_name == option_id, OptionsModel.year == year)).all()]
    res: OptionsSchema = {
        "option_name": str(option_id),  # Convert option_id to str if needed
        "requirements": [],
    }

    print('== rows', rows)

    for row in rows:
        courses = clean_courses(row["courses"])
        course_map = {"courses": courses, "number_of_courses": row["number_of_courses"], "name": row['name']}
        res["requirements"].append(OptionRequirement(**course_map))

    print("==wtf is this", res)

    return res


def validate_course_used_for_before(missing_requirement_list: list[MissingList], course: any):
    for requirement in missing_requirement_list:
        
        if course in requirement.courses and requirement.courses[course] == True:
            return True
    
    return False


def find_missing_requirements(course_list: list[str], requirements):
    missing_requirements = MissingReqs(lists=[])

    for requirement in requirements:
        courses_dict = {}

        # For each course in requirement that is in course_list, add to dictionary and assign value of True else False
        for course in requirement.courses:
            course_taken_before = validate_course_used_for_before(missing_requirements.lists, course)
            if course_taken_before:
                continue
            
            courses_dict[course] = course in course_list
            if course in course_list:
                course_list.remove(course)
                if course == "MSCI211" and "MSCI311" in requirement.courses:
                    requirement.courses.remove("MSCI311")
            
            

        # Calculate the total number of courses needed to complete the requirements
        total_courses_to_complete = requirement.number_of_courses

        # Create the MissingList instance for the current requirement
        missing_requirement = MissingList(
            list_name=requirement.name,
            courses=courses_dict,
            totalCourseToComplete=total_courses_to_complete,
            tag=tag_name_to_object(requirement.name)
        )

        missing_requirements.lists.append(missing_requirement)

    return missing_requirements


def get_option_missing_reqs(option_id: str, year: str, courses_taken: CoursesTakenIn, db: Session) -> MissingReqs:
    # get the requirements for the option
    data = get_options_reqs(option_id, year, db)
    # find the missing requirements
    missing_requirements: MissingReqs = find_missing_requirements(courses_taken, data["requirements"])

    if not missing_requirements:
        print("YAY all requirements met")
    else:
        print("MISSING REQUIREMENTS:", missing_requirements)

    return missing_requirements


def get_sample_paths(degree_name, db: Session):
    sample_paths = (
        db.query(SamplePathModel.course_code, SamplePathModel.course_order)
        .filter(SamplePathModel.engineering_discipline == degree_name)
        .all()
    )

    sample_path = []

    for course in sample_paths:
        sample_path.append(SamplePath(course_code=course.course_code, order_num=course.course_order))
    return sample_path
    
# get_degree_missing_reqs("software_engineering", ["CS137", "ECE105", "MATH115", "MATH119", "CS241", "ECE313"], "2023")
# get_options_reqs("management_sciences_option", db)

# courseCodesTaken = ["CHE102", "MSCI100", "MATH115", "MATH116", "PHYS115", "MSCI 211", "MSCI 331", "MSCI 442"]
# get_option_missing_reqs(option_id="management_sciences_option", courses_taken=courseCodesTaken, year="2023")

# get_degree_reqs("systems_design_engineering", "2023", db)
# search_and_populate_courses(q= "", offset= 0, degree_year= 2023, page_size= 20, degree_name= 'chemical_engineering', db=db, option_name="management_sciences_option", option_year= "2023", tag = "elective")
# get_degree_tags(degree_name="architectural_engineering", degree_year="2023", db=db)
# populate_courses_tags()

