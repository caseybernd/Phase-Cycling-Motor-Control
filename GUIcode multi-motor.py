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
serial_port = 'COM5'
baud_rate = 19200 #115200
stepsPerMin = 19200


ser = open_serial_port(serial_port, baud_rate)
ser.write(bytes(f'M92 Y8 Z8 A16 B16 C16\n', encoding='utf-8'))  # send command for steps per gcode unit (M502 for reset to default) look at M350 for microstep control
ser.write(bytes(f'M350 Y8 Z8 A8 B8 C8\n', encoding='utf-8'))
print(bytes(f'M92 Y8 Z8 A16 B16 C16\n', encoding='utf-8'))  # 16 microsteps per unit. 16 microsteps in one step. Now 1 step is 1 unit. 400 steps per revolution, 0.9 degrees
print(bytes(f'M350 Y8 Z8 A8 B8 C8\n', encoding='utf-8'))
ser.write(bytes(f'G1 F{stepsPerMin}\n', encoding='utf-8'))  # Send the command to set motor step rate in steps/minute
print(bytes(f'G1 F{stepsPerMin}\n', encoding='utf-8'))
ser.write(bytes(f'M211 S0\n', encoding='utf-8')) #disables software endstops, not working?
print(bytes(f'M211 S0\n', encoding='utf-8'))
ser.write(bytes(f'G91\n', encoding='utf-8')) #specify using relative coordinates
print(bytes(f'G91\n', encoding='utf-8'))
#print(ser.readline().decode('utf-8').strip())
ser.close()

'''''''''
stepsize = 0.9 #degrees
stepsPerRev = 360/stepsize

# gear ratio 24:30, 30 rotations of motor to 24 rotations of micrometer
revPerMeter = 600000 #unknown until gear ratio and everything built
'''''''''
# optical path length movement per motor step experimentally determined to be 1.437*10^-7 m/step
meterPerStep = 1.437*10**(-7)

#50 um per rev of micrometer usually, 0.000050 m per rev
#30 motor revs per rev of micrometer with worm gear
# 30 motor rev per micrometer rev * 1 micrometer rev per 0.000050 m = 600,000 motor revs per meter of platform movement = 1,200 rev per mm = 1.2 rev per um


currentPos = [0, 0]
stepsTakenFromZero = [0, 0, 0, 0, 0]

motorsList = ["Y", "Z", "A", "B", "C"]
laserBlocked = [False, False, False, False, False]



    
def send_step_pulse(steps, motor):
    # code block to send gcode command to motherboard
    global ser
    global serial_port
    global baud_rate
    global stepsTakenFromZero
    #steps = -steps
    print('step pulse command received')
    ser = open_serial_port(serial_port, baud_rate)
    print(f'attempting {steps} step pulse')
    ser.write(bytes(f'G0 {motorsList[motor]}{steps}\n', encoding='utf-8'))  # Send the command to generate a step pulse to stepper motor specified
    print(bytes(f'G0 {motorsList[motor]}{steps}\n', encoding='utf-8'))
    #stepsTakenFromZero[motor] -= steps
    stepsTakenFromZero[motor] += steps
    ser.close()
    print(stepsTakenFromZero)
    #getCurrentPos()

