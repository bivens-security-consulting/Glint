import re
from typing import List, Dict

class GlintFingerprinter:
    def __init__(self):
        # Common fingerprints (Regex based)
        self.header_rules = {
            "Server": {
                r"Apache": "Apache",
                r"nginx": "Nginx",
                r"Microsoft-IIS": "IIS",
                r"Cloudflare": "Cloudflare",
                r"LiteSpeed": "LiteSpeed"
            },
            "X-Powered-By": {
                r"PHP": "PHP",
                r"ASP\.NET": "ASP.NET",
                r"Express": "Express.js"
            }
        }
        
        self.html_rules = {
            "Meta Generators": {
                r'<meta name="generator" content="WordPress': "WordPress",
                r'<meta name="generator" content="Joomla': "Joomla",
                r'<meta name="generator" content="Drupal': "Drupal",
                r'<meta name="generator" content="Ghost': "Ghost"
            },
            "Frameworks/Libs": {
                r'/_next/static/': "Next.js",
                r'/wp-content/': "WordPress",
                r'react\.development\.js': "React",
                r'react\.production\.min\.js': "React",
                r'vue\.js': "Vue.js",
                r'angular\.js': "Angular"
            }
        }

    def detect(self, headers: Dict, html: str) -> List[str]:
        technologies = set()

        # Check Headers
        for header, rules in self.header_rules.items():
            value = headers.get(header) or headers.get(header.lower())
            if value:
                for regex, tech in rules.items():
                    if re.search(regex, value, re.I):
                        technologies.add(tech)

        # Check HTML
        if html:
            for category, rules in self.html_rules.items():
                for regex, tech in rules.items():
                    if re.search(regex, html, re.I):
                        technologies.add(tech)

        return sorted(list(technologies))
