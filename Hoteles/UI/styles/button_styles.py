from UI.styles.colors import Colors


def primary_button() -> dict:
    return {
        "fg_color": Colors.PRIMARY,
        "hover_color": Colors.PRIMARY_HOVER,
        "text_color": Colors.HEADER_TEXT,
        "text_color_disabled": Colors.TEXT_DISABLED,
    }


def secondary_button() -> dict:
    return {
        "fg_color": Colors.SECONDARY,
        "hover_color": Colors.SECONDARY_HOVER,
        "text_color": Colors.TEXT_PRIMARY,
        "text_color_disabled": Colors.TEXT_DISABLED,
    }
