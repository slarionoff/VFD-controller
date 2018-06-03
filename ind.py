import RPi.GPIO as GPIO
from time import localtime, strftime
from bitarray import bitarray
import sys
import math
from threading import Thread
import queue


def ON(pin):
    GPIO.output(pin, GPIO.LOW)


def OFF(pin):
    GPIO.output(pin, GPIO.HIGH)


def INIT():
    GPIO.setmode(GPIO.BCM)

    global DA_IN
    global LATCH
    global CLOCK
    global STB

    # RPi GPIO pin numbers
    DA_IN = 22
    LATCH = 23
    CLOCK = 24
    STB   = 25

    # Amount of used shift registers
    global USED_SHIFT_REGS_AMT
    USED_SHIFT_REGS_AMT = 19

    # Amount of symbols on the indicator
    global PLACEHOLDERS_AMT
    PLACEHOLDERS_AMT = 10

    global N_BIT_LINES
    N_BIT_LINES = int(math.floor(math.log10(USED_SHIFT_REGS_AMT * PLACEHOLDERS_AMT)))

    # Nice header lines with bit numbers for debug
    global BIT_NUM_LINE
    i = 0
    BIT_NUM_LINE = []
    while i <= N_BIT_LINES:
        j = 1
        s = ''
        while j <= USED_SHIFT_REGS_AMT * PLACEHOLDERS_AMT:
            s += (str(j).rjust(N_BIT_LINES + 1, '0'))[i]
            j = j + 1
        BIT_NUM_LINE.append(s)
        i = i + 1

    GPIO.setup([DA_IN, LATCH, CLOCK, STB], GPIO.OUT)

    ON(STB)
    OFF(LATCH)

    # Magic numbers below are taken from an exact indicator board design
    global PLACEHOLDERS
    PLACEHOLDERS = {
        10: 13,
        9:  12,
        8:  11,
        7:  10,
        6:   9,
        5:   8,
        4:   7,
        3:   6,
        2:   5,
        1:  19
    }

    global DISPLAY_ABCDEFG_Q
    DISPLAY_ABCDEFG_Q = {
        'A': 17,
        'B': 16,
        'C': 15,
        'D': 14,
        'E':  3,
        'F':  1,
        'G':  2,
        'H': 18,
        'DP': 4
    }

    # Standard seven-segment indicator numbers (A-G). In my case I have also H (underscore) and DP (decimal point)
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
        '_': {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0, 'G': 0, 'H': 1, 'DP': 0},
        '°': {'A': 1, 'B': 1, 'C': 0, 'D': 0, 'E': 0, 'F': 1, 'G': 1, 'H': 0, 'DP': 0},
        't': {'A': 0, 'B': 0, 'C': 0, 'D': 1, 'E': 1, 'F': 1, 'G': 1, 'H': 0, 'DP': 0},
        'C': {'A': 1, 'B': 0, 'C': 0, 'D': 1, 'E': 1, 'F': 1, 'G': 0, 'H': 0, 'DP': 0}
    }


def FINALIZE():
    ON(STB)
    ON(LATCH)
    OFF(LATCH)
    OFF(STB)


def DEBUG_PRINT_BA():
    i = 0
    while i <= N_BIT_LINES:
        print(''.join(BIT_NUM_LINE[i]))
        i = i + 1
    print(BA.to01())


def FILL_BITARRAY(INPUT_STRING):
    # print(INPUT_STRING)

    BA = bitarray('0' * USED_SHIFT_REGS_AMT) * PLACEHOLDERS_AMT

    i = 1
    while i <= PLACEHOLDERS_AMT:
        # Fill a bit array presenting Q-outputs.
        BA[(i - 1) * USED_SHIFT_REGS_AMT + PLACEHOLDERS[i] - 1] = True

        ssi = SYMBOLS[INPUT_STRING[i - 1]]
        for S in ssi:
            if ssi[S] == 1:
                BA[(i - 1) * USED_SHIFT_REGS_AMT + DISPLAY_ABCDEFG_Q[S] - 1] = True
        i = i + 1
    # DEBUG_PRINT_BA(BA)
    q.put(BA)


def SEND_BITARRAY_TO_INDICATOR():
    BA = q.get()
    while True:
        if not q.empty():
            BA = q.get()
        #DEBUG_PRINT_BA(BA)
        i = 1
        while i <= PLACEHOLDERS_AMT:
            k = 1
            while k <= USED_SHIFT_REGS_AMT:
                OFF(CLOCK)
                if BA[i * USED_SHIFT_REGS_AMT - k]:
                    ON(DA_IN)
                else:
                    OFF(DA_IN)
                ON(CLOCK)
                k = k + 1
            FINALIZE()
            i = i + 1


# Main program
INIT()

q = queue.Queue()
q.put(bitarray('0' * USED_SHIFT_REGS_AMT) * PLACEHOLDERS_AMT)

if __name__ == "__main__":
    t1 = Thread(target = SEND_BITARRAY_TO_INDICATOR)
    t1.setDaemon(True)
    t1.start()

    STR_TO_SHOW_PREV = ''
    STR_TO_SHOW = ''.ljust(PLACEHOLDERS_AMT)

    try:
        while True:
            DT = strftime('%Y-%m-%d', localtime()).ljust(PLACEHOLDERS_AMT)
            TM = strftime('  %H %M %S', localtime()).ljust(PLACEHOLDERS_AMT)
            TC = '   t -15°C'.ljust(PLACEHOLDERS_AMT)
            SEC = int(strftime('%S', localtime())[0])

            if SEC == 0 or SEC == 3:
                STR_TO_SHOW = DT
            elif SEC == 1 or SEC == 4:
                STR_TO_SHOW = TM
            elif SEC == 2 or SEC == 5:
                STR_TO_SHOW = TC

            if STR_TO_SHOW != STR_TO_SHOW_PREV:
                FILL_BITARRAY(STR_TO_SHOW)
                STR_TO_SHOW_PREV = STR_TO_SHOW

    except KeyboardInterrupt:
        OFF(DA_IN)
        m = 1
        while m <= USED_SHIFT_REGS_AMT:
            OFF(CLOCK)
            ON(CLOCK)
            m = m + 1
        FINALIZE()

        GPIO.cleanup()

        print('Bye!')
        sys.exit(0)