def rotateSlicer(status, motor): #has to rotate incredibly slowly, otherwise the silicon will fall off. modify time.sleep()?
    global ser
    global serial_port
    global baud_rate
    print(f"Attempting rotation of motor {motor}")
    ser = open_serial_port(serial_port, baud_rate)
    if status == "on":
        ser.write(bytes(f'G0 {motorsList[motor+1]}100 F1000\n', encoding='utf-8'))
        print(f'G0 {motorsList[motor+1]}100 F1000\n')
    if status == "off":
        ser.write(bytes(f'G0 {motorsList[motor+1]}-100 F1000\n', encoding='utf-8'))
        print(f'G0 {motorsList[motor+1]}-100 F1000\n')
    readLines()
    ser.close()

    '''
    delay = 0.5
    if status == "on":
        while True:
            ser = open_serial_port(serial_port, baud_rate)
            laserCheck()
            ser.close()
            time.sleep(delay/2)
            print(laserBlocked)
            if laserBlocked[motor + 1] == False:
                break
            send_step_pulse(1, motor + 1)
            time.sleep(delay/2)
        while True:
            ser = open_serial_port(serial_port, baud_rate)
            laserCheck()
            ser.close()
            time.sleep(delay/2)
            print("second while loop")
            print(laserBlocked)
            if laserBlocked[motor + 1] == True:
                if motor == 1:
                    print('Slicer 1 rotated 90 degrees.')
                    with rotationStatus1:
                        rotationStatus1.clear()
                        ui.label('Slicer 1 rotated 90 degrees.')
                if motor == 2:
                    with rotationStatus2:
                        rotationStatus2.clear()
                        ui.label('Slicer 2 rotated 90 degrees.')
                if motor == 3:
                    with rotationStatus3:
                        rotationStatus3.clear()
                        ui.label('Slicer 3 rotated 90 degrees.')
                break
            send_step_pulse(1, motor + 1)
            time.sleep(delay/2)

    if status=="off": #rotate by +90 degrees 3 times
        for i in range(0,2):
            while True:
                ser = open_serial_port(serial_port, baud_rate)
                laserCheck()
                ser.close()
                time.sleep(delay/2)
                print(laserBlocked)
                if laserBlocked[motor + 1] == False:
                    break
                send_step_pulse(1, motor + 1)
                time.sleep(delay/2)
            while True:
                ser = open_serial_port(serial_port, baud_rate)
                laserCheck()
                ser.close()
                time.sleep(delay/2)
                print("second while loop")
                print(laserBlocked)
                if laserBlocked[motor + 1] == True:
                    break
                send_step_pulse(1, motor + 1)
                time.sleep(delay/2)
        if motor == 1:
            with rotationStatus1:
                rotationStatus1.clear()
                ui.label('Slicer 1 rotated 270 degrees.')
        if motor == 2:
            with rotationStatus2:
                rotationStatus2.clear()
                ui.label('Slicer 2 rotated 270 degrees.')
        if motor == 3:
            with rotationStatus3:
                rotationStatus3.clear()
                ui.label('Slicer 3 rotated 270 degrees.')
    '''
    

def getCurrentPos():
    global serial_port
    global baud_rate
    global currentPos
    global posLabel1
    global posLabel2
    global pos_values
    ser = open_serial_port(serial_port, baud_rate)
    ser.reset_input_buffer()
    ser.write(bytes(f'M114\n', encoding='utf-8'))
    pos_values = {axis: None for axis in motorsList}

    # Read lines until all desired axes are found
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line == '':
            continue
        for axis in motorsList:
            if f'{axis}:' in line:
                try:
                    pos_values[axis] = float(line.split(f'{axis}:')[1].split()[0])
                except (IndexError, ValueError):
                    pass
        if all(pos_values[axis] is not None for axis in motorsList):
            break
    ser.close()

    currentYPos = pos_values['Y'] * meterPerStep
    print(currentYPos)
    mmYPosString = f'{round(currentYPos*1000,6)} mm from zero'
    print('Y is '+mmYPosString)
    currentPos[0] = currentYPos

    currentZPos = pos_values['Z'] * meterPerStep
    print(currentZPos)
    mmZPosString = f'{round(currentZPos*1000,6)} mm from zero'
    print(f'Z is '+mmZPosString)
    currentPos[1] = currentZPos

    with posLabel1:
        posLabel1.clear()
        ui.label('Y is '+mmYPosString)
        #ui.label(f'{stepsTaken} steps taken this move.')
    with posLabel2:
        posLabel2.clear()
        ui.label(f'Z is '+mmZPosString)





def laserCheck():
    global laserBlocked
    global ser
    ser.write(bytes(f'M119\n', encoding='utf-8'))  # Send M119 command
    print("Sent M119. Reading full response...")

    # Reset all values
    endstop_values = {}

    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == "":
            continue
        print(f"> {line}")  # Print every line for debugging

        # Break when Marlin sends "ok" (meaning end of response)
        if line.lower() == "ok":
            break

        # Store detected endstop states in a dictionary
        if ':' in line:
            parts = line.split(':')
            if len(parts) == 2:
                endstop_name = parts[0].strip()
                endstop_state = parts[1].strip()
                endstop_values[endstop_name] = endstop_state

    # Map to laserBlocked by known order, if applicable
    axis_list = ['y_min', 'z_min', 'a_min', 'b_min', 'c_min']
    for i, axis in enumerate(axis_list):
        if axis in endstop_values:
            laserBlocked[i] = (endstop_values[axis] == 'TRIGGERED')
            print(f"{axis}: {endstop_values[axis]}")


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


