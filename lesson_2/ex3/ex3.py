import yaml

data_to_yaml = {
    'item': ['шапка',
             'шарф',
             'варежки'],
    'quantity': 1000,
    'price': {
        'шапка': '1800 ₽',
        'шарф': '3000 ₽',
        'варежки': '1200 ₽'
    }
}
with open('file.yaml', 'w', encoding='utf-8') as file1:
    yaml.dump(data_to_yaml, file1, default_flow_style=False, allow_unicode=True, sort_keys=False)

with open("file.yaml", 'r', encoding='utf-8') as file2:
    data = yaml.load(file2, Loader=yaml.SafeLoader)

print(data_to_yaml==data)
print(data)
