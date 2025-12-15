# --- PROGRAM START ---
print("❄️  Welcome to the North Pole Hot Cocoa Shop! ❄️")
print("Let's build your perfect holiday drink.\n")

# REQUIREMENT: 3 Variables of different types
base_price = 2.50              # Number (Float)
order_summary = "Hot Cocoa"    # String
has_membership = False         # Boolean

# --- USER INPUT & LOGIC ---

# Question 1: Flavor Selection
flavor = input("Choose a flavor (Classic, Peppermint, or Gingerbread): ").lower()

# REQUIREMENT: Conditional Statement 1 (If/Elif/Else)
if flavor == "peppermint":
    base_price = base_price + 0.50
    order_summary = order_summary + " (Peppermint twist)"
    print("Optimization: Added Peppermint (+$0.50)")
elif flavor == "gingerbread":
    base_price = base_price + 0.75
    order_summary = order_summary + " (Gingerbread spice)"
    print("Optimization: Added Gingerbread (+$0.75)")
else:
    # Default to classic if they type something else or "classic"
    order_summary = order_summary + " (Classic Milk Chocolate)"
    print("Standard choice selected.")

# Question 2: Toppings
wants_whip = input("\nWould you like festive whipped cream? (yes/no): ").lower()

# REQUIREMENT: Conditional Statement 2 (If/Else)
if wants_whip == "yes":
    base_price = base_price + 0.25
    order_summary = order_summary + " with Whipped Cream"
    print("Yum! Whipped cream added.")
else:
    print("Keeping it simple. No whipped cream.")

# Question 3: Membership Check (Boolean Logic)
member_check = input("\nDo you have a Reindeer Club membership? (yes/no): ").lower()

if member_check == "yes":
    has_membership = True

# --- FINAL CALCULATIONS ---

# Apply discount if they are a member
if has_membership:
    print("\n🌟 Member detected! Applying $0.50 discount.")
    base_price = base_price - 0.50

# --- REQUIREMENT: Output Results ---
print("-" * 30)
print("🎁 RECEIPT 🎁")
print(f"Item: {order_summary}")
print(f"Total Due: ${base_price:.2f}")
print("-" * 30)
print("Happy Holidays! Enjoy your cocoa!")