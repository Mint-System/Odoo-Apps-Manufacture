import odoo
from odoo.api import Environment


def odoo_env() -> Environment:
    # /!\ With Odoo < 15 you need to wrap all this in 'with
    #     Environment.manage()' and apply this Odoo patch:
    #     https://github.com/odoo/odoo/pull/70398, to properly handle context
    #     locals in an async program.

    config = odoo.tools.config
    config["db_name"] = "18.0"
    config["db_port"] = 5433
    config["db_user"] = "admin"
    config["db_password"] = "admin"

    # check_signaling() is to refresh the registry and cache when needed.
    registry = odoo.registry(config["db_name"]).check_signaling()
    # manage_change() is to signal other instances when the registry or cache
    # needs refreshing.
    with registry.manage_changes():
        # The cursor context manager commits unless there is an exception.
        with registry.cursor() as cr:
            yield Environment(cr, odoo.SUPERUSER_ID, {})