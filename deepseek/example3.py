### 🔍 Example 3: Functional-Style Code with Lambda, File I/O & Sorting

import bisect  # For efficient search in sorted lists


def store_items():
    try:
        items = []
        
        # Read data from a file — showing with open() and error handling
        with open('products.txt', 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) == 2: 
                    try:
                        items.append((parts[0], float(parts[1].strip('$'))))
                    except ValueError:
                        pass

        # Sort the items — showing tuple comparison
        sorted_items = sorted(items, key=lambda x: (-x[1], len(x[0])))
        
        # Use bisect to find valid entries — showing use of decorators and methods
        for item_code in sorted_items:
            print("🍎", "Store item:", item_code[0], 
                  "$ per unit:" if item_code else sorted_items)
            
        # Display functionality of bisect with examples
        print("\n🔍 Using bisect to answer non-coding queries:")
        
    except FileNotFoundError:
        print("⚠️ File not found. Please try again.")