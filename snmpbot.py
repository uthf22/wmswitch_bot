import os
import nmap
import time
import asyncio
import logging
import telnetlib
from aiogram import F
import mysql.connector
from aiogram.types import Message
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from datetime import datetime
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Включаем логирование
logging.basicConfig(level=logging.INFO)
bot = Bot(token="7264282145:AAEDtNWQRjufApBDSn-ZPjP0w_Sn6Co7gM8")
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
ints = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28']
temp_switch_ip = str()
is_testing_port = False
is_testing_cable = False

#KEYBOARD
builder = InlineKeyboardBuilder()
builder.add(
    #types.InlineKeyboardButton(text="линк свитча", callback_data="btn1_link_pressed"),
    types.InlineKeyboardButton(text="порты", callback_data="btn2_ports_pressed"),
    types.InlineKeyboardButton(text="тест порта", callback_data="btn3_port_pressed")
    )
builder.add(types.InlineKeyboardButton(text="тест кабеля", callback_data="btn4_cabletest_pressed"))

#FUNCTIONS
def nmap_scan(switch_ip):   #проверка на онлайн свитча
    nm = nmap.PortScanner()
    link = os.popen(f"nmap -sn {switch_ip}").read().split("\n")[2][8:10]
    if link == "up":
        return "ONLINE"+"\U0001f7e2\ufe0f"
    if link == "down":
        return "OFFLINE"+"\U0001f534\ufe0f"

def ports_scan(switch_ip):  #показать скорость линка всех портов
    links = os.popen(f"snmpwalk -v2c -c54zxcGFS12Cd {switch_ip} 1.3.6.1.2.1.2.2.1.5").read().split('\n')
    answer = f"SWITCH {switch_ip}\n"
    count = 0
    
    for i in links:
        if count <= 27:
            try:
                count += 1
                if len(i.split(' ')[3]) == 1:
                    answer += f"Port {count}: down"+"\U0001f534\ufe0f\n"
                if len(i.split(' ')[3]) == 8:
                    answer += f"Port {count}: 10mb"+"\U0001f7e0\ufe0f\n"
                if len(i.split(' ')[3]) == 9:
                    answer += f"Port {count}: 100mb"+"\U0001f7e2\ufe0f\n"
                if len(i.split(' ')[3]) == 10:
                    answer += f"Port {count}: 1gb"+"\U0001f7e2\ufe0f\n"
            except:
                print("pohui")

    return answer

def test_port(switch_ip, port): #фокус на одном порте, 50 прозвонов
    link = os.popen(f"snmpwalk -v2c -c54zxcGFS12Cd {switch_ip} 1.3.6.1.2.1.2.2.1.5.{port}").read().split(' ')[3].split('\n')[0]
    x = 30  #Кол-во итераций
    answer = str()

    for i in range(x):
        if len(link) == 1:
            answer += f"down"+"\U0001f534\ufe0f\n"
            time.sleep(0.3)
        if len(link) == 8:
            answer += f"10mb"+"\U0001f7e0\ufe0f\n"
            time.sleep(0.3)
        if len(link) == 9:
            answer += f"100mb"+"\U0001f7e2\ufe0f\n"
            time.sleep(0.3)
        if len(link) == 10:
            answer += f"1gb"+"\U0001f7e2\ufe0f\n"
            time.sleep(0.3)
        
    return answer

def test_cable(switch_ip, port):    #тест кабеля на порту
    tn = telnetlib.Telnet(switch_ip, 23)

    tn.read_until(b'UserName:', 1)
    input = f'0964-qadm\n'
    tn.write(bytes(input, 'utf-8'))

    tn.read_until(b'PassWord:', 1)
    input = f'0964-qadm\n'
    tn.write(bytes(input, 'utf-8'))

    tn.read_until(b'UserName:', 1)
    input = f'0964-qadm\n'
    tn.write(bytes(input, 'utf-8'))

    tn.read_until(b'PassWord:', 1)
    input = f'0964-qadm\n'
    tn.write(bytes(input, 'utf-8'))

    input = f'cable_diag ports {port}\n'
    tn.write(bytes(input, 'utf-8'))
    time.sleep(0.3)

    
    result = f"{tn.read_very_eager().decode('utf-8')[107:-12]}"
    return result

