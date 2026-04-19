# Let me show you a few classic examples 👇

from turtle import *  # This is part of Python Standard Library for drawing graphics
import math            # For mathematical functions (like calculating sqrt)
from datetime import datetime  # Handles date/time


# Example 1: A classic "Hello, World!" with a twist
def greet():
    """Prints a greeting with the current date/time"""
    name = input("Enter your name: ")  # Taking user input
    time_now = datetime.now().strftime("%I:%M %p")  # Current time in readable format
    print(f"\nHello, {name}! It's currently → {time_now}\n")

greet()


# Example 2: A financial calculation with a real-world context
def calculate_simple_interest(principal, rate, time):
    """Calculate simple interest on a principal amount borrowed or invested"""
    # Formula: I = P * R * T
    interest = principal * rate / 100.0 * time
    total_amount = principal + interest
    
    # Format for readability — using string methods and formatting capabilities
    print(f"In {time} years at {rate}% interest,")
    print("your investment of $%.2f would grow to: \n$%.2f" % (principal, total_amount))

# Call the calculation function with example inputs
calculate_simple_interest(1000, 5, 3) # Invested $1000 at 5% for 3 years


# Example 3: A fun fizzbuzz-style program
def fizz_buzz():
    """Classic FizzBuzz — prints numbers but with conditions"""
    for num in range(1, 21): # Loop through a range of numbers
        if (num % 3 == 0) and (num % 5 == 0):
            print("FizzBuzz")
        elif num % 3 == 0:
            print("Fizz")
        elif num % 5 == 0:
            print("Buzz")
        else:
            print(num)

fizz_buzz() # Print numbers from 1 to 20


# Example 4: Basic mathematics with a clock display
def draw_clock(hour, minute):
    """Simple graphical clock using the turtle library showing time input"""
    # Set up our drawing space
    reset()
    penup()
    home()  # Bring turtle back to center

    # Draw hour hand
    angle_hour = ((hour + minute/60) / 12 * 360) % 360 
    # Angles are calculated relative to the passage of time
    setheading(90 - angle_hour)
    forward(80)
    write("%d:%02d" % (hour, minute), font = ("Arial", 16, "normal"))

draw_clock(3,45) # Draw a clock showing 3:45


# Example 5: A versatile function using if-else, input validation and libraries
def calculate_triangle_area():
    """Calculate area of a triangle with user-input dimensions."""
    
    try:
        base = float(input("Enter the length of the triangle's base: "))
        height = float(input("Enter the perpendicular height of the triangle: "))

        # The formula is Area = (base * height) / 2
        area = base * height / 2
        
        # Tell the user what happened — demonstrating string formatting
        print(f"📏 Calculating area with base {base} and height {height}:")
        print(f"📐 A right triangle would have an area of %.2f units squared." % area)

        # If needed, validate input — showing conditionals
        if base <= 0 or height <= 0:
            raise ValueError("Dimensions must be positive values.")

        # Then draw something? With turtle! 😄
        reset()
        penup()
        home()
        
        # Draw a triangle with the given base and height (simplified)
        color("blue")
        setpos(base/2, 0) 
        pendown()
        goto(-base/2, -height)
        goto(base/2*1.5, 0) # Just to form a closed shape
        home()

    except ValueError as ve:
        print("🚨 Error: ", ve)
    except ZeroDivisionError:
        print("🚨 Invalid calculation — base cannot be zero.")
    
calculate_triangle_area()
