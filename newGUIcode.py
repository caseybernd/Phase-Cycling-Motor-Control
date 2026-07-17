from nicegui import ui
import time
import serial
import serial.tools.list_ports
import numpy as np


#debugging code

import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
for p in ports:
    print(p)


def open_serial_port(port, baudrate, timeout=1):
    while True:
        try:
            ser = serial.Serial(port, baudrate, timeout=timeout)
            print(f"Successfully connected to {port}")
            return ser
        except serial.SerialException as e:
            print(f"Error opening {port}: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(port.device)

# List available ports for debugging
print("Available ports:")
list_serial_ports()

# Attempt to open COM5 with a baud rate of 115200
serial_port = 'COM3'
baud_rate = 115200


ser = open_serial_port(serial_port, baud_rate)
ser.write(bytes(f'M92 Y16\n', encoding='utf-8'))  # send command for steps per gcode unit (M502 for reset to default) look at M350 for microstep control
print(bytes(f'M92 Y16\n', encoding='utf-8'))  # 16 microsteps per unit. 16 microsteps in one step. Now 1 step is 1 unit. 400 steps per revolution, 0.9 degrees
ser.write(bytes(f'G1 F38400\n', encoding='utf-8'))  # Send the command to set motor step rate in steps/second?
print(bytes(f'G1 F38400\n', encoding='utf-8'))
#print(ser.readline().decode('utf-8').strip())
ser.close()


stepsize = 0.9 #degrees
stepsPerRev = 360/stepsize

# gear ratio 24:30, 30 rotations of motor to 24 rotations of micrometer
revPerMeter = 600000 #unknown until gear ratio and everything built

#50 um per rev of micrometer usually, 0.000050 m per rev
#30 motor revs per rev of micrometer with worm gear
# 30 motor rev per micrometer rev * 1 micrometer rev per 0.000050 m = 600,000 motor revs per meter of platform movement = 1,200 rev per mm = 1.2 rev per um


currentPos = None
stepsTaken = None



    
def send_step_pulse(steps):
    # code block to send gcode command to motherboard
    global ser
    global serial_port
    global baud_rate
    global stepsTaken
    stepsTaken = 0
    print('step pulse command received')
    ser = open_serial_port(serial_port, baud_rate)
    print('attempting {steps} step pulse')
    ser.write(bytes(f'G90\n', encoding='utf-8')) #specify using absolute coordinates
    ser.write(bytes(f'G0 Y-{steps}\n', encoding='utf-8'))  # Send the command to generate a step pulse. 
    print(bytes(f'G0 Y-{steps}\n', encoding='utf-8'))
    ser.close()
    stepsTaken = steps
    getCurrentPos()


def getCurrentPos():
    global serial_port
    global baud_rate
    global currentPos
    global stepsPerRev
    global revPerMeter
    global posLabel
    global stepsTaken
    ser = open_serial_port(serial_port, baud_rate)
    ser.write(bytes(f'M114\n', encoding='utf-8'))
    y_current_value = None
    while True:
        line = ser.readline().decode('utf-8').strip()
        if 'Y:' in line:
            y_current_value = line.split('Y:')[1].split()[0]
            print(y_current_value)
            break
    currentPos = float(y_current_value) / stepsPerRev /revPerMeter
    print(currentPos)
    ser.close()
    mmPosString = f'{round(currentPos*1000,6)} mm from zero'
    print(mmPosString)
    with posLabel:
        posLabel.clear()
        ui.label(mmPosString)
        ui.label(f'{stepsTaken} steps taken this move.')



def laserCheck():
    # look at M119, M120, M121
    global laserBlocked
    global ser
    ser.write(bytes(f'M119\n', encoding='utf-8'))  # Send the command to report endstop status
    y_min_value = None
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line.startswith('y_min:'):
            y_min_value = line.split(': ')[1]
            break
    if y_min_value is not None:
        print(f"y_min value: {y_min_value}")

    if y_min_value == 'TRIGGERED':
        laserBlocked = True
    else:
        laserBlocked = False



def laserChecker():
    global serial_port
    global baud_rate
    global ser
    ser = open_serial_port(serial_port, baud_rate)
    print("after port opening in laserChecker()")
    for i in range(100):
        laserCheck()
        time.sleep(0.2)
    ser.close()


def backToZero():
    global serial_port
    global baud_rate
    global laserBlocked
    global ser
    laserBlocked = False
    # look at G28, G60, G90, G91, G92
    ser = open_serial_port(serial_port, baud_rate)
    #ser.write(bytes(f'G28 Y\n', encoding='utf-8'))  # Send the command to home Y axis
    #print(bytes(f'G28 Y\n', encoding='utf-8'))
    ser.write(bytes(f'G91\n', encoding='utf-8'))  # Send the command to change to relative coordinate system
    laserCheck()
    print(laserBlocked)
    print("zero working?")
    while laserBlocked == False:
        ser.write(bytes(f'G0 Y10\n', encoding='utf-8'))
        print(bytes(f'G0 Y10\n', encoding='utf-8'))
        laserCheck()
    

    ser.write(bytes(f'G90\n', encoding='utf-8'))  # Send the command to change to absolute coordinate system
    print(bytes(f'G90\n', encoding='utf-8'))
    ser.write(bytes(f'G92 Y0\n', encoding='utf-8'))  # Send the command to set 0 position
    print(bytes(f'G92\n', encoding='utf-8'))
    ser.close()
    global currentPos 
    currentPos = 0
    print(f'Current Position is {round(currentPos*1000,6)} mm from zero')
    getCurrentPos()


maxMovement = 0.050 #meters, need to measure
def set(frequency, phase):
    global currentPos

    if phase < 0:
        phase += 360

    #calculate necessary steps to send
    inputWavelength = 2.9979*10**8/(frequency*10**9)
    distancePerDegree = inputWavelength / 360
    moveDistance = phase * distancePerDegree

    steps = moveDistance * revPerMeter * stepsPerRev

    #for time of movement calculations
    getCurrentPos()
    stepsToGo = np.abs((moveDistance - currentPos) * revPerMeter * stepsPerRev)


    with containerBelowSet:
        if list(containerBelowSet) or list(containerAboveSet):
            containerBelowSet.clear()
            containerAboveSet.clear()
        with ui.row():
            ui.label('Set')
            ui.icon('check')
            ui.label(f'Performing {round(stepsToGo,1)} steps, or {round(stepsToGo/stepsPerRev,2)} revolutions, taking about {round(stepsToGo/stepsPerRev*6.2,0)} seconds')
    
    with containerAttemptedInput:
        if list(containerAttemptedInput):
            containerAttemptedInput.clear()
        with ui.row():
            ui.label(str(frequency) + ' GHz at ' + str(phase) + ' degrees')



    if moveDistance+currentPos < maxMovement:
        send_step_pulse(steps)
        getCurrentPos()
    else:
        with containerAboveSet:
            if list(containerAboveSet) or list(containerBelowSet):
                containerAboveSet.clear()
                containerBelowSet.clear()
            ui.label('Invalid input, outside physical bounds of system.')
        with containerBelowSet:    
            with ui.row():
                ui.label('Set')
                ui.icon('X')




def newInput():
    with containerAboveSet:
        if list(containerBelowSet) or list(containerAboveSet):
            containerBelowSet.clear()
            containerAboveSet.clear()
        ui.label('Awaiting new input...')

def stopMovement():
    global serial_port
    global baud_rate
    ser = open_serial_port(serial_port, baud_rate)
    ser.write(bytes(f'M410\n', encoding='utf-8'))
    ser.close()



def fineAdjustment(input):
    global serial_port
    global baud_rate
    ser = open_serial_port(serial_port, baud_rate)
    ser.write(bytes(f'G91\n', encoding='utf-8'))
    if input > 0:
        print('increase by 1 step')
        ser.write(bytes(f'G1 Y1\n', encoding='utf-8'))
    else:
        print('decrease by 1 step')
        ser.write(bytes(f'G1 Y-1\n', encoding='utf-8'))
    ser.close()
    getCurrentPos()



with ui.card():
    ui.label('Stepper Motor 1')
    with ui.column():
        with ui.row():
            with ui.card():
                moveValue = ui.number(label='Move Position', format='%.10f')
                ui.button('Move', on_click=lambda: send_step_pulse(moveValue.value))
            with ui.card():
                ui.label('Fine Adjustment (1 step)')
                with ui.button_group():
                    ui.button('+', on_click=lambda: fineAdjustment(1))
                    ui.button('-', on_click=lambda: fineAdjustment(-1))
        with ui.row():
            with ui.card():
                ui.label('Frequency (GHz)')
                frequency = ui.number(label='Frequency (GHz)', format='%.10f', min=0, on_change=lambda: newInput())

            with ui.card():
                ui.label('Phase Difference (Degrees)')
                phase = ui.number(label='Phase Difference (Degrees)', format='%.10f',  min=-180, on_change=lambda: newInput())

        with ui.row():
            with ui.card():
                containerAboveSet = ui.column()
                ui.button('Set', on_click=lambda: set(frequency.value,phase.value))
                containerBelowSet = ui.column()
                ui.button('Zero', on_click=lambda: backToZero())
                ui.button('Stop Move', on_click=lambda: stopMovement())
            

            with ui.card():
                with ui.row():
                    ui.label('Current Input:')
                    posLabel = ui.column()
                with ui.row():
                    ui.label('Attempted Input:')
                    containerAttemptedInput = ui.column()

                

ui.run() #evaluates the code twice