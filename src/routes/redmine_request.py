from fastapi import APIRouter

from src.utils.redminereq import get_burned_hours

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/burned_hours")
async def burned_hours(contract_num: str = None, project_stage: int = None,
                       time_from: str = None, time_to: str = None):
    result = await get_burned_hours(contract_num=contract_num, project_stage=project_stage,
                                    time_from=time_from, time_to=time_to)
    return result
