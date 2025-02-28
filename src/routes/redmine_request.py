from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response

from src.utils.redminereq import get_issues_info
from src.utils.catalogs import get_catalog_type_activity

router = APIRouter(prefix="/redmine", tags=["redmine"])

FILE_PATH_XLSX = Path("src/xlsx_files/Issues info.xlsx")
FILE_PATH_JSON = Path("src/xlsx_files/Issues info.json")


@router.get("/issues_info")
async def issues_info(project_id: str = None, project_stage: str | int = None,
                      time_from: str = None, time_to: str = None):
    """
    Get issues info based on query paras.

    - **project_id**: Id of project to get issues info for.
    - **project_stage**: Stage of project to get issues info for.
    - **time_from**: Start date to find issues. Format: YYYY-MM-DD.
    - **time_to**: End date to find issues. Format: YYYY-MM-DD.

    Return:

    - **message**: Message request.
    - **data**: Json response with issues info.
    """
    result = await get_issues_info(project_id=project_id, project_stage=project_stage,
                                   time_from=time_from, time_to=time_to)

    return JSONResponse(content=result)


@router.get("/catalog/activity_type")
def get_activity_type_catalog():
    result = get_catalog_type_activity()

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
    """
    Download json file to disk, by issues_info route.
    :return:
    """
    if not FILE_PATH_JSON.exists():
        return {"error": "Файл не знайдено"}

    return FileResponse(
        path=FILE_PATH_JSON,
        media_type="application/json",
        filename="Issues info.json"
    )
