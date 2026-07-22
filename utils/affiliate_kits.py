"""
Single source of truth for KidsCode's Amazon Associates kit links.

Each project's META can set 'required_kits' to one of the lists below (or a
custom combination). Update a URL here once and every project referencing it
picks up the change — never hardcode these links directly in a template or
project_*.py file.
"""

UNO_KIT = {
    'emoji': '🟦',
    'name': 'Arduino UNO',
    'button_label': 'Arduino UNO board',
    'url': 'https://www.amazon.ca/Elegoo-Board-ATmega328P-ATMEGA16U2-Arduino/dp/B01EWOE0UU?crid=3GLAQO7GR4V89&dib=eyJ2IjoiMSJ9.MazmhFfn-DF8W5oyX_S-tDFAqLRDaMJSkroaZhdQMdjgp7pw-zFOOb8_l9DBkr96eO-NCEA_5az_itPhaeCnFMklbh-z2dfkw0mHhlDrPbqGl-xVJq3lpVcbtJsG4mbGGJijW9mDWsYq5LwSDE3LOyP-U47kjZw_tN1ygFD7bFPCP6d0PI4pJZKTG0eHdchex52nXlyKfEpq5A62Ob3uTQvVb6J0YK6R9aq3Z-fRuVNp46rompDjAMuD7VG8q_WENYSaEJeSoOcH-urdWnAH0ch7KUEoXQN-wXVeHlg4tlw.Jt34XcdEwD9ENEFEv_XKjsubN-lQSaaAVi6ScizpmYQ&dib_tag=se&keywords=arduino+uno+r3&qid=1783907794&sprefix=arduino+uno+r3%2Caps%2C150&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1&linkCode=ll2&tag=kidscode-20&linkId=c0c16d53980692c0b71de6f30a3c466c&ref_=as_li_ss_tl',
}

STARTER_KIT = {
    'emoji': '🧰',
    'name': 'Starter Kit',
    'button_label': 'Starter Kit (breadboard, resistors, LEDs, buttons, buzzer, wires)',
    'url': 'https://www.amazon.ca/Breadboard-Electronics-Component-Starter-Arduino/dp/B0F93S2RWW?crid=2RCMPGU93ZQWI&dib=eyJ2IjoiMSJ9.AcWZy-Yg4mDTnhzEHozxzIDnH5oCBatxHsbP1dDaLRLSTC4JgJDXsPav0St_4UMYnW55OcApuQxJtb_M5yFuh_x8pyVBY_LOgZiYbN2wv2lLLf4GC8eOKvnGFrYhtUXjEdMMtF8GTnKiPLdx1NufXgbjcp9EPpiwLoVfaghv8Gsw93Ik5FxcxNLlkvi_O69nqbnQp9xxHvO3GQMJbz7lgds-51jcAyEn0a-qzQJ8vRSuvmbn2p1tiyY-fNuMdZyfkw5Z0ROhE-A-R5AA2-sVJvEjgwOS3Q20PdjBsmkqPcw.hI6vGMBANeTXJB2HLUnyif5iqbYF9tllL8IaRNXlA2U&dib_tag=se&keywords=arduino+starter+kit+with+switch&qid=1783906782&sprefix=arduino+starter+kit+with+switch%2Caps%2C152&sr=8-36&linkCode=ll2&tag=kidscode-20&linkId=75ae6a59dd80462d10aa60674e655971&ref_=as_li_ss_tl',
}

# Not yet assigned to any project — staged for the sensor-pack rollout (projects
# fifteen, seventeen, eighteen need SONAR_SENSOR; nineteen needs SERVO_MOTOR).
SONAR_SENSOR = {
    'emoji': '📡',
    'name': 'Sonar Sensor',
    'button_label': 'HC-SR04 Ultrasonic Sensor',
    'url': 'https://www.amazon.ca/HC-SR04-Ultrasonic-Distance-Arduino-MEGA2560/dp/B01COSN7O6?crid=3SYNI4Y13Y1QM&dib=eyJ2IjoiMSJ9.3UqbhKzKFDOOqP9YI3z6z9eDjuGabbKNgavYusav3oJx8DM2oq1D0E2z9CAMmsLh5glWy8VNf0W45DcOxZrjqz9gPz-mHdB5kNCOrH4hhytz9zwx0ssbDGSBYuwJGNtsopWZTc2I9memWkp17ZSf2mdqIv33NFozalg69fppPwV-R-AGuHTXTIWme35RGQKOD7rPoZiFN9WIzgl2J-JpngOCgovFSvix1FaSyGrOMJquJODe9AcHai7lrruVoEH1_s2z7PJQEMDy2MA4GTz9E03GORIcGqUccN3CY35rlh8.paPFFDZ7TVrzqkZ5svivDYT5oBe8ePwCPJch4KNAnU8&dib_tag=se&keywords=sonar+sensor+arduino&qid=1783908452&sprefix=sonar+sensor+arduino%2Caps%2C133&sr=8-2-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&psc=1&linkCode=ll2&tag=kidscode-20&linkId=260c148c36b15d405f0cf9ee6dc25b8b&ref_=as_li_ss_tl',
}

SERVO_MOTOR = {
    'emoji': '⚙️',
    'name': 'Servo Motor',
    'button_label': 'SG90 Servo Motor',
    'url': 'https://www.amazon.ca/ALMOCN-Helicopter-Airplane-Controls-Project/dp/B09CGYX76S?crid=2ZOP2SNXRKXE9&dib=eyJ2IjoiMSJ9.c45rmcMo5Hhg7RdSndIfnyycpn56U9NM6nkTrQxcakHRxXYcHQf8JSPv8VLEycV7RC0SyrK_rOOFpwWJiWJI0MhyPuKjWMK4Vo0T-dOsuu1S1hwlb0EhqIwtuGmll0H0OLzIBwt7LuNuvnMQl8uto5nR7xxAPYnBlZztjRug1iCBaL3TvZka-uaPhJU-dwdFZj0vrYD0BDJ2UdpVDc1p8NVq8ezzcLDoog_qbu--mXGSs8dgYaVd2XQYM8Vyeet6XrSxW25v71i6CiRcm3-PSjy5cLVK1s_dG9C8_I-m04Y._jDnZR_X73pZAfZms_kn4Mdlqni8zjK52GabZrAR55o&dib_tag=se&keywords=arduino%2Bservo&qid=1783908534&sprefix=arduino%2Bservo%2Caps%2C153&sr=8-7&th=1&linkCode=ll2&tag=kidscode-20&linkId=133eeb3412925cd7c1200d03267225c9&ref_=as_li_ss_tl',
}

UNO_ONLY_KIT = [UNO_KIT]
BASIC_KITS = [UNO_KIT, STARTER_KIT]
SONAR_KIT = [UNO_KIT, STARTER_KIT, SONAR_SENSOR]
SERVO_KIT = [UNO_KIT, STARTER_KIT, SERVO_MOTOR]
