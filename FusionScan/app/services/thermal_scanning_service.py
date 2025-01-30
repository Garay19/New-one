import serial
import time

def get_temperature_from_arduino():
    """
    Reads the temperature from an MLX90614 sensor connected to an Arduino via serial.

    Returns:
        float: The temperature in Celsius, or None if an error occurred.
    """
    try:
        # Configure the serial port
        ser = serial.Serial('COM11', 9600, timeout=2)  # Replace 'COM11' with your Arduino's port

        time.sleep(2)  # Allow time for the Arduino to initialize

        # Send a command to the Arduino to request the temperature
        ser.write(b'T')  # Send 'T' to request temperature

        # Read the temperature from the serial port
        line = ser.readline().decode('utf-8').strip()

        # Check if the response is valid
        if line:
            try:
                temperature = float(line)
                return temperature
            except ValueError:
                print(f"Error: Invalid temperature reading from Arduino: '{line}'")
                return None
        else:
            print("Error: No temperature reading received from Arduino.")
            return None

    except serial.SerialException as e:
        print(f"Error: Could not open serial port: {e}")
        return None
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()