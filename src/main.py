from typing import Annotated
import requests
from fastapi import FastAPI, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from db.models import CourseModel, EngineeringDisciplineModel
from db.schema import CourseSchema, CourseWithTagsSchema, OptionsSchema, OptionRequirement, DegreeMissingReqs, \
    DegreeReqs
from collections import defaultdict
from db.schema import CoursesTakenIn, RequirementsResults
from db.database import SessionLocal
from sqladmin import Admin
from sqlalchemy.orm import Session
from sqlalchemy import and_

from db import engine
from db.admin import admin_views
from db.database import SessionLocal
from .validation import can_take_course
from api import get_options_reqs, get_degree_reqs, get_all_degrees, get_degree_missing_reqs, get_option_missing_reqs, \
    get_degree_tags, search_and_populate_courses

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin dashboard
admin = Admin(app, engine)
for view in admin_views:
    admin.add_view(view)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"Hello": "Worasdfld"}


@app.get("/query")
def read_item():
    url = 'https://openapi.data.uwaterloo.ca/v3/subjects'
    api_key = '2FEF9C75B2F34CAF91CC3B6DF0D6C6C0'
    header = {'x-api-key': api_key}

    response = requests.get(url, headers=header)
    return response.json()


# --------
# done
@app.get('/option/{opt_id}/reqs', response_model=OptionsSchema)
def options_reqs(opt_id: str, year: str, db: Session = Depends(get_db)):
    reqs = get_options_reqs(opt_id, year, db)
    return reqs


# done
@app.get('/option/{opt_id}/missing_reqs', response_model=list[OptionRequirement])
def options_missing_reqs(opt_id: str, courses_taken: CoursesTakenIn, year: str, db: Session = Depends(get_db)):
    missing_reqs = get_option_missing_reqs(opt_id, year, courses_taken)
    return missing_reqs


# done
@app.get('/degree/{degree_name}/reqs', response_model=DegreeReqs)
def degree_reqs(degree_name: str, year: str, db: Session = Depends(get_db)):
    reqs = get_degree_reqs(degree_name, year, db)
    return reqs


# done
@app.get('/degree')
def degrees(db: Session = Depends(get_db)) -> list[str]:
    degrees = get_all_degrees(db).keys()
    return degrees


# done
@app.get('/degree/{degree_id}/missing_reqs', response_model=DegreeMissingReqs)
def degree_missing_reqs(degree_id: str, courses_taken: CoursesTakenIn, year: str, db: Session = Depends(get_db)):
    missing_reqs = get_degree_missing_reqs(degree_id, courses_taken, year, db)
    return missing_reqs


# done
@app.get('/courses/can-take/{course_code}', response_model=RequirementsResults)
def courses_can_take(course_code: str, courses_taken: CoursesTakenIn, db: Session = Depends(get_db)):
    can_take = can_take_course(db, courses_taken.course_codes_taken, course_code)
    res = RequirementsResults(result=can_take[0], message=can_take[1])
    return res


# done
@app.get('/courses/search', response_model=list[CourseWithTagsSchema])
# @app.get('/courses/search')
def search_courses(q: str | None = None, offset: Annotated[int | None, "bruh"] = 0,
                   page_size: Annotated[int | None, Path(title="Number of results returned", gt=0, le=100)] = 20,
                   degree_name: Annotated[str | None, "The degree name, e.g. 'management_engineering'"] = None,
                   degree_year: Annotated[str | None, "The year the plan was declared"] = None):
    courses = search_and_populate_courses(q=q, offset=offset, page_size=page_size, degree_name=degree_name, degree_year=degree_year)
    return courses


@app.get('/courses/tags')
def tags(degree_name: Annotated[str, "The degree name, e.g. 'management_engineering'"],
         degree_year: Annotated[str, "The year the plan was declared"]):
    return get_degree_tags(degree_name, degree_year)


@app.get('/sample-path')
def sample_path():
    return {
        "lol": "rooined"
    }
