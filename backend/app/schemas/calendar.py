from pydantic import BaseModel


class CalendarEventOut(BaseModel):
    day: int
    start_time: str
    end_time: str
    label: str
