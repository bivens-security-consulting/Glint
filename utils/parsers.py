import xml.etree.ElementTree as ET
import os
from typing import List

class GlintParser:
    @staticmethod
    def parse_nmap(xml_file: str) -> List[str]:
        """Parse Nmap XML file and extract probable web service URLs."""
        if not os.path.exists(xml_file):
            return []
        with open(xml_file, 'r') as f:
            content = f.read()
        return GlintParser.parse_nmap_string(content)

    @staticmethod
    def parse_nmap_string(xml_content: str) -> List[str]:
        """Parse Nmap XML string and extract probable web service URLs."""
        urls = []
        try:
            root = ET.fromstring(xml_content)
            for host in root.findall('host'):
                # Extract IP or hostname
                address_node = host.find('address')
                if address_node is None:
                    continue
                
                target = address_node.get('addr')
                
                # Check hostnames if available
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    name_node = hostnames.find('hostname')
                    if name_node is not None:
                        target = name_node.get('name')

                ports_node = host.find('ports')
                if ports_node is None:
                    continue

                for port in ports_node.findall('port'):
                    state = port.find('state')
                    if state is None or state.get('state') != 'open':
                        continue

                    portid = port.get('portid')
                    service = port.find('service')
                    protocol = "http"
                    
                    if service is not None:
                        service_name = service.get('name', '').lower()
                        if 'https' in service_name or 'ssl' in service_name or portid == '443':
                            protocol = "https"
                        elif 'http' not in service_name and portid not in ['80', '8080', '8000']:
                            continue
                    
                    if portid == '80' and protocol == 'http':
                        urls.append(f"http://{target}")
                    elif portid == '443' and protocol == 'https':
                        urls.append(f"https://{target}")
                    else:
                        urls.append(f"{protocol}://{target}:{portid}")

        except Exception as e:
            print(f"Error parsing Nmap XML: {e}")
        
        return list(dict.fromkeys(urls))