def backToZero(motor):
    global serial_port
    global baud_rate
    global laserBlocked
    global ser
    global stepsTakenFromZero

    # look at G28, G60, G90, G91, G92
    ser = open_serial_port(serial_port, baud_rate)
    #ser.write(bytes(f'G28 Y\n', encoding='utf-8'))  # Send the command to home Y axis
    #print(bytes(f'G28 Y\n', encoding='utf-8'))
    #ser.write(bytes(f'G91\n', encoding='utf-8'))  # Send the command to change to relative coordinate system
    laserCheck()
    print(laserBlocked)
    print("zero working?")

    while laserBlocked[motor] == False:
        ser.write(bytes(f'G0 {motorsList[motor]}10\n', encoding='utf-8')) #step back a little bit
        print(bytes(f'G0 {motorsList[motor]}10\n', encoding='utf-8'))
        laserCheck()  #check if endstop is triggered
    '''
    if motor == 0:
        while laserBlocked[0] == False:
            ser.write(bytes(f'G0 Y10\n', encoding='utf-8'))
            print(bytes(f'G0 Y10\n', encoding='utf-8'))
            laserCheck()
    if motor == 1:
        while laserBlocked[1] == False:
            ser.write(bytes(f'G0 Z10\n', encoding='utf-8'))
            print(bytes(f'G0 Z10\n', encoding='utf-8'))
            laserCheck()
    '''
    #ser.write(bytes(f'G90\n', encoding='utf-8'))  # Send the command to change to absolute coordinate system
    #print(bytes(f'G90\n', encoding='utf-8'))
    ser.write(bytes(f'G92 {motorsList[motor]}0\n', encoding='utf-8'))  # Send the command to set 0 position
    print(bytes(f'G92\n', encoding='utf-8'))
    ser.close()
    print(f'Current Position is {round(currentPos[motor]*1000,6)} mm from zero')
    getCurrentPos()
    for i in range(len(stepsTakenFromZero)):
        stepsTakenFromZero[i] = 0


maxMovement = 0.008 #meters, need to measure
def set(frequency, phase, motor):
    global currentPos
    global pos_values

    print(frequency)
    print(phase)

    if phase < 0:
        phase += 360

    #calculate necessary steps to send
    inputWavelength = 2.9979*10**8/(frequency*10**9)
    distancePerDegree = inputWavelength / 360
    moveDistance = phase * distancePerDegree

    #steps = moveDistance * revPerMeter * stepsPerRev
    steps = moveDistance / meterPerStep

    #for time of movement calculations
    getCurrentPos()
    #stepsToGo = np.abs((moveDistance - currentPos) * revPerMeter * stepsPerRev)
    stepsToGo = steps - stepsTakenFromZero[motor]
    print(f'stepsToGo is {stepsToGo}')

    if motor == 0:
        with containerBelowSet1:
            if list(containerBelowSet1) or list(containerAboveSet1):
                containerBelowSet1.clear()
                containerAboveSet1.clear()
            with ui.row():
                ui.label('Set')
                ui.icon('check')
                ui.label(f'Performing {round(stepsToGo,1)} steps, or {round(stepsToGo/400,2)} revolutions, taking about {round(stepsToGo/stepsPerMin*60,2)} seconds')
        
        with containerAttemptedInput1:
            if list(containerAttemptedInput1):
                containerAttemptedInput1.clear()
            with ui.row():
                ui.label(str(frequency) + ' GHz at ' + str(phase) + ' degrees')
    if motor == 1:
        with containerBelowSet2:
            if list(containerBelowSet2) or list(containerAboveSet2):
                containerBelowSet2.clear()
                containerAboveSet2.clear()
            with ui.row():
                ui.label('Set')
                ui.icon('check')
                ui.label(f'Performing {round(stepsToGo,1)} steps, or {round(stepsToGo/400,2)} revolutions, taking about {round(stepsToGo/400/stepsPerMin*60,0)} seconds')
        
        with containerAttemptedInput2:
            if list(containerAttemptedInput2):
                containerAttemptedInput2.clear()
            with ui.row():
                ui.label(str(frequency) + ' GHz at ' + str(phase) + ' degrees')
    


    if moveDistance+currentPos[motor] < maxMovement:
        send_step_pulse(stepsToGo, motor)
        getCurrentPos()
    else:
        if motor == 0:
            with containerAboveSet1:
                if list(containerAboveSet1) or list(containerBelowSet1):
                    containerAboveSet1.clear()
                    containerBelowSet1.clear()
                ui.label('Invalid input, outside physical bounds of system.')
            with containerBelowSet1:    
                with ui.row():
                    ui.label('Set')
                    ui.icon('X')
        if motor == 1:
            with containerAboveSet2:
                if list(containerAboveSet2) or list(containerBelowSet2):
                    containerAboveSet2.clear()
                    containerBelowSet2.clear()
                ui.label('Invalid input, outside physical bounds of system.')
            with containerBelowSet2:    
                with ui.row():
                    ui.label('Set')
                    ui.icon('X')




