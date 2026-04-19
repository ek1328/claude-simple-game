### 🚀 Example 2: Object-Oriented (OOP) Approach to Geometry + Inheritance


import math  # For sqrt calculations


class Shape:
    def area(self):
        print("Area function defined in base class")

    def perimeter(self, *args) -> float:
        ...


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        super().__init__()
        self.radius = radius

    def area(self):
        return math.pi * (self.radius ** 2)

# Demonstrate Circle properties — showing method overriding and floating point use
circle = Circle(4.5)
print(f"✅ Area of circle: {round(circle.area(), 2)} units squared")
