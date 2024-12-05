from machine import Pin, I2C
from time import sleep
from pico_i2c_lcd import I2cLcd

# Configuración del LCD
I2C_ADDR = 0x27  
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# Configuración de los LEDs y Zumbador
led_verde = Pin(14, Pin.OUT)
led_rojo = Pin(15, Pin.OUT)
zumbador = Pin(16, Pin.OUT)

# Configuración del Keypad Matricial
key_names = "*7410852#963DCBA"
codigo_correcto = "1234"
intentos = 0
codigo_ingresado = ""

@rp2.asm_pio(set_init=[rp2.PIO.IN_HIGH]*4)
def keypad():
    wrap_target()
    set(y, 0)
    label("1")
    mov(isr, null)
    set(pindirs, 1)
    in_(pins, 4)
    set(pindirs, 2)
    in_(pins, 4)
    set(pindirs, 4)
    in_(pins, 4)
    set(pindirs, 8)
    in_(pins, 4)
    mov(x, isr)
    jmp(x_not_y, "13")
    jmp("1")
    label("13")
    push(block)
    irq(0)
    mov(y, x)
    jmp("1")
    wrap()

for i in range(10, 14):
    Pin(i, Pin.IN, Pin.PULL_DOWN)

def on_keypad_input(sm):
    global codigo_ingresado, intentos
    keys = sm.get()
    while sm.rx_fifo():
        keys = sm.get()
    for i in range(len(key_names)):
        if keys & (1 << i):
            tecla = key_names[i]
            lcd.putstr(tecla)  
            if tecla.isdigit(): 
                codigo_ingresado += tecla
            elif tecla == "#": 
                verificar_codigo(codigo_ingresado)
                codigo_ingresado = ""
            break

sm = rp2.StateMachine(0, keypad, freq=2000, in_base=Pin(10, Pin.IN, Pin.PULL_DOWN), set_base=Pin(6))
sm.irq(on_keypad_input)
sm.active(1)

def verificar_codigo(codigo):
    global intentos
    lcd.clear()
    if codigo == codigo_correcto:
        lcd.putstr("Codigo Correcto!")
        led_verde.on()
        led_rojo.off()
        sleep(2)
        led_verde.off()
        lcd.clear()
        lcd.putstr("Bienvenido!")
    else:
        intentos += 1
        lcd.putstr(f"Incorrecto {intentos}/3")
        led_rojo.on()
        sleep(1)
        led_rojo.off()
        if intentos < 3:
            lcd.clear()
            lcd.putstr("Ingrese codigo:")
        else:
            lcd.clear()
            lcd.putstr("Alarma Activada!")
            zumbador.on()
            sleep(3)
            zumbador.off()
            intentos = 0 
            lcd.clear()
            lcd.putstr("Ingrese codigo:")

# Mostrar mensaje de bienvenida
lcd.putstr("Bienvenido")
sleep(2)
lcd.clear()
lcd.putstr("Ingrese codigo:")

# Mantén el programa corriendo
while True:
    sleep(0.1)