def newInput(motor):
    if motor == 1:
        with containerAboveSet1:
            if list(containerBelowSet1) or list(containerAboveSet1):
                containerBelowSet1.clear()
                containerAboveSet1.clear()
            ui.label('Awaiting new input...')
    if motor == 2:
        with containerAboveSet2:
            if list(containerBelowSet2) or list(containerAboveSet2):
                containerBelowSet2.clear()
                containerAboveSet2.clear()
            ui.label('Awaiting new input...')

def stopMovement():
    global serial_port
    global baud_rate
    ser = open_serial_port(serial_port, baud_rate)
    ser.write(bytes(f'M410\n', encoding='utf-8'))
    ser.close()



def fineAdjustment(input, motor):
    global serial_port
    global baud_rate
    ser = open_serial_port(serial_port, baud_rate)
    ser.write(bytes(f'G91\n', encoding='utf-8'))
    if input > 0:
        print('increase by 1 step')
        ser.write(bytes(f'G0 {motorsList[motor]}1\n', encoding='utf-8'))
        print(f'G0 {motorsList[motor]}1\n')
    else:
        print('decrease by 1 step')
        ser.write(bytes(f'G0 {motorsList[motor]}-1\n', encoding='utf-8'))
        print(f'G0 {motorsList[motor]}-1\n')
    ser.close()
    #getCurrentPos()

def readLines(): #run while serial port is open
    # Start timeout clock
    timeout = 2  # seconds
    start_time = time.time()
    
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line == "":
            continue
        print(f"> {line}")  # Print every line for debugging

        # Break when Marlin sends "ok" (meaning end of response)
        if line.lower() == "ok":
            break
        
        #break after timeout
        if time.time() - start_time > timeout:
            break

def debug():
    global serial_port
    global baud_rate
    global ser
    
    ser = open_serial_port(serial_port, baud_rate)
    #ser.write(bytes(f'M211 S0\n', encoding='utf-8')) #disables software endstops
    #ser.write(bytes(f'M121\n', encoding='utf-8')) #disables endstops
    ser.write(bytes(f'M119\n', encoding='utf-8')) #reads endstops
    readLines()
    '''
    ser.write(bytes(f'M111 S6\n', encoding='utf-8')) #debugging extra info, extra errors
    ser.write(bytes(f'M906\n', encoding='utf-8')) #debugging reads motor currents in milliamps?
    ser.write(bytes(f'M503\n', encoding='utf-8')) #debugging reads current motor microstepping configuration
    ser.write(bytes(f'M211 S0\n', encoding='utf-8')) #disables software endstops
    ser.write(bytes(f'M122\n', encoding='utf-8')) #reads TMC driver info
    ser.write(bytes(f'M114\n', encoding='utf-8')) #reads current position
    readLines()
    readLines()
    readLines()
    readLines()
    readLines()
    print('positions are:')
    readLines()
    '''
    ser.close()
    
    #send_step_pulse(4000, 2)



