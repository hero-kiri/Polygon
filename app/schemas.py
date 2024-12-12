from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class StockDataRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker, AAPL or TSLA")
    multiplier: int = Field(..., gt=0, description="Multiplier must be a positive integer")
    timespan: str = Field(
        ..., 
        pattern="^(minute|hour|day|week|month)$", 
        description="Valid timespans are: minute, hour, day, week, or month"
    )
    start_date: str = Field(..., description="Start date in format YYYY-MM-DD")
    end_date: str = Field(..., description="End date in format YYYY-MM-DD")

    @field_validator("start_date", "end_date")
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Date must be in the format YYYY-MM-DD")

    @field_validator("end_date")
    def validate_date_logic(cls, end_date, values):
        start_date = values.data.get("start_date")
        if start_date and start_date > end_date:
            raise ValueError("start_date must be earlier than or equal to end_date")
        return end_date
    