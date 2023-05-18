import locale
import subprocess

import chardet

print('\nЗадание № 1')

str_list = ['разработка', 'сокет', 'декоратор']
print('\nСтроковый формат:')
for el in str_list:
    print(f'тип: {type(el)}, содержимое: {el}')

unicode_list = [
    '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430',
    '\u0441\u043e\u043a\u0435\u0442',
    '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'
]
print('\nФормат Unicode:')
for el in unicode_list:
    print(f'тип: {type(el)}, содержимое: {el}')

print('\nЗадание № 2')

byte_list = [b'class', b'unicode', b'method']
for el in byte_list:
    print(f'тип: {type(el)}, содержимое: {el}, длина: {len(el)}')

print('\nЗадание № 3')

str_list = ['attribute', 'класс', 'функция', 'type']
print('\nСлова, которые не возможно записать в байтовом типе:')
for el in str_list:
    el_encode = el.encode('ascii', errors='ignore')
    if el_encode == b'':
        print(f'{el}')

print('\nЗадание № 4')

str_list = ['разработка', 'администрирование', 'protocol', 'standard']
for el in str_list:
    el_encode = el.encode('ascii', errors='ignore')
    print(ascii(el_encode), type(el_encode))
    el_decode = el_encode.decode('ascii', errors='ignore')
    print(ascii(el_decode), type(el_decode))


print('\nЗадание № 5')

# args = ['ping', 'yandex.ru']
# subproc_ping = subprocess.Popen(args, stdout=subprocess.PIPE)
# for line in subproc_ping.stdout:
#     result = chardet.detect(line) # определим кодировку строки
#     line = line.decode(result['encoding']).encode('utf-8') # выполняем обратное  преобразование
#                                                            # из строки в байты в кодировке utf-8
#     print(line.decode('utf-8')) # преобразуем байты в строку в кодировке utf-8

print('\nЗадание № 6')

def_coding = locale.getpreferredencoding()
print(f'Кодировка по умолчанию:{def_coding}\n')
with open('test_file.txt', encoding='utf-8') as f:
    for elem in f:
        el_encode = elem.encode('utf-8')
        el_decode = el_encode.decode('utf-8')
        print(el_decode, end='')
