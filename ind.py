import RPi.GPIO as GPIO
from time import sleep, localtime, strftime
from bitarray import bitarray
import sys

def ON(pin):
    GPIO.output(pin, GPIO.LOW)

def OFF(pin):
    GPIO.output(pin, GPIO.HIGH)

def INIT():
    print('Initialization Started')

    GPIO.setmode(GPIO.BCM)

    global DA_IN
    global LATCH
    global CLOCK
    global STB

    DA_IN = 22
    LATCH = 23
    CLOCK = 24
    STB   = 25

    GPIO.setup([DA_IN, LATCH, CLOCK, STB], GPIO.OUT)

    ON(STB)
    OFF(LATCH)

    global PLACEHOLDERS
    PLACEHOLDERS={
        10: 13 ,
        9 : 12 ,
        8 : 11 ,
        7 : 10 ,
        6 :  9 ,
        5 :  8 ,
        4 :  7 ,
        3 :  6 ,
        2 :  5 ,
        1 : 19
    }

    global SYMBOLS
    SYMBOLS={
        '0' : {'A':1,'B':1,'C':1,'D':1,'E':1,'F':1,'G':0,'H':0,'DP':0} ,
        '1' : {'A':0,'B':1,'C':1,'D':0,'E':0,'F':0,'G':0,'H':0,'DP':0} ,
        '2' : {'A':1,'B':1,'C':0,'D':1,'E':1,'F':0,'G':1,'H':0,'DP':0} ,
        '3' : {'A':1,'B':1,'C':1,'D':1,'E':0,'F':0,'G':1,'H':0,'DP':0} ,
        '4' : {'A':0,'B':1,'C':1,'D':0,'E':0,'F':1,'G':1,'H':0,'DP':0} ,
        '5' : {'A':1,'B':0,'C':1,'D':1,'E':0,'F':1,'G':1,'H':0,'DP':0} ,
        '6' : {'A':1,'B':0,'C':1,'D':1,'E':1,'F':1,'G':1,'H':0,'DP':0} ,
        '7' : {'A':1,'B':1,'C':1,'D':0,'E':0,'F':0,'G':0,'H':0,'DP':0} ,
        '8' : {'A':1,'B':1,'C':1,'D':1,'E':1,'F':1,'G':1,'H':0,'DP':0} ,
        '9' : {'A':1,'B':1,'C':1,'D':0,'E':0,'F':1,'G':1,'H':0,'DP':0} ,
        ' ' : {'A':0,'B':0,'C':0,'D':0,'E':0,'F':0,'G':0,'H':0,'DP':0} ,
        '.' : {'A':0,'B':0,'C':0,'D':0,'E':0,'F':0,'G':0,'H':0,'DP':1} ,
        '-' : {'A':0,'B':0,'C':0,'D':0,'E':0,'F':0,'G':1,'H':0,'DP':0}
    }

    global DISPLAY_ABCDEFG_Q
    DISPLAY_ABCDEFG_Q={
        'A' : 17 ,
        'B' : 16 ,
        'C' : 15 ,
        'D' : 14 ,
        'E' :  3 ,
        'F' :  1 ,
        'G' :  2 ,
        'H' : 18,
        'DP':  4
    }
    print('Initialization Finished')

def FINALIZE():
    ON(STB)
    ON(LATCH)
    OFF(LATCH)
    OFF(STB)

def OUTPUT_LINE(str):
#    print(str)

#    print('-------------------XXXXXXXXXXXXX')
#    print('00000000011111111112222222222333')
#    print('12345678901234567890123456789012')
#    print('-------------------XXXXXXXXXXXXX')

    i=1
    while i<=10:
#   Create a bit array presenting Q-outputs. Q20..Q32 are disconnected.
        BA=bitarray('00000000000000000000000000000000')
        PLACEHOLDER_BIT=PLACEHOLDERS[i]
        BA[PLACEHOLDER_BIT-1]=True

        SSI=SYMBOLS[str[i-1]]
        j=0
        for S in SSI:
            if SSI[S]==1:
                BA[DISPLAY_ABCDEFG_Q[S]-1]=True
            j=j+1

#        print(BA.to01())

#   Write bit array to Indicator chip
        k=1
        while k<=32:
            OFF(CLOCK)
            if BA[32-k]:
                ON(DA_IN)
            else:
                OFF(DA_IN)
            ON(CLOCK)
            k=k+1
        FINALIZE()

        i=i+1

# Main program
INIT()

try:
    while True:
        DT = strftime('%Y-%m-%d', localtime()).ljust(10)
        TM = strftime('  %H %M %S', localtime()).ljust(10)
        SEC = int(strftime('%S', localtime())[1])

        if SEC >=0 and SEC <5:
            OUTPUT_LINE(DT)
        elif SEC >=5 and SEC<10:
            OUTPUT_LINE(TM)

except KeyboardInterrupt:
    OFF(DA_IN)
    k=1
    while k<=32:
        OFF(CLOCK)
        ON(CLOCK)
        k=k+1
    FINALIZE()

    GPIO.cleanup()

    print('Bye!')
    sys.exit(0)
