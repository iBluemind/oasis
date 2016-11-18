===============================
oasis
===============================

OpenStack Boilerplate contains all the boilerplate you need to create an OpenStack package.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/oasis

Features
--------

* Function as a Service on OpenStack


Enabling in DevStack
--------------------

Add this repo as an external repository into your ``local.conf`` file::

    [[local|localrc]]
    enable_plugin oasis https://github.com/samgoon/oasis
    enable_plugin oasis-dashboard https://github.com/samgoon/oasis-dashboard
    enable_service o-api
    enable_service o-cond
                         
