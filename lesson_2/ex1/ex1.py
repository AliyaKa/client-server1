import csv
import re


def get_data():
    # создаем списки
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    main_data = []

    # задаем регулярные выражения
    os_prod_el = re.compile(r'(Изготовитель ОС: .+?)\n')
    os_name_el = re.compile(r'(Название ОС: .+?)\n')
    os_code_el = re.compile(r'(Код продукта: .+?)\n')
    os_type_el = re.compile(r'(Тип системы: .+?)\n')

    # список названия столбцов
    headers = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
    main_data.append(headers)

    # осуществляем в цикле перебор файлов
    for i in range(1, 4):
        f = open(f'info_{i}.txt', encoding='cp1251', errors='ignore')
        data = f.read()
    # извлекаем с помощью регулярных выражений необходимые данные
        os_prod_list.append(os_prod_el.findall(data)[0].split()[2])
        os_name_list.append(' '.join(os_name_el.findall(data)[0].split()[3:5]))
        os_code_list.append(os_code_el.findall(data)[0].split()[2])
        os_type_list.append(os_type_el.findall(data)[0].split()[2])
    for i in range(0, len(os_prod_list)):
        row_data = [os_prod_list[i], os_name_list[i], os_code_list[i], os_type_list[i]]
        main_data.append(row_data)
    return main_data


def write_to_csv(file):
    # записываем данные в файл csv
    main_data = get_data()
    with open(file, 'w', encoding='utf-8') as f:
        f_n_writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        f_n_writer.writerows(main_data)

write_to_csv('data_report.csv')
