from lib.db import init_db


def initialize_schema():
    """
    Initialize and migrate all persistent Ninjaku schemas once at process startup.

    Read/status paths must not run CREATE, ALTER, INSERT defaults, or migrations.
    """

    # Core tables: settings, audit_logs, devices.
    init_db()

    # Lazy imports avoid module import cycles.
    from lib import device_service
    from lib import profiles_service
    from lib import policy_service
    from lib import wifi_service
    from lib import static_lease_service
    from lib import dns_filter_service
    from lib import qos_pipe_service
    from lib import qos_service
    from lib import dhcp_service

    # Profiles must exist before policy resolution/migrations.
    profiles_service.ensure_table()
    policy_service.ensure_table()

    # Core device schema migration.
    device_service.ensure_schema()

    # Feature tables.
    wifi_service.ensure_table()
    static_lease_service.ensure_table()
    dns_filter_service.ensure_table()
    qos_pipe_service.ensure_table()

    # Persistent settings defaults.
    qos_service.ensure_defaults()
    dhcp_service.ensure_defaults()

    return True
