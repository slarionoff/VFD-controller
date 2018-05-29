import RPi.GPIO as GPIO
from time import sleep, localtime, strftime
from bitarray import bitarray
import sys


def on(pin):
    GPIO.output(pin, GPIO.LOW)


def off(pin):
    GPIO.output(pin, GPIO.HIGH)


def init():
    print('Initialization Started')

    GPIO.setmode(GPIO.BCM)

    global DA_IN
    global LATCH
    global CLOCK
    global STB

    DA_IN = 22
    LATCH = 23
    CLOCK = 24
    STB = 25

    global USED_SHIFT_REGS_AMT
    USED_SHIFT_REGS_AMT = 32

    GPIO.setup([DA_IN, LATCH, CLOCK, STB], GPIO.OUT)

    on(STB)
    off(LATCH)

    #   Magic numbers below are taken from an exact indicator board design
    global PLACEHOLDERS
    PLACEHOLDERS = {
        10: 13,
        9: 12,
        8: 11,
        7: 10,
        6: 9,
        5: 8,
        4: 7,
        3: 6,
        2: 5,
        1: 19
    }

    global DISPLAY_ABCDEFG_Q
    DISPLAY_ABCDEFG_Q = {
        'A': 17,
        'B': 16,
        'C': 15,
        'D': 14,
        'E': 3,
        'F': 1,
        'G': 2,
        'H': 18,
        'DP': 4
    }

    #   Standard seven-segment indicator numbers. In my case I have also H (underscore)
    global SYMBOLS
    SYMBOLS = {
        '0': {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 0, 'H': 0, 'DP': 0},
        '1': {'A': 0, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 0, 'G': 0, 'H': 0, 'DP': 0},
        '2': {'A': 1, 'B': 1, 'C': 0, 'D': 1, 'E': 1, 'F': 0, 'G': 1, 'H': 0, 'DP': 0},
        '3': {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 0, 'F': 0, 'G': 1, 'H': 0, 'DP': 0},
        '4': {'A': 0, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 1, 'G': 1, 'H': 0, 'DP': 0},
        '5': {'A': 1, 'B': 0, 'C': 1, 'D': 1, 'E': 0, 'F': 1, 'G': 1, 'H': 0, 'DP': 0},
        '6': {'A': 1, 'B': 0, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 1, 'H': 0, 'DP': 0},
        '7': {'A': 1, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 0, 'G': 0, 'H': 0, 'DP': 0},
        '8': {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1, 'F': 1, 'G': 1, 'H': 0, 'DP': 0},
        '9': {'A': 1, 'B': 1, 'C': 1, 'D': 0, 'E': 0, 'F': 1, 'G': 1, 'H': 0, 'DP': 0},
        ' ': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0, 'G': 0, 'H': 0, 'DP': 0},
        '.': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0, 'G': 0, 'H': 0, 'DP': 1},
        '-': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0, 'G': 1, 'H': 0, 'DP': 0},
        '_': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0, 'G': 0, 'H': 1, 'DP': 0}
    }

    print('Initialization Finished')


def finalize():
    on(STB)
    on(LATCH)
    off(LATCH)
    off(STB)


def output_string(input_string):
    # print(input_string)

    # print('00000000011111111112222222222333')

    # print('12345678901234567890123456789012')

    i = 1
    while i <= 10:
        # Create a bit array presenting Q-outputs.
        ba = bitarray('0' * USED_SHIFT_REGS_AMT)
        placeholder_bit = PLACEHOLDERS[i]
        ba[placeholder_bit - 1] = True

        ssi = SYMBOLS[input_string[i - 1]]
        j = 0
        for S in ssi:
            if ssi[S] == 1:
                ba[DISPLAY_ABCDEFG_Q[S] - 1] = True
            j = j + 1

        # print(ba.to01())

        # Write bit array to Indicator chip
        k = 1
        while k <= USED_SHIFT_REGS_AMT:
            off(CLOCK)
            if ba[USED_SHIFT_REGS_AMT - k]:
                on(DA_IN)
            else:
                off(DA_IN)
            on(CLOCK)
            k = k + 1
        finalize()

        i = i + 1


# Main program
init()

try:
    while True:
        DT = strftime('%Y-%m-%d', localtime()).ljust(10)
        TM = strftime('  %H %M %S', localtime()).ljust(10)
        SEC = int(strftime('%S', localtime())[1])

        if 0 <= SEC < 5:
            output_string(DT)
        elif 5 <= SEC < 10:
            output_string(TM)

except KeyboardInterrupt:
    off(DA_IN)
    m = 1
    while m <= USED_SHIFT_REGS_AMT:
        off(CLOCK)
        on(CLOCK)
        m = m + 1
    finalize()

    GPIO.cleanup()

    print('Bye!')
    sys.exit(0)
