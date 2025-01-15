import os
import urllib3
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv
from openpyxl import Workbook
from redminelib import Redmine
from redminelib.exceptions import ResourceAttrError, ResourceNotFoundError

from logger import logger

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

date_request = {'start_date': "issue.start_date", 'end_date': "issue.due_date"}

# Connect to Redmine
try:
    redmine = Redmine(REDMINE_URL, key=API_KEY, requests={'verify': False})
    logger.info('Redmine connected successfully')
except Exception as e:
    logger.error(f"Failed to connect to Redmine: {e}")
    exit()


def logging_func(func):
    def inner(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = None
            logger.error(f"Failed to run {func.__name__}: {e}")
        else:
            return result
        return result
    return inner


async def get_issues_by_query(time_from, time_to, contract_num: str = None, project_stage: str | int = None):
    filter_kwargs = {'status_id': '*'}
    if contract_num:
        filter_kwargs['project_id'] = contract_num
    if project_stage:
        try:
            project_stage = int(project_stage)
        except ValueError:
            pass
        filter_kwargs['cf_18'] = project_stage
    filter_kwargs['updated_on'] = f"><{time_from}|{time_to if time_to else ''}"

    if filter_kwargs:
        issues = redmine.issue.filter(**filter_kwargs)
    else:
        issues = redmine.issue.all()
    return issues


@logging_func
def get_user_name(issue) -> str | None:
    try:
        user_name = issue.assigned_to.name
    except ResourceAttrError:
        try:
            parent_issue = redmine.issue.get(issue.parent)
        except ResourceAttrError:
            return None
        user_name = get_user_name(parent_issue)
    return user_name


def get_user_hours(issues) -> dict:
    user_burned_hours_dict = defaultdict(int)
    for issue in issues:
        user_name = get_user_name(issue)
        if not user_name:
            continue
        try:
            user_hours = issue.spent_hours
        except ResourceAttrError:
            user_hours = 0.0
        user_burned_hours_dict[user_name] += user_hours
    return user_burned_hours_dict


def create_xlsx_file(issues_list: list) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Issues info"
    ws.append(['ПІБ', 'Ідентифікатор спеціаліста', 'Проект', 'Ідентифікатор проекта', 'Договір', 'Етап', 'Версія',
               'Версія ПО', 'Номер задачі', 'Трекер', 'Тема', 'Специфіка задачі', 'Дата початку', 'Дата завершення',
               'Готовність', 'Діяльність', 'Планові працевитрати', 'Фактичні працевитрати'])
    for issue in issues_list:
        ws.append([issue['name'], issue['user_id'],
                   issue['project_name'], issue['project_id'], issue['contract'], issue['stage'],
                   issue['version'], issue['software_version'],
                   issue['issue_id'], issue['issue_tracker'], issue['issue_subject'], '',
                   issue['start_date'], issue['end_date'], issue['done_ratio'],
                   issue['status'], issue['planned_hours'], issue['real_hours']])
    output_file = r"src/xlsx_files/Issues info.xlsx"
    try:
        wb.save(output_file)
    except Exception as e:
        logger.error(f"Failed to save xlsx file: {e}")


async def get_burned_hours(**kwargs):
    issues = await get_issues_by_query(**kwargs)
    user_burned_hours = get_user_hours(issues)
    for name, hours in user_burned_hours.items():
        user_burned_hours[name] = "{:.1f}".format(hours)
    create_xlsx_file(user_burned_hours)
    return user_burned_hours


def get_info(issues, time_from, time_to) -> list:
    issues_info = []
    for issue in issues:
        issue_dict = {}
        for key, value in requests_dict.items():
            try:
                issue_dict[key] = eval(value)
            except ResourceAttrError:
                issue_dict[key] = None

        for key, value in date_request.items():
            try:
                date = eval(value)
                if date:
                    issue_dict[key] = date.strftime("%d-%m-%Y")
                else:
                    issue_dict[key] = None
            except ResourceAttrError:
                issue_dict[key] = None

        for field_id, name in {13: 'contract', 16: 'software_version', 18: 'stage'}.items():
            try:
                issue_dict[name] = issue.custom_fields.get(field_id).value
            except (ResourceAttrError, AttributeError):
                issue_dict[name] = None

        time_entries_data = get_time_entries(issue, time_from, time_to)

        if time_entries_data:
            for val in time_entries_data:
                issue_dict.update(val)
                issues_info.append(issue_dict.copy())
        else:
            issue_dict['name'] = issue.assigned_to.name
            issue_dict['user_id'] = issue.assigned_to.id
            issue_dict['real_hours'] = issue.spent_hours
            issues_info.append(issue_dict)
    return issues_info


def get_time_entries(issue, time_from, time_to):
    if not time_to:
        time_to = datetime.now().date()

    time_entries_data_dict = []
    time_entries = issue.time_entries

    for time_entry in time_entries:
        if time_from <= time_entry.created_on.date() <= time_to:
            time_entries_data = {}
            name, user_id = time_entry.user.name, time_entry.user.id
            time_entries_data['name'] = name
            time_entries_data['user_id'] = user_id
            time_entries_data['real_hours'] = time_entry.hours
            time_entries_data_dict.append(time_entries_data)
            # if name not in time_entries_data_dict:
            #     time_entries_data_dict[name] = {'real_hours': 0}
            # time_entries_data = time_entries_data_dict[name]
            # time_entries_data['name'] = name
            # time_entries_data['user_id'] = user_id
            # time_entries_data['real_hours'] += time_entry.hours
            # time_entries_data_dict[name] = time_entries_data

    return time_entries_data_dict


async def get_issues_info(time_from, time_to, **kwargs):
    if time_from:
        time_from = datetime.strptime(time_from, '%Y-%m-%d').date()
    else:
        time_from = datetime(year=1970, month=1, day=1).date()
    if time_to:
        time_to = datetime.strptime(time_to, '%Y-%m-%d').date()

    issues = await get_issues_by_query(time_from, time_to, **kwargs)

    try:
        issues_info = get_info(issues, time_from, time_to)
        create_xlsx_file(issues_info)
        return {'message': 'Issues info saved successfully'}
    except ResourceNotFoundError:
        return {'message': 'Issues not found'}


if __name__ == '__main__':
    get_issues_info(time_from='2024-12-12', time_to='2024-12-14')
    # 24002-ПФУ (підтримка)  24005-ПФУ (модернізація)
