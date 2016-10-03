# oasis.sh - Devstack extras script to install oasis

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

echo_summary "oasis's plugin.sh was called..."
source $DEST/oasis/devstack/lib/oasis
(set -o posix; set)

if is_service_enabled o-api o-cond; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing oasis"
        install_oasis
#        LIBS_FROM_GIT="${LIBS_FROM_GIT},python-oasisclient"
#        install_oasisclient
        cleanup_oasis
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring oasis"
        configure_oasis

        # Hack a large timeout for now
        iniset /etc/keystone/keystone.conf token expiration 7200

        if is_service_enabled key; then
            create_oasis_accounts
        fi

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize oasis
        init_oasis
#        oasis_register_image

        # Start the oasis API and oasis taskmgr components
        echo_summary "Starting oasis"
        start_oasis

#        configure_iptables
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_oasis
    fi

    if [[ "$1" == "clean" ]]; then
        cleanup_oasis
    fi
fi

# Restore xtrace
$XTRACE
