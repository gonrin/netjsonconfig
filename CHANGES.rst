Change log
==========

Version 0.3.4 [2016-01-14]
--------------------------

- `#35 <https://github.com/openwisp/netjsonconfig/issues/35>`_ wifi inherits ``disabled`` from interface

Version 0.3.3 [2015-12-18]
--------------------------

- `219f638 <https://github.com/openwisp/netjsonconfig/commit/219f638>`_ [cli] fixed binary standard output for ``generate`` method
- `a0b1373 <https://github.com/openwisp/netjsonconfig/compare/219f638...a0b1373>`_ removed
  timestamp from generated configuration archive to ensure reliable checksums

Version 0.3.2 [2015-12-11]
--------------------------

- `#31 <https://github.com/openwisp/netjsonconfig/issues/31>`_ added files in ``render`` output
- `#32 <https://github.com/openwisp/netjsonconfig/issues/32>`_ ``generate`` now returns an in-memory file object
- `badf292 <https://github.com/openwisp/netjsonconfig/commit/badf292>`_ updated command line utility script and examples
- `#33 <https://github.com/openwisp/netjsonconfig/issues/33>`_ added ``write`` method
- `5ff7360 <https://github.com/openwisp/netjsonconfig/commit/5ff7360>`_ [cli] positional ``config`` param is now ``--config`` or ``-c``
- `28de4a5 <https://github.com/openwisp/netjsonconfig/commit/28de4a5>`_ [cli] marked required arguments: ``--config``, ``--backend`` and ``--method``
- `f55cc4a <https://github.com/openwisp/netjsonconfig/commit/f55cc4a>`_ [cli] added ``--arg`` option to pass arguments to methods

Version 0.3.1 [2015-12-02]
--------------------------

- `69197ed <https://github.com/openwisp/netjsonconfig/commit/69197ed>`_ added "details" attribute to ``ValidationError``
- `0005186 <https://github.com/openwisp/netjsonconfig/commit/0005186>`_ avoid modifying original ``config`` argument

Version 0.3 [2015-11-30]
------------------------

- `#18 <https://github.com/openwisp/netjsonconfig/issues/18>`_ added ``OpenWisp`` backend
- `66ee96 <https://github.com/openwisp/netjsonconfig/commit/66ee96>`_ added file permission feature
- `#19 <https://github.com/openwisp/netjsonconfig/issues/19>`_ added sphinx documentation
  (published at `netjsonconfig.openwisp.org <http://netjsonconfig.openwisp.org>`_)
- `30348e <https://github.com/openwisp/netjsonconfig/commit/30348e>`_ hardened ntp server option schema for ``OpenWrt`` backend
- `c31375 <https://github.com/openwisp/netjsonconfig/commit/c31375>`_ added madwifi to the allowed drivers in schema ``OpenWrt`` backend
- `#30 <https://github.com/openwisp/netjsonconfig/issues/30>`_ updated schema according to latest `NetJSON <http://netjson.org>`_ spec

Version 0.2 [2015-11-23]
------------------------

- `#20 <https://github.com/openwisp/netjsonconfig/issues/20>`_ added support for array of lines in files
- `#21 <https://github.com/openwisp/netjsonconfig/issues/21>`_ date is now correctly set in tar.gz files
- `82cc5e <https://github.com/openwisp/netjsonconfig/commit/82cc5e>`_ configuration archive is now compatible with ``sysupgrade -r``
- `#22 <https://github.com/openwisp/netjsonconfig/issues/22>`_ improved and simplified bridging
- `#23 <https://github.com/openwisp/netjsonconfig/issues/23>`_ do not ignore interfaces with no addresses
- `#24 <https://github.com/openwisp/netjsonconfig/issues/24>`_ restricted schema for interface names
- `#25 <https://github.com/openwisp/netjsonconfig/issues/25>`_ added support for logical interface names
- `#26 <https://github.com/openwisp/netjsonconfig/issues/26>`_ ``merge_dict`` now returns a copy of all the elements
- `d22d59 <https://github.com/openwisp/netjsonconfig/commit/d22d59>`_ restricted SSID to 32 characters
- `#27 <https://github.com/openwisp/netjsonconfig/issues/27>`_ improved wireless definition
- `#28 <https://github.com/openwisp/netjsonconfig/issues/28>`_ removed "enabled" in favour of "disabled"

Version 0.1 [2015-10-20]
------------------------

- Added ``OpenWrt`` Backend
- Added command line utility ``netjsonconfig``
- Added multiple templating feature
- Added file inclusion feature
