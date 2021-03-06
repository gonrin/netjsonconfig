import json
from copy import deepcopy
from ipaddress import ip_interface, ip_network

from .timezones import timezones
from ..base import BaseRenderer
from ...utils import sorted_dict


class NetworkRenderer(BaseRenderer):
    """
    Renders content importable with:
        uci import network
    """
    def _get_globals(self):
        globals = self.config.get('globals', {}).copy()
        if globals:
            globals.update({
                'ula_prefix': globals.get('ula_prefix', None),
            })
        return sorted_dict(globals)
        
    def _get_interfaces(self):
        """
        converts interfaces object to UCI interface directives
        """
        interfaces = self.config.get('interfaces', [])
        # this line ensures interfaces are not entirely
        # ignored if they do not contain any address
        default_addresses = [{'proto': 'none'}]
        # results container
        uci_interfaces = []
        for interface in interfaces:
            counter = 1
            is_bridge = False
            # determine uci logical interface name
            network = interface.get('network')
            if network:
                uci_name = network
            # default to ifname
            else:
                uci_name = interface['name'].replace('.', '_')\
                                            .replace('-', '_')
            # determine if must be type bridge
            if interface.get('type') == 'bridge':
                is_bridge = True
                bridge_members = ' '.join(interface['bridge_members'])
            # address list defaults to empty list
            for address in interface.get('addresses', default_addresses):
                # prepare new UCI interface directive
                uci_interface = deepcopy(interface)
                if network:
                    del uci_interface['network']
                if uci_interface.get('autostart'):
                    uci_interface['auto'] = interface['autostart']
                    del uci_interface['autostart']
                if uci_interface.get('disabled'):
                    uci_interface['enabled'] = not interface['disabled']
                    del uci_interface['disabled']
                if uci_interface.get('addresses'):
                    del uci_interface['addresses']
                if uci_interface.get('type'):
                    del uci_interface['type']
                if uci_interface.get('wireless'):
                    del uci_interface['wireless']
                # default values
                address_key = None
                address_value = None
                # proto defaults to static
                proto = address.get('proto', 'static')
                # add suffix if there is more than one config block
                if counter > 1:
                    name = '{name}_{counter}'.format(name=uci_name, counter=counter)
                else:
                    name = uci_name
                if address.get('family') == 'ipv4':
                    address_key = 'ipaddr'
                elif address.get('family') == 'ipv6':
                    address_key = 'ip6addr'
                    proto = proto.replace('dhcp', 'dhcpv6')
                if address.get('address') and address.get('mask'):
                    address_value = '{address}/{mask}'.format(**address)
                # update interface dict
                uci_interface.update({
                    'name': name,
                    'ifname': interface['name'],
                    'proto': proto,
                    'dns': self.__get_dns_servers(),
                    'dns_search': self.__get_dns_search()
                })
                # bridging
                if is_bridge:
                    uci_interface['type'] = 'bridge'
                    # put bridge members in ifname attribute
                    if bridge_members:
                        uci_interface['ifname'] = bridge_members
                    # if no members, this is an empty bridge
                    else:
                        uci_interface['bridge_empty'] = True
                        del uci_interface['ifname']
                    # ensure type "bridge" is only given to one logical interface
                    is_bridge = False
                # bridge has already been defined
                # but we need to add more references to it
                elif interface.get('type') == 'bridge':
                    # openwrt adds "br-"" prefix to bridge interfaces
                    # we need to take this into account when referring
                    # to these physical names
                    uci_interface['ifname'] = 'br-{0}'.format(interface['name'])
                # delete bridge_members attribtue
                if uci_interface.get('bridge_members') is not None:
                    del uci_interface['bridge_members']
                # add address if any (with correct option name)
                if address_key and address_value:
                    uci_interface[address_key] = address_value
                # merge additional address fields (discard default ones first)
                address_copy = address.copy()
                for key in ['address', 'mask', 'proto', 'family']:
                    if key in address_copy:
                        del address_copy[key]
                uci_interface.update(address_copy)
                # append to interface list
                uci_interfaces.append(sorted_dict(uci_interface))
                counter += 1
        return uci_interfaces

    def _get_routes(self):
        routes = self.config.get('routes', [])
        # results container
        uci_routes = []
        counter = 1
        # build uci_routes
        for route in routes:
            # prepare UCI route directive
            uci_route = route.copy()
            del uci_route['device']
            del uci_route['next']
            del uci_route['destination']
            if uci_route.get('cost'):
                del uci_route['cost']
            network = ip_interface(route['destination'])
            version = 'route' if network.version == 4 else 'route6'
            target = network.ip if network.version == 4 else network.network
            uci_route.update({
                'version': version,
                'name': 'route{0}'.format(counter),
                'interface': route['device'],
                'target': str(target),
                'gateway': route['next'],
                'metric': route.get('cost'),
                'source': route.get('source')
            })
            if network.version == 4:
                uci_route['netmask'] = str(network.netmask)
            uci_routes.append(sorted_dict(uci_route))
            counter += 1
        return uci_routes

    def _get_ip_rules(self):
        rules = self.config.get('ip_rules', [])
        uci_rules = []
        for rule in rules:
            uci_rule = rule.copy()
            src_net = None
            dest_net = None
            family = 4
            if rule.get('src'):
                src_net = ip_network(rule['src'])
            if rule.get('dest'):
                dest_net = ip_network(rule['dest'])
            if dest_net or src_net:
                family = dest_net.version if dest_net else src_net.version
            uci_rule['block_name'] = 'rule{0}'.format(family).replace('4', '')
            uci_rules.append(sorted_dict(uci_rule))
        return uci_rules

    def __get_dns_servers(self):
        dns = self.config.get('dns_servers', None)
        if dns:
            dns = ' '.join(dns)
        return dns

    def __get_dns_search(self):
        dns = self.config.get('dns_search', None)
        if dns:
            dns = ' '.join(dns)
        return dns

    def _get_switches(self):
        uci_switches = []
        for switch in self.config.get('switch', []):
            uci_switch = sorted_dict(deepcopy(switch))
            uci_switch['vlan'] = [sorted_dict(vlan) for vlan in uci_switch['vlan']]
            uci_switches.append(uci_switch)
        return uci_switches
    


