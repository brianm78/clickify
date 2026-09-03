def click_command_name(funcname: str) -> str:
    """Normalise function name to command name using click rules

    (Replace "_" with "-" and remove -command/-cmd/-group/-grp suffix)
    """
    name = funcname.lower().replace("_", "-")
    cmd_left, sep, suffix = name.rpartition("-")
    if sep and suffix in {"command", "cmd", "group", "grp"}:
        name = cmd_left
    return name


def click_option_name(paramname: str) -> str:
    """Normalise parameter to the expected click option name.
    Eg. foo_bar -> --foo-bar
    """
    # TODO: Check this.  (eliminate leading "_"?)
    return "--" + paramname.replace("_", "-")
