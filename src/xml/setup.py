import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import (Alignment, Font)
from openpyxl.worksheet.worksheet import Worksheet
from src.utils.common import iso_to_msc
from src.xml.charts import create_line_chart
from src.xml.styles import H2, H1
from components import draw_title
from openpyxl.cell.text import InlineFont
from openpyxl.cell.rich_text import TextBlock, CellRichText

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
FILE_DIR = Path(__file__).resolve().parent
WORK_DIR = FILE_DIR / 'sheets'
WORK_DIR.mkdir(exist_ok=True)


def make_head(ws: Worksheet, file_io):
    obj = json.load(file_io)

    sport_name = obj['sport_name']
    league_name = obj["league_name"]
    home_name = obj["home_name"]
    away_name = obj["away_name"]
    start_time = obj['start_time']

    home_font = InlineFont(rFont='Roboto', sz=20, color='008000')
    away_font = InlineFont(rFont='Roboto', sz=20, color='B22222')
    common_font = InlineFont(rFont='Roboto', sz=20)

    head_title = CellRichText([TextBlock(common_font, league_name),
                               TextBlock(common_font, ' | '),
                               TextBlock(home_font, home_name),
                               TextBlock(common_font, ' - '),
                               TextBlock(away_font, away_name),
                               TextBlock(common_font, ' ('),
                               TextBlock(common_font, sport_name),
                               TextBlock(common_font, ')')])
    time_title = f'Начало матча: {iso_to_msc(start_time)}'

    crds = draw_title(ws,
                      crds=(1, 1),
                      title=head_title,
                      width=20,
                      height=30,
                      font=H1,
                      alignment=Alignment(horizontal='center', vertical='center'),
                      sticky=True,
                      sticky_offset=2)

    crds = draw_title(ws,
                      crds=crds,
                      title=time_title,
                      width=20,
                      height=20,
                      font=H2,
                      alignment=Alignment(horizontal='center', vertical='center'))


def make_content(ws: Worksheet, file_io):
    obj = json.load(file_io)
    content = obj['content']
    print(content)
    for data in content:
        if data['w_type'] == "moneyline":
            ws['A5'] = f'MoneyLine Тайм - {data["period"]}'
            ws.merge_cells(start_row=5, start_column=1, end_row=6, end_column=5)
            ws['A5'].font = H2
            ws['A3'].alignment = Alignment(horizontal='center', vertical='center')
            for price in data['price']:
                if price['design'] == 'home':
                    pass
                else:
                    pass
                print(price)


def create():
    wb = Workbook()
    ws = wb.active

    for sport_folder in DATA_DIR.iterdir():
        for match in sport_folder.iterdir():
            for file in match.iterdir():
                if file.name == 'head.json':
                    with open(file, 'r') as file_io:
                        make_head(ws, file_io)
                    d1 = {'home': {'name': 'Aquila Basket Trento', 'values': [1.96, 1.54, 2.98, 1.67, 2.78, 1.45, 2.08, 1.02, 2.35, 1.13]}, 'away': {'name': 'Scaligera Basket Verona', 'values': [1.85, 2.38, 1.26, 1.50, 1.88, 2.11, 1.63, 2.25, 2.74, 1.90]}}
                    d2 = {'home': {'name': 'Aquila Basket Trento', 'values': [1.21, 2.03, 1.75, 2.02, 2.66, 1.87, 1.24, 2.44, 1.67, 2.43]}, 'away': {'name': 'Scaligera Basket Verona', 'values': [1.83, 1.56, 2.34, 1.48, 2.22, 1.91, 2.89, 2.35, 1.99, 1.98]}}
                    h1 = ['20:00', '21:00', '22:00', '23:00', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00']
                    h2 = ['21:00', '22:00', '23:00', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00']
                    create_line_chart(ws=ws, dates=h1, data=d1, crds=(1, 5), title='MoneyLine - Игра')
                    create_line_chart(ws=ws, dates=h2, data=d2, crds=(1, 28), title='MoneyLine - 1-й Тайм')

                    break
    wb.save(WORK_DIR / 'sample.xlsx')


if __name__ == "__main__":
    create()
