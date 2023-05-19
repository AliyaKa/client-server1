import json


def write_order_to_json(item, quantity, price, buyer, date):

    with open('orders.json', 'r', encoding='utf-8') as file_read:
        objs = json.load(file_read)

    with open('orders.json', 'w', encoding='utf-8') as file_write:
        order_row = {'item': item,
                     'quantity': quantity,
                     'price': price,
                     'buyer': buyer,
                     'date': date}
        orders_objs = objs['orders']
        orders_objs.append(order_row)
        json.dump(objs, file_write, indent=4, ensure_ascii=False)


write_order_to_json('шапка', '5', '5000', 'Епифанова А.Н.', '13.01.2023')
write_order_to_json('шарф', '1', '3000', 'Калимуллина А.Р.', '14.02.2023')
write_order_to_json('варежки', '2', '4000', 'Макарова Е.В.', '08.01.2023')
