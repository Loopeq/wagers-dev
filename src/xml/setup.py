import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import (Alignment)
from openpyxl.worksheet.worksheet import Worksheet

from src.utils.common import iso_to_msc
from src.xml.styles import H2

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
FILE_DIR = Path(__file__).resolve().parent
WORK_DIR = FILE_DIR / 'sheets'
WORK_DIR.mkdir(exist_ok=True)


def make_head(ws: Worksheet, file_io):
    from openpyxl.cell.text import InlineFont
    from openpyxl.cell.rich_text import TextBlock, CellRichText

    obj = json.load(file_io)

    sport_name = obj['sport_name']
    league_name = obj["league_name"]
    home_name = obj["home_name"]
    away_name = obj["away_name"]
    start_time = obj['start_time']

    home_font = InlineFont(rFont='Roboto', sz=20, color='008000')
    away_font = InlineFont(rFont='Roboto', sz=20, color='B22222')
    common_font = InlineFont(rFont='Roboto', sz=20)

    title = CellRichText([TextBlock(common_font, league_name),
                          TextBlock(common_font, ' | '),
                          TextBlock(home_font, home_name),
                          TextBlock(common_font, ' - '),
                          TextBlock(away_font, away_name),
                         TextBlock(common_font, ' ('),
                          TextBlock(common_font, sport_name),
                         TextBlock(common_font, ')')])
    ws['A1'].value = title
    ws['A1'].alignment = Alignment(horizontal='center')

    full_title = f"{league_name} | {home_name} - {away_name}"
    title_length = len(full_title)
    cell_width = 5
    num_cells_to_merge = (title_length // cell_width) + (title_length // 3)
    ws.merge_cells(start_row=1, start_column=1, end_row=2, end_column=num_cells_to_merge)

    ws['A3'] = f'Начало матча: ' + iso_to_msc(start_time)
    ws['A3'].font = H2
    ws.merge_cells(start_row=3, start_column=1, end_row=4, end_column=num_cells_to_merge)
    ws['A3'].alignment = Alignment(horizontal='center')

    return ws


def create():
    wb = Workbook()
    ws = wb.active

    for sport_folder in DATA_DIR.iterdir():
        for match in sport_folder.iterdir():
            for file in match.iterdir():

                if file.name == 'head.json':
                    with open(file, 'r') as file_io:
                        ws = make_head(ws, file_io)
                        continue

    wb.save(WORK_DIR / 'sample.xlsx')


if __name__ == "__main__":
    create()
