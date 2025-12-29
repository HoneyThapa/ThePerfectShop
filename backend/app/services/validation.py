def validate_dataframe(df, required_columns):
    errors = {}

    for col in required_columns:
        if col not in df.columns:
            errors[col] = "missing"

    if "on_hand_qty" in df.columns:
        neg = (df["on_hand_qty"] < 0).sum()
        if neg > 0:
            errors["on_hand_qty"] = f"{neg} negative values"

    if "expiry_date" in df.columns:
        missing = df["expiry_date"].isna().sum()
        if missing > 0:
            errors["expiry_date"] = f"{missing} missing expiry dates"

    return errors
