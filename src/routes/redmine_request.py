from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from utils.redminereq import get_burned_hours

router = APIRouter(prefix="/redmine", tags=["redmine"])

FILE_PATH = Path("src/xlsx_files/burned_hours_per_worker.xlsx")


@router.get("/burned_hours")
async def burned_hours(contract_num: str = None, project_stage: str | int = None,
                       time_from: str = None, time_to: str = None):
    result = await get_burned_hours(contract_num=contract_num, project_stage=project_stage,
                                    time_from=time_from, time_to=time_to)
    return result


@router.get("/download_excel", response_class=FileResponse)
async def download_excel():
    if not FILE_PATH.exists():
        return {"error": "Файл не знайдено"}

    return FileResponse(
        path=FILE_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="burned_hours_per_project.xlsx"
    )
