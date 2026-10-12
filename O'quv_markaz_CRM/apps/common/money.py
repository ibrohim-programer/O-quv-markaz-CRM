def format_sum(amount):
    if amount == amount.to_integral_value():
        text = f"{amount:,.0f}"
    else:
        text = f"{amount:,.2f}"
    return f"{text.replace(',', ' ')} so'm"