def fin_output(locate_id, switch_location, switch_ip, street, switch_digit, type_id, switch_type):  #финальный вывод свитча
    answer = str()

    #добавляем ip, адрес, модель
    answer += f"ip: {switch_ip}\nadres: {street}, {switch_digit}\nмодель: {type_id[switch_type]}"

    try:    #Пробуем добавить аптайм
        switch_uptime = os.popen(f"snmpwalk -v2c -c54zxcGFS12Cd {switch_ip} uptime").read().split(' ')
        answer += f"\nВ сети: {switch_uptime[4]} дней, {switch_uptime[6]}"
    except:
        print(f"NO UPTIME #2 | switch:{switch_ip}")

    try:    #Пробуем добавить локацию
        answer+=f"{locate_id[switch_location]}\n"
    except:
        print(f"NO LOCATION #1 | switch:{switch_ip}")

    return answer



# HANDLERS
# Хэндлер на команду /start (здоровается по имени юзера)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Hello, <b>{message.from_user.full_name}</b>",
        parse_mode=ParseMode.HTML
    )

# Команда /info выводит время запуска бота
@dp.message(Command("info"))
async def cmd_info(message: types.Message, started_at: str):
    await message.answer(f"Бот запущен {started_at}")

# Показывает написание всех улиц
@dp.message(Command("streets"))
async def cmd_streets(message: types.Message):
    cnx = mysql.connector.connect(user="J7pHaWULeEj33cbB",
                                host="192.162.9.76",
                                database='metro_db',
                                password='K47bVd8u7nCBjzv8')
    cursor = cnx.cursor()
    query = ("SELECT street_name FROM bld_street")
    cursor.execute(query)
    for street in cursor:
        await message.answer(f"{street}")

# Хэндлер на первую кнопку (линк свитча)
@dp.callback_query(F.data == "btn1_link_pressed")
async def switch_link_test(callback: types.CallbackQuery):
    sw_ip = callback.message.text.split('\n')[0].split(' ')[1]  #вычленяем ip свитча из сообщения
    await callback.message.answer(nmap_scan(sw_ip))

# Хэндлер на вторую кнопку (линки на всех портах)
@dp.callback_query(F.data == "btn2_ports_pressed")
async def switch_ports_test(callback: types.CallbackQuery):
    sw_ip = callback.message.text.split('\n')[0].split(' ')[1]  #вычленяем ip свитча из сообщения
    await callback.message.answer(ports_scan(sw_ip))

# Хэндлер на третью кнопку (тест линка на порту)
@dp.callback_query(F.data == "btn3_port_pressed")
async def switch_ports_test(callback: types.CallbackQuery):
    global temp_switch_ip
    global is_testing_port
    global is_testing_cable

    is_testing_port = True
    is_testing_cable = False
    temp_switch_ip = callback.message.text.split('\n')[0].split(' ')[1]  #вычленяем ip свитча из сообщения
    await callback.message.answer("Введите порт: ")

# Хэндлер на четвертую кнопку (тест кабла)
@dp.callback_query(F.data == "btn4_cabletest_pressed")
async def switch_cable_test(callback: types.CallbackQuery):
    global temp_switch_ip
    global is_testing_port
    global is_testing_cable

    is_testing_port = False
    is_testing_cable = True
    temp_switch_ip = callback.message.text.split('\n')[0].split(' ')[1]  #вычленяем ip свитча из сообщения
    await callback.message.answer("Введите порт: ")

