from src.utils.common import calc_coeff, gmt_to_msc


async def collect_straight_content(data: list[dict], header: dict):

    result = []
    for content in data:

        response_date = gmt_to_msc(header.get('Date'))
        w_type = content['type']
        status = content['status']
        period = content['period']

        prices = content['prices']
        total_tmp = []
        for price in prices:
            design = price['designation']
            points = price.get('points')
            coeff = calc_coeff(price['price'])
            total_tmp.append({'design': design, 'points': points, 'coeff': coeff})

        info = {'w_type': w_type, 'status': status, 'period': period,
                'price': total_tmp, 'response_date': response_date}
        result.append(info)
    return result


