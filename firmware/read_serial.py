import serial
import time

ser = serial.Serial('/dev/ttyACM1', 115200, timeout=1)
ser.flushInput()
print(ser.name,"\n")

while(1):
    time.sleep(.01)
    line = ser.readline()
    if line:
        print(line.decode())

ser.close()