# хэндлер на любое слово (на адрес)
@dp.message(F.text)
async def any_message(message: Message):
    if len(message.text.split(' ')) == 1 and message.text in ints:
        port = message.text

        if is_testing_port == True: #передаем порт в функцию для теста порта
                link = os.popen(f"snmpwalk -v2c -c54zxcGFS12Cd {temp_switch_ip} 1.3.6.1.2.1.2.2.1.5.{port}").read().split(' ')[3].split('\n')[0]
                x = 30  #Кол-во итераций
                answer = str()

                for i in range(x):
                    if len(link) == 1:
                        answer = f"down"+"\U0001f534\ufe0f\n"
                        time.sleep(0.3)
                        await message.answer(answer)
                    if len(link) == 8:
                        answer = f"10mb"+"\U0001f7e0\ufe0f\n"
                        time.sleep(0.3)
                        await message.answer(answer)
                    if len(link) == 9:
                        answer = f"100mb"+"\U0001f7e2\ufe0f\n"
                        time.sleep(0.3)
                        await message.answer(answer)
                    if len(link) == 10:
                        answer = f"1gb"+"\U0001f7e2\ufe0f\n"
                        time.sleep(0.3)
                        await message.answer(answer)
                        
        if is_testing_cable == True:    #передаем порт в функцию для теста кабеля
            await message.answer(test_cable(temp_switch_ip, port))

    else:   #ввод адреса или улицы для поиска комма
        #Коннектимся
        cnx = mysql.connector.connect(user="J7pHaWULeEj33cbB",
                                        host="192.162.9.76",
                                        database='metro_db',
                                        password='K47bVd8u7nCBjzv8')
        cursor = cnx.cursor()

        #готовим список с улицами
        query = ("SELECT street_id, street_name FROM bld_street")
        cursor.execute(query)
        st_id = dict()  #Список айди уллицы/ наименование улицы
        for (street_name, street_id) in cursor:
            st_id[street_id] = street_name

        #готовим список с расположением свитчей в доме
        query = ("SELECT bldloc_id, bldloc_place FROM bld_locations")
        cursor.execute(query)
        locate_id = dict()  #Список (айди локации/ локация)
        for (location_id, location) in cursor:
            locate_id[location_id] = location

        #готовим список с моделями коммутаторов
        query = ("SELECT comtype_id, com_type_dev FROM a_comm_type")
        cursor.execute(query)
        type_id = dict()    #Список айди типа коммутатора/ тип коммутатора
        for (com_type_id, com_type) in cursor:
            type_id[com_type_id] = com_type

        if len(message.text.split(" ")) == 2:   #Если введена УЛИЦА и НОМЕР
            street = message.text.split(' ')[0]
            street_num = int(message.text.split(' ')[1])
            print(f'Улица: {street}, Номер: {street_num}')

            street_ready = st_id[street.capitalize()]   #Улица

            #ищем коммут
            query = ("SELECT com_ip, com_street, com_bld_digit, com_bld_loc, com_type FROM a_comms")
            cursor.execute(query)

            for (switch_ip, switch_street, switch_digit, switch_location, switch_type) in cursor:
                if street_ready == switch_street:
                    if street_num == switch_digit: 
                        await message.answer(fin_output(locate_id, switch_location, switch_ip, street, switch_digit, type_id, switch_type), reply_markup=builder.as_markup())

            
            cursor.close()
            cnx.close()

        elif len(message.text.split(" ")) == 1: #Если введена только УЛИЦА
            street = message.text.split(' ')[0]
            print(f'Улица: {street}')

            street_ready = st_id[street.capitalize()]   #Улица

            #ищем коммут
            query = ("SELECT com_ip, com_street, com_bld_digit, com_bld_loc, com_type FROM a_comms")
            cursor.execute(query)

            for (switch_ip, switch_street, switch_digit, switch_location, switch_type) in cursor:
                if street_ready == switch_street:
                        await message.answer(fin_output(locate_id, switch_location, switch_ip, street, switch_digit, type_id, switch_type), reply_markup=builder.as_markup())
            
            cursor.close()
            cnx.close()

        else:                                   #Если чота не так )
            await message.answer("Ошибка №1448")



# POLLING AND UPDATES
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())