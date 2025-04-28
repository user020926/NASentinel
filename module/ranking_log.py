import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

class Ranking_Log:    
    """
    排行榜日誌類，用於記錄和保存上傳、下載、刪除次數的排行榜數據。

    屬性:
        RANKING_COLUMNS (list): 排行榜表格的欄位名稱。
        logs (List[Dict[str, str]]): 儲存排行榜記錄的列表。
        log_file (str): 日誌檔案的保存路徑。
    """
    RANKING_COLUMNS = ["排名", "使用者", "次數", "姓名", "電子郵件"]

    def __init__(self):
        """
        初始化 Ranking_Log 實例，設置日誌列表和檔案路徑。
        """
        self.logs: List[Dict[str, str]] = []
        self.log_file = self.get_log_path()

    def get_log_path(self) -> str:
        """
        生成日誌檔案的保存路徑，使用當前時間戳命名並儲存至桌面。

        返回:
            str: 日誌檔案的完整路徑。
        """
        date_str = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
        desktop_path = Path.home() / "Desktop"
        return str(desktop_path / f"NAS_Ranking_Log_{date_str}.xlsx")

    def add_log(self, ranking_type: str, rank: int, username: str, count: int, name: str, email: str):
        """
        添加排行榜記錄至日誌列表。

        參數:
            ranking_type (str): 排行榜類型（例如 "upload", "download", "delete"）。
            rank (int): 排名。
            username (str): 使用者名稱。
            count (int): 事件次數。
            name (str): 使用者姓名。
            email (str): 使用者電子郵件。

        異常:
            Exception: 若添加記錄失敗，拋出包含錯誤訊息的異常。
        """
        try:
            entry = {
                "排名": str(rank),
                "使用者": username,
                "次數": str(count),
                "姓名": name,
                "電子郵件": email,
                "類型": ranking_type
            }
            self.logs.append(entry)
        except Exception as e:
            raise Exception(f"添加排行榜日誌失敗: {str(e)}")
        
    def save_to_excel(self) -> bool:
        """
        將排行榜日誌保存為 Excel 檔案，包含上傳、下載、刪除三個工作表，並應用格式化樣式。

        返回:
            bool: 若保存成功，返回 True；若無日誌數據，返回 False。

        異常:
            Exception: 若保存失敗，拋出包含錯誤訊息的異常。
        """
        if not self.logs:
            return False
        try:
            df = pd.DataFrame(self.logs, columns=self.RANKING_COLUMNS + ["類型"])
            workbook = Workbook()
            default_sheet = workbook.active
            workbook.remove(default_sheet)
            title_font = Font(bold=True, size=14)
            title_alignment = Alignment(horizontal='center', vertical='center')

            header_font = Font(bold=True)
            header_alignment = Alignment(horizontal='center', vertical='center')
            header_fill = PatternFill(start_color='BFD1E5', end_color='BFD1E5', fill_type='solid')
            border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            
            data_alignment = Alignment(horizontal='center', vertical='center')
            
            column_widths = {
                'A': 8,  # 排名
                'B': 15,  # 使用者
                'C': 10,  # 次數
                'D': 15,  # 姓名
                'E': 25  # 電子郵件
            }

            for ranking_type, sheet_name, title in [
                ("upload", "上傳排行榜", "上傳次數排行榜"),
                ("download", "下載排行榜", "下載次數排行榜"),
                ("delete", "刪除排行榜", "刪除次數排行榜")
            ]:
                type_df = df[df["類型"] == ranking_type][self.RANKING_COLUMNS]
                
                if type_df.empty:
                    continue

                worksheet = workbook.create_sheet(title=sheet_name)
                worksheet.merge_cells('A1:E1')
                title_cell = worksheet['A1']
                title_cell.value = title
                title_cell.font = title_font
                title_cell.alignment = title_alignment

                for col_num, value in enumerate(self.RANKING_COLUMNS, 1):
                    cell = worksheet.cell(row=2, column=col_num)
                    cell.value = value
                    cell.font = header_font
                    cell.alignment = header_alignment
                    cell.fill = header_fill
                    cell.border = border

                for row_idx, row_data in enumerate(type_df.itertuples(), 3):
                    for col_idx, value in enumerate(row_data[1:], 1):
                        cell = worksheet.cell(row=row_idx, column=col_idx)
                        cell.value = value
                        cell.alignment = data_alignment
                        cell.border = border

                for col_letter, width in column_widths.items():
                    worksheet.column_dimensions[col_letter].width = width
            
            workbook.save(self.log_file)
            self.logs.clear()
            return True
        except Exception as e:
            raise Exception(f"保存排行榜日誌失敗: {str(e)}")