class SystemRenderer(BaseRenderer):
    """
    Renders content importable with:
        uci import system
    """
    def _get_system(self):
        general = self.config.get('general', {}).copy()
        if general:
            timezone_human = general.get('timezone', 'Coordinated Universal Time')
            #timezone_value = timezones[timezone_human]
            general.update({
                'hostname': general.get('hostname', 'OpenWRT'),
                #'timezone': timezone_value,
                'timezone': timezone_human,
            })
        return sorted_dict(general)

    def _get_ntp(self):
        return sorted_dict(self.config.get('ntp', {}))

    def _get_leds(self):
        uci_leds = []
        for led in self.config.get('led', []):
            uci_leds.append(sorted_dict(led))
        return uci_leds


class WirelessRenderer(BaseRenderer):
    """
    Renders content importable with:
        uci import wireless
    """
    def _get_radios(self):
        radios = self.config.get('radios', [])
        uci_radios = []
        for radio in radios:
        	
            uci_radio = radio.copy()
            # rename tx_power to txpower
            if uci_radio.get('tx_power'):
            	uci_radio['txpower'] = radio['tx_power']
            	del uci_radio['tx_power']
            # rename driver to type
            uci_radio['type'] = radio['driver']
            del uci_radio['driver']
            # determine hwmode option
            uci_radio['hwmode'] = self.__get_hwmode(radio)
            del uci_radio['protocol']
            # determine channel width
            if radio['driver'] == 'mac80211':
                uci_radio['htmode'] = self.__get_htmode(radio)
            elif radio['driver'] in ['ath9k', 'ath5k']:
                uci_radio['chanbw'] = radio['channel_width']
            del uci_radio['channel_width']
            # ensure country is uppercase
            if uci_radio.get('country'):
                uci_radio['country'] = uci_radio['country'].upper()
            # append sorted dict
            uci_radios.append(sorted_dict(uci_radio))
        return uci_radios

    def __get_hwmode(self, radio):
        """
        possible return values are: 11a, 11b, 11g
        """
        protocol = radio['protocol']
        if protocol not in ['802.11n', '802.11ac']:
            return protocol.replace('802.', '')
        elif protocol == '802.11n' and radio['channel'] <= 13:
            return '11g'
        return '11a'

    def __get_htmode(self, radio):
        """
        only for mac80211 driver
        """
        if radio['protocol'] == '802.11n':
            return 'HT{0}'.format(radio['channel_width'])
        elif radio['protocol'] == '802.11ac':
            return 'VHT{0}'.format(radio['channel_width'])
        # disables n
        return 'NONE'

    def _get_wifi_interfaces(self):
        # select interfaces that have type == "wireless"
        wifi_interfaces = [i for i in self.config.get('interfaces', [])
                           if 'wireless' in i]
        # results container
        uci_wifi_ifaces = []
        for wifi_interface in wifi_interfaces:
            wireless = wifi_interface['wireless']
            # prepare UCI wifi-iface directive
            uci_wifi = wireless.copy()
            # add ifname
            #uci_wifi['ifname'] = wifi_interface['name']
            # rename radio to device
            uci_wifi['device'] = wireless['radio']
            del uci_wifi['radio']
            # map netjson wifi modes to uci wifi modes
            modes = {
                'access_point': 'ap',
                'station': 'sta',
                'adhoc': 'adhoc',
                'wds': 'wds',
                'monitor': 'monitor',
                '802.11s': 'mesh'
            }
            uci_wifi['mode'] = modes[wireless['mode']]
            # map advanced 802.11 netjson attributes to UCI
            wifi_options = {
                'ack_distance': 'distance',
                'rts_threshold': 'rts',
                'frag_threshold': 'frag'
            }
            for netjson_key, uci_key in wifi_options.items():
                if wireless.get(netjson_key) is not None:
                    uci_wifi[uci_key] = wireless[netjson_key]
                    del uci_wifi[netjson_key]
            # determine encryption for wifi
            if uci_wifi.get('encryption'):
                del uci_wifi['encryption']
                uci_encryption = self.__get_encryption(wireless)
                uci_wifi.update(uci_encryption)
            # attached networks (openwrt specific)
            # by default the wifi interface is attached
            # to its defining interface
            # but this behaviour can be overridden
            if not uci_wifi.get('network'):
                # get network, default to ifname
                network = wifi_interface.get('network', wifi_interface['name'])
                uci_wifi['network'] = [network]
            uci_wifi['network'] = ' '.join(uci_wifi['network'])\
                                     .replace('.', '_')
            uci_wifi_ifaces.append(sorted_dict(uci_wifi))
        return uci_wifi_ifaces

    def __get_encryption(self, wireless):
        encryption = wireless.get('encryption', {})
        disabled = encryption.get('disabled', False)
        uci = {}
        encryption_map = {
            'wep_open': 'wep-open',
            'wep_shared': 'wep-shared',
            'wpa_personal': 'psk',
            'wpa2_personal': 'psk2',
            'wpa_personal_mixed': 'psk-mixed',
            'wpa_enterprise': 'wpa',
            'wpa2_enterprise': 'wpa2',
            'wpa_enterprise_mixed': 'wpa-mixed',
            'wps': 'psk'
        }
        # if encryption disabled return empty dict
        if not encryption or disabled:
            return uci
        # otherwise configure encryption
        protocol = encryption['protocol']
        # default to protocol raw value in order
        # to allow customization by child classes
        uci['encryption'] = encryption_map.get(protocol, protocol)
        if protocol.startswith('wep'):
            uci['key'] = '1'
            uci['key1'] = encryption['key']
            # tell hostapd/wpa_supplicant key is not hex format
            if protocol == 'wep_open':
                uci['key1'] = 's:{0}'.format(uci['key1'])
        else:
            uci['key'] = encryption['key']
        # add ciphers
        if encryption.get('ciphers'):
            uci['encryption'] += '+{0}'.format('+'.join(encryption['ciphers']))
        return uci


class DefaultRenderer(BaseRenderer):
    """
    Default OpenWrt Renderer
    Allows great flexibility in defining UCI configuration in JSON format
    """
    def _get_custom_packages(self):
        # determine config keys to ignore
        ignore_list = list(self.backend.schema['properties'].keys())
        ignore_list += self.backend.get_packages()
        # determine custom packages
        custom_packages = {}
        for key, value in self.config.items():
            if key not in ignore_list:
                block_list = []
                # sort each config block
                if isinstance(value, list):
                    for block in value[:]:
                        # config block must be a dict
                        # with a key named "config_name"
                        # otherwise it's skipped with a warning
                        if not isinstance(block, dict) or 'config_name' not in block:
                            json_block = json.dumps(block, indent=4)
                            print('Unrecognized config block was skipped:\n\n'
                                  '{0}\n\n'.format(json_block))
                            continue
                        block_list.append(sorted_dict(block))
                # if not a list just skip
                else:  # pragma: nocover
                    continue
                custom_packages[key] = block_list
        # sort custom packages
        return sorted_dict(custom_packages)
