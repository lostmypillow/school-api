from pydantic import BaseModel


class LogRecordCreate(BaseModel):
    employee_name: str    # 對應: 員工姓名
    category: str         # 對應: 類別
    log_content: str      # 對應: 記錄檔 (ntext)
    computer_name: str    # 對應: 電腦名稱
    employee_id: str       # 對應: student_id
