def format_sum(amount):
    """Xabarlarda pulni o'qishga qulay ko'rsatadi: Decimal("1500000.00") -> "1 500 000 so'm"."""
    if amount == amount.to_integral_value():
        text = f"{amount:,.0f}"
    else:
        text = f"{amount:,.2f}"
    return f"{text.replace(',', ' ')} so'm"
