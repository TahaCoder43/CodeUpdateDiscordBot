class StarterMessageNotFound(Exception):
    """When watching a forum post, it is expected to have a starter_message that is it's content which should be the code"""


class EnvNotProvided(Exception):
    """Providing .env file is a must and the bot cannot work without it"""


class NeitherLineNorKeyProvided(Exception):
    """handle_watchfile_command() needs either a line, or a key. If both are not provided this error is raised"""
