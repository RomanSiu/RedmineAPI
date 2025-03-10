import os
import urllib3
import json
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
from redminelib import Redmine
from redminelib.exceptions import ResourceAttrError, ResourceNotFoundError

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Redmine configuration
load_dotenv()
REDMINE_URL = os.getenv('REDMINE_URL')
API_KEY = os.getenv('API_KEY')

requests_dict = {'project_name': "issue.project.name", 'project_id': "issue.project.id",
                 'version': "issue.fixed_version.name",
                 'issue_id': "issue.id", 'issue_tracker': "issue.tracker.name", 'issue_subject': "issue.subject",
                 'done_ratio': "issue.done_ratio",
                 'status': "issue.status.name", 'planned_hours': "issue.estimated_hours"}

# Connect to Redmine
try:
    print(REDMINE_URL, API_KEY)
    redmine = Redmine(REDMINE_URL, key=API_KEY, requests={'verify': False})
except Exception as e:
    print(f"Failed to connect to Redmine: {e}")
    exit()


async def get_issues_by_query(time_from, time_to, project_id: str = None, project_stage: str | int = None):
    time_to = datetime.now().date()
    filter_kwargs = {'status_id': '*'}
    if project_id:
        filter_kwargs['project_id'] = project_id
    if project_stage:
        try:
            project_stage = int(project_stage)
        except ValueError:
            pass
        filter_kwargs['cf_18'] = project_stage
    # filter_kwargs['updated_on'] = f"><{time_from}|{time_to if time_to else ''}"
    filter_kwargs['updated_on'] = f"><{time_from}|{time_to}"

    issues = redmine.issue.filter(**filter_kwargs)
    return issues


# def create_xlsx_file(issues_list: list) -> None:
#     wb = Workbook()
#     ws = wb.active
#     ws.title = "Issues info"
#     ws.append(['ПІБ', 'Ідентифікатор спеціаліста', 'Проект', 'Ідентифікатор проекта', 'Договір', 'Етап', 'Версія',
#                'Версія ПО', 'Номер задачі', 'Трекер', 'Тема', 'Специфіка задачі', 'Дата початку', 'Дата завершення',
#                'Готовність', 'Діяльність', 'Планові працевитрати', 'Фактичні працевитрати'])
#     for issue in issues_list:
#         ws.append([issue['name'], issue['user_id'],
#                    issue['project_name'], issue['project_id'], issue['contract'], issue['stage'],
#                    issue['version'], issue['software_version'],
#                    issue['issue_id'], issue['issue_tracker'], issue['issue_subject'], '',
#                    issue['start_date'], issue['end_date'], issue['done_ratio'],
#                    issue['status'], issue['planned_hours'], issue['real_hours']])
#     output_file = r"src/xlsx_files/Issues info.xlsx"
#     try:
#         wb.save(output_file)
#     except Exception as e:
#         print(f"Failed to save xlsx file: {e}")


def create_json_file(issues_list: list) -> None:
    try:
        os.remove(r"src/xlsx_files/Issues info.json")
    except FileNotFoundError:
        ...
    with open(r"src/xlsx_files/Issues info.json", 'w', encoding='utf-8') as f:
        json.dump(issues_list, f, ensure_ascii=False, indent=4)


def get_info(issues, time_from, time_to) -> list:
    issues_info = []
    for issue in issues:
        issue_dict = {}
        for key, value in requests_dict.items():
            try:
                issue_dict[key] = eval(value)
            except ResourceAttrError:
                issue_dict[key] = None

        issue_dict.update(get_date_fields(issue))
        issue_dict.update(get_custom_fields(issue))

        time_entries_data = get_time_entries(issue, time_from, time_to)

        if time_entries_data:
            for val in time_entries_data:
                issue_dict.update(val)
                issues_info.append(issue_dict.copy())
        else:
            # try:
            #     time_entries = issue.time_entries
            #     issue_dict['name'] = issue.assigned_to.name
            #     issue_dict['user_id'] = issue.assigned_to.id
            #     issue_dict['real_hours'] = issue.spent_hours
            #     issue_dict['updated_date'] = issue.updated_on.strftime("%d-%m-%Y")
            #     if issue.updated_on.date() > time_to:
            #         continue
            #     if issue_dict['real_hours'] == 0:
            #         continue
            #     issues_info.append(issue_dict)
            # except ResourceAttrError:
            #     continue
            continue

    return issues_info


def get_date_fields(issue):
    date_fields_data = {}
    date_request = {'start_date': "issue.start_date", 'end_date': "issue.due_date"}

    for key, value in date_request.items():
        try:
            date = eval(value)
            if date:
                date_fields_data[key] = date.strftime("%d-%m-%Y")
            else:
                date_fields_data[key] = None
        except ResourceAttrError:
            date_fields_data[key] = None

    return date_fields_data


def get_custom_fields(issue):
    custom_fields_data = {}

    for field_id, name in {13: 'contract', 16: 'software_version', 21: 'stage', 19: 'issue_type',
                           20: 'error_reason'}.items():
        try:
            custom_fields_data[name] = issue.custom_fields.get(field_id).value
        except (ResourceAttrError, AttributeError):
            custom_fields_data[name] = None

    return custom_fields_data


def get_time_entries(issue, time_from, time_to):
    time_entries_data_dict = []
    time_entries = issue.time_entries

    for time_entry in time_entries:
        if time_from <= time_entry.updated_on.date() <= time_to:
            time_entries_data = {}
            name, user_id = time_entry.user.name, time_entry.user.id
            time_entries_data['time_entry_id'] = time_entry.id
            time_entries_data['name'] = name
            time_entries_data['user_id'] = user_id
            time_entries_data['activity'] = time_entry.activity.name
            time_entries_data['real_hours'] = time_entry.hours
            time_entries_data['time_entry_date'] = time_entry.spent_on.strftime("%d-%m-%Y")
            time_entries_data['updated_data'] = time_entry.updated_on.strftime("%d-%m-%Y")
            if time_entries_data['real_hours'] == 0:
                continue
            time_entries_data_dict.append(time_entries_data)

    return time_entries_data_dict


async def get_issues_info(time_from, time_to, **kwargs):
    if time_from:
        time_from = datetime.strptime(time_from, '%Y-%m-%d').date()
    else:
        time_from = datetime(year=1970, month=1, day=1).date()
    if time_to:
        time_to = datetime.strptime(time_to, '%Y-%m-%d').date()
    else:
        time_to = datetime.now().date()

    issues = await get_issues_by_query(time_from, time_to, **kwargs)

    try:
        issues_info = get_info(issues, time_from, time_to)
        # create_xlsx_file(issues_info)
        create_json_file(issues_info)
        data = jsonable_encoder(issues_info)
        return {'message': 'Issues info saved successfully', 'data': data}
    except ResourceNotFoundError:
        # create_xlsx_file([])
        create_json_file([])
        return {'message': 'Issues not found'}


if __name__ == '__main__':
    get_issues_info(time_from='2024-12-12', time_to='2024-12-14')
    # 24002-ПФУ (підтримка)  24005-ПФУ (модернізація)
