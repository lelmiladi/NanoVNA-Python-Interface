# NanoVNA Interface and Data Processing Tool

# Author: Lisa Elmiladi

'''
This script provides the basic functionality to communicate with the NanoVNA, including opening the serial port, sending commands, 
receiving and parsing data, and closing the connection. For plotting and other advanced processing, you would need to use libraries like matplotlib for 
plotting and scipy for fitting and step response analysis, which are the Python equivalents of MATLAB functions like rfplot, smith, and stepresp.'''

import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy.constants import pi
from scipy.interpolate import interp1d
from scipy.signal import lfilter, bilinear, find_peaks, chirp


# Open the serial port connection
def nano_open(port):
    ser = serial.Serial(port, 9600, timeout=1)
    print(f'connect: {ser.name}')
    return ser

# Send a command to the NanoVNA and read the response
def nano_command(ser, command):
    ser.write(f'{command}\n'.encode())
    lines = []
    while True:
        line = ser.readline().decode().strip()
        if line == 'ch>':
            break
        if line:
            lines.append(line)
    return lines

# Get data from the NanoVNA
def nano_get_data(ser):
    freqs = nano_command(ser, 'frequencies')
    freqs = np.array([float(f) for f in freqs])

    s11 = nano_command(ser, 'data 0')
    s11 = np.array([str2complex(s) for s in s11])

    s21 = nano_command(ser, 'data 1')
    s21 = np.array([str2complex(s) for s in s21])

    # Create a structured numpy array to mimic MATLAB's network object
    dtype = [('frequencies', float), ('s11', complex), ('s21', complex)]
    netwk = np.zeros(len(freqs), dtype=dtype)
    netwk['frequencies'] = freqs
    netwk['s11'] = s11
    netwk['s21'] = s21
    return netwk

# Convert string to complex number
def str2complex(str_val):
    re_val, im_val = map(float, str_val.split(','))
    return re_val + 1j * im_val

# Close the serial port connection
def nano_close(ser):
    if ser.is_open:
        print('close')
        ser.close()

# Example of use
def nanovna():
    hCom = nano_open('COM3')
    try:
        # Send commands
        nano_command(hCom, 'sweep start 50000')
        nano_command(hCom, 'sweep stop 900000000')
        network_data = nano_get_data(hCom)
        
        # Plotting and other processing would go here
           # Plot S11 LOGMAG
        plt.figure()
        plt.plot(netwk['frequencies'], 20 * np.log10(abs(netwk['s11'])), '-r')
        plt.plot(netwk['frequencies'], 20 * np.log10(abs(netwk['s21'])), '-b')
        plt.ylim(-90, 10)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude (dB)')
        plt.title('LOGMAG')
        plt.show()

        # Plot S11 SMITH CHART
        # Note: matplotlib doesn't have a built-in Smith chart function like MATLAB
        # There are third-party libraries available for this purpose, or you can implement your own

        # Plot TDR step response - this is a simplified example
        # Use scipy or another library to implement the rational fitting and step response
        # Here we use a simple interpolation and filtering to mimic TDR response
        freqs = netwk['frequencies']
        s11 = netwk['s11']
        
        # Create a step function in frequency domain
        step_freq = interp1d(freqs, s11, kind='cubic', fill_value="extrapolate")
        freq_step = np.linspace(freqs.min(), freqs.max(), num=2048)
        t_step = np.fft.ifft(step_freq(freq_step))

        # Apply a window to limit the response (like a Kaiser window)
        window = np.kaiser(len(t_step), beta=5)
        t_step_windowed = t_step * window
        
        plt.figure()
        plt.plot(np.real(t_step_windowed))
        plt.xlabel('Time')
        plt.ylabel('Amplitude')
        plt.title('TDR Step Response')
        plt.show()

    finally:
        nano_close(hCom)

if __name__ == "__main__":
    nanovna()