ui.button('Custom, Debug', on_click=lambda: debug())
with ui.row():
    with ui.card():
        ui.label('Stepper Motor 1') #Y
        with ui.column():
            with ui.row():
                with ui.card():
                    moveValue1 = ui.number(label='Move Position', format='%.10f')
                    ui.button('Move', on_click=lambda: send_step_pulse(moveValue1.value, 0))
                with ui.card():
                    ui.label('Fine Adjustment (1 step)')
                    with ui.button_group():
                        ui.button('+', on_click=lambda: fineAdjustment(1, 0))
                        ui.button('-', on_click=lambda: fineAdjustment(-1, 0))
            with ui.row():
                with ui.card():
                    ui.label('Frequency (GHz)')
                    frequency1 = ui.number(label='Frequency (GHz)', format='%.10f', min=0, on_change=lambda: newInput(1))

                with ui.card():
                    ui.label('Phase Difference (Degrees)')
                    phase1 = ui.number(label='Phase Difference (Degrees)', format='%.10f',  min=-180, on_change=lambda: newInput(1))

            with ui.row():
                with ui.card():
                    containerAboveSet1 = ui.column()
                    ui.button('Set', on_click=lambda: set(frequency1.value,phase1.value,0))
                    containerBelowSet1 = ui.column()
                    ui.button('Zero', on_click=lambda: backToZero(0))
                    ui.button('Stop Move', on_click=lambda: stopMovement())
                

                with ui.card():
                    with ui.row():
                        ui.label('Current Input:')
                        posLabel1 = ui.column()
                    with ui.row():
                        ui.label('Attempted Input:')
                        containerAttemptedInput1 = ui.column()


    with ui.card():
        ui.label('Stepper Motor 2') #Z
        with ui.column():
            with ui.row():
                with ui.card():
                    moveValue2 = ui.number(label='Move Position', format='%.10f')
                    ui.button('Move', on_click=lambda: send_step_pulse(moveValue2.value, 1))
                with ui.card():
                    ui.label('Fine Adjustment (1 step)')
                    with ui.button_group():
                        ui.button('+', on_click=lambda: fineAdjustment(1, 1))
                        ui.button('-', on_click=lambda: fineAdjustment(-1, 1))
            with ui.row():
                with ui.card():
                    ui.label('Frequency (GHz)')
                    frequency2 = ui.number(label='Frequency (GHz)', format='%.10f', min=0, on_change=lambda: newInput(2))

                with ui.card():
                    ui.label('Phase Difference (Degrees)')
                    phase2 = ui.number(label='Phase Difference (Degrees)', format='%.10f',  min=-180, on_change=lambda: newInput(2))

            with ui.row():
                with ui.card():
                    containerAboveSet2 = ui.column()
                    ui.button('Set', on_click=lambda: set(frequency2.value,phase2.value,1))
                    containerBelowSet2 = ui.column()
                    ui.button('Zero', on_click=lambda: backToZero(1))
                    ui.button('Stop Move', on_click=lambda: stopMovement())
                

                with ui.card():
                    with ui.row():
                        ui.label('Current Input:')
                        posLabel2 = ui.column()
                    with ui.row():
                        ui.label('Attempted Input:')
                        containerAttemptedInput2 = ui.column()


with ui.card():
    ui.label('Slicer Rotators')
    with ui.row():
        with ui.card():
            with ui.column():
                ui.label('Slicer 1')
                ui.button('Rotate +90 degrees', on_click=lambda: rotateSlicer("on", 1))
                ui.button('Rotate -90 degrees', on_click=lambda: rotateSlicer("off", 1))
                rotationStatus1 = ui.column()
        with ui.card():
            with ui.column():
                ui.label('Slicer 2')
                ui.button('Rotate +90 degrees', on_click=lambda: rotateSlicer("on", 2))
                ui.button('Rotate -90 degrees', on_click=lambda: rotateSlicer("off", 2))
                rotationStatus2 = ui.column()
        with ui.card():
            with ui.column():
                ui.label('Slicer 3')
                ui.button('Rotate +90 degrees', on_click=lambda: rotateSlicer("on", 3))
                ui.button('Rotate -90 degrees', on_click=lambda: rotateSlicer("off", 3))
                rotationStatus3 = ui.column()



ui.run() #evaluates the code twice