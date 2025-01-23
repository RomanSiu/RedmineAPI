from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from src.utils.redminereq import get_issues_info

router = APIRouter(prefix="/redmine", tags=["redmine"])

FILE_PATH_XLSX = Path("src/xlsx_files/Issues info.xlsx")
FILE_PATH_JSON = Path("src/xlsx_files/Issues info.json")


@router.get("/issues_info")
async def issues_info(contract_num: str = None, project_stage: str | int = None,
                      time_from: str = None, time_to: str = None):
    result = await get_issues_info(contract_num=contract_num, project_stage=project_stage,
                                   time_from=time_from, time_to=time_to)

    return JSONResponse(content=result)


# @router.get("/download_excel", response_class=FileResponse)
# async def download_excel():
#     if not FILE_PATH_XLSX.exists():
#         return {"error": "Файл не знайдено"}
#
#     return FileResponse(
#         path=FILE_PATH_XLSX,
#         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         filename="Issues info.xlsx"
#     )


@router.get("/download_json", response_class=FileResponse)
async def download_json():
    if not FILE_PATH_JSON.exists():
        return {"error": "Файл не знайдено"}

    return FileResponse(
        path=FILE_PATH_JSON,
        media_type="application/json",
        filename="Issues info.json"
    )
