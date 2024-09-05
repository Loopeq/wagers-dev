import json
from src.utils.common import gmt_to_msc


def period_corrector(title: str, period: int) -> str:
    if period == 0:
        prefix = 'Игра'
    else:
        prefix = f'{period} Тайм'
    total = f'{title.title()} - {prefix}'
    return total


def reforge(file_io) -> tuple:
    objs = json.load(file_io)
    dates = []
    var = {'moneyline': {}, 'total': {}, 'spread': {}, 'team_total': {}}
    for obj in objs:

        response_date = obj.get('response_date')
        response_date = gmt_to_msc(response_date)
        dates.append(response_date)

        for content in obj['content']:
            content_type = content['w_type']
            period = content['period']
            prices = content['price']
            for index, price in enumerate(prices):
                if var[content_type].get(period):
                    if var[content_type][period].get(price['design']):
                        if price.get('points'):
                            if var[content_type][period][price['design']].get(price['points']):
                                var[content_type][period][price['design']][price['points']].append(price['coeff'])
                            else:
                                var[content_type][period][price['design']][price['points']] = [price['coeff']]
                        else:
                            var[content_type][period][price['design']].append(price['coeff'])
                    else:
                        if price.get('points'):
                            var[content_type][period][price['design']] = {price['points']: [price['coeff']]}
                        else:
                            var[content_type][period][price['design']] = [price['coeff']]
                else:
                    if price.get('points'):
                        var[content_type][period] = {price['design']: {price['points']: [price['coeff']]}}
                    else:
                        var[content_type][period] = {price['design']: [price['coeff']]}
    return var, dates
