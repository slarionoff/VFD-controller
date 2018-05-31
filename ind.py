import RPi.GPIO as GPIO
from time import sleep, localtime, strftime
from bitarray import bitarray
import sys
import math


def on(pin):
    GPIO.output(pin, GPIO.LOW)


def off(pin):
    GPIO.output(pin, GPIO.HIGH)


def init():
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
    USED_SHIFT_REGS_AMT = 19

    global PLACEHOLDERS_AMT
    PLACEHOLDERS_AMT = 10

    global n_bit_lines
    n_bit_lines = int(math.floor(math.log10(USED_SHIFT_REGS_AMT * PLACEHOLDERS_AMT)))

    # Nice header lines with bit numbers
    global bit_num_line
    i = 0
    bit_num_line = []
    while i <= n_bit_lines:
        j = 1
        s = ''
        while j <= USED_SHIFT_REGS_AMT * PLACEHOLDERS_AMT:
            s += (str(j).rjust(n_bit_lines + 1, '0'))[i]
            j = j + 1
        bit_num_line.append(s)
        i = i + 1

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

    #   Standard seven-segment indicator numbers (A-G). In my case I have also H (underscore) and DP (decimal point)
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


def finalize():
    on(STB)
    on(LATCH)
    off(LATCH)
    off(STB)


def debug_print_ba():
    i = 0
    while i <= n_bit_lines:
        print(''.join(bit_num_line[i]))
        i = i + 1
    print(ba.to01())


def fill_bitarray(input_string):
    # print(input_string)

    global ba
    ba = bitarray('0' * USED_SHIFT_REGS_AMT) * PLACEHOLDERS_AMT

    i = 1
    while i <= PLACEHOLDERS_AMT:
        # Fill a bitarray presenting Q-outputs.
        placeholder_bit = PLACEHOLDERS[i]
        ba[(i - 1) * USED_SHIFT_REGS_AMT + placeholder_bit - 1] = True

        ssi = SYMBOLS[input_string[i - 1]]
        for S in ssi:
            if ssi[S] == 1:
                ba[(i - 1) * USED_SHIFT_REGS_AMT + DISPLAY_ABCDEFG_Q[S] - 1] = True
        i = i + 1
    # debug_print_ba()


def send_bitarray_to_indicator():
    i = 1
    while i <= PLACEHOLDERS_AMT:
        k = 1
        while k <= USED_SHIFT_REGS_AMT:
            off(CLOCK)
            if ba[i * USED_SHIFT_REGS_AMT - k]:
                on(DA_IN)
            else:
                off(DA_IN)
            on(CLOCK)
            k = k + 1
        finalize()
        i = i + 1


# Main program
init()

str_to_show_prev = ''
str_to_show = ''.ljust(PLACEHOLDERS_AMT)

try:
    while True:
        DT = strftime('%Y-%m-%d', localtime()).ljust(PLACEHOLDERS_AMT)
        TM = strftime('  %H %M %S', localtime()).ljust(PLACEHOLDERS_AMT)
        TC = '   t -15°C'.ljust(PLACEHOLDERS_AMT)
        SEC = int(strftime('%S', localtime())[0])

        if SEC == 0 or SEC == 3:
            str_to_show = DT
        elif SEC == 1 or SEC == 4:
            str_to_show = TM
        elif SEC == 2 or SEC == 5:
            str_to_show = TC

#        str_to_show = TM
#        str_to_show = '0123456789'

        if str_to_show != str_to_show_prev:
            fill_bitarray(str_to_show)
            str_to_show_prev = str_to_show

        send_bitarray_to_indicator()

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
