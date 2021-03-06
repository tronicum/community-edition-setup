#!/usr/bin/python

# The MIT License (MIT)
#
# Copyright (c) 2014 Gluu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os.path
import Properties
import random
import shutil
import socket
import string
import time
import uuid
import json
import traceback
import subprocess
import sys
import getopt
import hashlib
import re
import glob

class Setup(object):
    def __init__(self, install_dir=None):
        self.install_dir = install_dir

        self.oxVersion = '3.0.0-SNAPSHOT'
        self.githubBranchName = 'master'

        # Used only if -w (get wars) options is given to setup.py
        self.oxauth_war = 'https://ox.gluu.org/maven/org/xdi/oxauth-server/%s/oxauth-server-%s.war' % (self.oxVersion, self.oxVersion)
        self.oxauth_rp_war = 'https://ox.gluu.org/maven/org/xdi/oxauth-rp/%s/oxauth-rp-%s.war' % (self.oxVersion, self.oxVersion)
        self.oxtrust_war = 'https://ox.gluu.org/maven/org/xdi/oxtrust-server/%s/oxtrust-server-%s.war' % (self.oxVersion, self.oxVersion)
        self.idp3_war = 'http://ox.gluu.org/maven/org/xdi/oxshibbolethIdp/%s/oxshibbolethIdp-%s.war' % (self.oxVersion, self.oxVersion)
        self.idp3_dist_jar = 'http://ox.gluu.org/maven/org/xdi/oxShibbolethStatic/%s/oxShibbolethStatic-%s.jar' % (self.oxVersion, self.oxVersion)
        self.idp3_cml_keygenerator = 'http://ox.gluu.org/maven/org/xdi/oxShibbolethKeyGenerator/%s/oxShibbolethKeyGenerator-%s.jar' % (self.oxVersion, self.oxVersion)
        self.asimba_war = 'http://ox.gluu.org/maven/org/asimba/asimba-wa/%s/asimba-wa-%s.war' % (self.oxVersion, self.oxVersion)
        self.cas_war = 'http://ox.gluu.org/maven/org/xdi/ox-cas-server-webapp/%s/ox-cas-server-webapp-%s.war' % (self.oxVersion, self.oxVersion)
        self.ce_setup_zip = 'https://github.com/GluuFederation/community-edition-setup/archive/%s.zip' % self.githubBranchName

        self.downloadWars = None
        self.templateRenderingDict = {}

        # OS commands
        self.cmd_ln = '/bin/ln'
        self.cmd_chmod = '/bin/chmod'
        self.cmd_chown = '/bin/chown'
        self.cmd_mkdir = '/bin/mkdir'
        self.cmd_rpm = '/bin/rpm'
        self.cmd_dpkg = '/usr/bin/dpkg'
        self.opensslCommand = '/usr/bin/openssl'

        self.sysemProfile = "/etc/profile"

        # java commands
        self.jre_home = '/opt/jre'
        self.cmd_java = '%s/bin/java' % self.jre_home
        self.cmd_keytool = '%s/bin/keytool' % self.jre_home
        self.cmd_jar = '%s/bin/jar' % self.jre_home

        # Component versions
        self.jre_version = '102'
        self.jetty_version = '9.3.12.v20160915'
        self.jython_version = '2.7.0'
        self.node_version = '6.9.1'
        self.apache_version = None
        self.opendj_version = None

        # Gluu components installation status
        self.installOxAuth = True
        self.installOxTrust = True
        self.installLdap = True
        self.installHttpd = True
        self.installSaml = False
        self.installAsimba = False
        self.installCas = False
        self.installOxAuthRP = False
        self.installPassport = False
        self.allowPreReleasedApplications = False

        self.os_types = ['centos', 'redhat', 'fedora', 'ubuntu', 'debian']
        self.os_type = None
        self.os_initdaemon = None

        self.shibboleth_version = ''

        self.node_home = '/opt/node'

        self.jetty_dist = '/opt/jetty-9.3'
        self.jetty_home = '/opt/jetty'
        self.jetty_base = '/opt/web/jetty'
        self.jetty_user_home = '/home/jetty'
        self.jetty_user_home_lib = '%s/lib' % self.jetty_user_home
        self.jetty_app_configuration = {
                'oxauth' : {'name' : 'oxauth',
                            'jetty' : {'modules' : 'deploy,http,logging,jsp,servlets,ext,http-forwarded'},
                            'memory' : {'ratio' : 0.3, "max_allowed_mb" : 4096},
                            'installed' : False
            },
                'identity' : {'name' : 'identity',
                              'jetty' : {'modules' : 'deploy,http,logging,jsp,ext,http-forwarded'},
                              'memory' : {'ratio' : 0.2, "max_allowed_mb" : 2048},
                              'installed' : False
            },
                'idp' : {'name' : 'idp',
                         'jetty' : {'modules' : 'deploy,http,logging,jsp,http-forwarded'},
                         'memory' : {'ratio' : 0.2, "max_allowed_mb" : 1024},
                         'installed' : False
            },
                'asimba' : {'name' : 'asimba',
                         'jetty' : {'modules' : 'deploy,http,logging,jsp,http-forwarded'},
                         'memory' : {'ratio' : 0.1, "max_allowed_mb" : 1024},
                         'installed' : False
            },
                'cas' : {'name' : 'cas',
                         'jetty' : {'modules' : 'deploy,http,logging,jsp,http-forwarded'},
                         'memory' : {'ratio' : 0.1, "max_allowed_mb" : 1024},
                         'installed' : False
            },
                'oxauth-rp' : {'name' : 'oxauth-rp',
                         'jetty' : {'modules' : 'deploy,http,logging,jsp,http-forwarded'},
                         'memory' : {'ratio' : 0.1, "max_allowed_mb" : 512},
                         'installed' : False
            }
        }

        self.distFolder = '/opt/dist'
        self.distAppFolder = '%s/app' % self.distFolder
        self.distWarFolder = '%s/war' % self.distFolder
        self.distTmpFolder = '%s/tmp' % self.distFolder

        self.setup_properties_fn = '%s/setup.properties' % self.install_dir
        self.log = '%s/setup.log' % self.install_dir
        self.logError = '%s/setup_error.log' % self.install_dir
        self.savedProperties = '%s/setup.properties.last' % self.install_dir

        self.gluuOptFolder = '/opt/gluu'
        self.gluuOptBinFolder = '/opt/gluu/bin'
        self.gluuBaseFolder = '/etc/gluu'
        self.configFolder = '%s/conf' % self.gluuBaseFolder
        self.certFolder = '/etc/certs'

        self.oxBaseDataFolder = "/var/ox"
        self.oxPhotosFolder = "/var/ox/photos"
        self.oxTrustRemovedFolder = "/var/ox/oxtrust/removed"
        self.oxTrustCacheRefreshFolder = "/var/ox/oxtrust/vds-snapshots"
        self.oxCustomizationFolder = "/var/gluu/webapps"

        self.etc_hosts = '/etc/hosts'
        self.etc_hostname = '/etc/hostname'

        self.idp3Folder = "/opt/shibboleth-idp"
        self.idp3MetadataFolder = "/opt/shibboleth-idp/metadata"
        self.idp3LogsFolder = "/opt/shibboleth-idp/logs"
        self.idp3LibFolder = "/opt/shibboleth-idp/lib"
        self.idp3ConfFolder = "/opt/shibboleth-idp/conf"
        self.idp3ConfAuthnFolder = "/opt/shibboleth-idp/conf/authn"
        self.idp3CredentialsFolder = "/opt/shibboleth-idp/credentials"
        # self.idp3WarFolder = "/opt/shibboleth-idp/war"

        self.hostname = None
        self.ip = None
        self.orgName = None
        self.orgShortName = None
        self.countryCode = None
        self.city = None
        self.state = None
        self.admin_email = None
        self.encoded_ox_ldap_pw = None
        self.encoded_ldap_pw = None
        self.encoded_shib_jks_pw = None
        self.application_max_ram = None    # in MB
        self.encode_salt = None

        self.baseInum = None
        self.inumOrg = None
        self.inumAppliance = None
        self.inumOrgFN = None
        self.inumApplianceFN = None
        self.ldapBaseFolderldapPass = None
        self.oxauth_client_id = None
        self.oxauthClient_pw = None
        self.oxauthClient_encoded_pw = None
        self.oxTrustConfigGeneration = None

        self.outputFolder = '%s/output' % self.install_dir
        self.templateFolder = '%s/templates' % self.install_dir
        self.oxauth_error_json = '%s/static/oxauth/oxauth-errors.json' % self.install_dir

        self.oxauth_openid_jwks_fn = "%s/oxauth-keys.json" % self.certFolder
        self.oxauth_openid_jks_fn = "%s/oxauth-keys.jks" % self.certFolder
        self.oxauth_openid_jks_pass = None

        self.httpdKeyPass = None
        self.httpdKeyFn = '%s/httpd.key' % self.certFolder
        self.httpdCertFn = '%s/httpd.crt' % self.certFolder
        self.shibJksPass = None
        self.shibJksFn = '%s/shibIDP.jks' % self.certFolder
        self.asimbaJksPass = None
        self.asimbaJksFn = '%s/asimbaIDP.jks' % self.certFolder

        self.opendj_ldap_binddn = 'cn=directory manager'
        self.ldap_hostname = "localhost"
        self.ldap_port = '1389'
        self.ldaps_port = '1636'
        self.ldap_jmx_port = '1689'
        self.ldap_admin_port = '4444'
        self.ldapBaseFolder = '/opt/opendj'
        self.ldap_user_home = '/home/ldap'
        self.ldapPassFn = '%s/.pw' % self.ldap_user_home
        self.ldap_backend_type = 'je'
        self.importLdifCommand = '%s/bin/import-ldif' % self.ldapBaseFolder
        self.ldapModifyCommand = '%s/bin/ldapmodify' % self.ldapBaseFolder
        self.loadLdifCommand = self.ldapModifyCommand
        self.schemaFolder = "%s/template/config/schema" % self.ldapBaseFolder
        self.gluuScriptFiles = ['%s/static/scripts/logmanager.sh' % self.install_dir,
                                '%s/static/scripts/testBind.py' % self.install_dir]
        self.redhat_services = ['memcached', 'httpd']
        self.debian_services = ['memcached', 'apache2']

        self.apache_start_script = '/etc/init.d/httpd'

        self.ldapEncodePWCommand = '%s/bin/encode-password' % self.ldapBaseFolder
        self.oxEncodePWCommand = '%s/bin/encode.py' % self.gluuOptFolder
        self.defaultTrustStoreFN = '%s/jre/lib/security/cacerts' % self.jre_home
        self.defaultTrustStorePW = 'changeit'

        self.openldapBaseFolder = '/opt/symas'
        self.openldapBinFolder = '/opt/symas/bin'
        self.openldapConfFolder = '/opt/symas/etc/openldap'
        self.openldapCnConfig = '%s/slapd.d' % self.openldapConfFolder
        self.openldapRootUser = "cn=directory manager,o=gluu"
        self.openldapKeyPass = None
        self.openldapTLSCACert = '%s/openldap.pem' % self.certFolder
        self.openldapTLSCert = '%s/openldap.crt' % self.certFolder
        self.openldapTLSKey = '%s/openldap.key' % self.certFolder
        self.openldapSlapdConf = '%s/slapd.conf' % self.outputFolder
        self.openldapSymasConf = '%s/symas-openldap.conf' % self.outputFolder
        self.slaptest = '%s/slaptest' % self.openldapBinFolder
        self.openldapLogDir = "/var/log/openldap/"
        self.openldapSyslogConf = "%s/static/openldap/openldap-syslog.conf" % self.install_dir
        self.openldapLogrotate = "%s/static/openldap/openldap_logrotate" % self.install_dir


        # Stuff that gets rendered; filename is necessary. Full path should
        # reflect final path if the file must be copied after its rendered.
        self.oxauth_config_json = '%s/oxauth-config.json' % self.outputFolder
        self.oxtrust_config_json = '%s/oxtrust-config.json' % self.outputFolder
        self.oxtrust_cache_refresh_json = '%s/oxtrust-cache-refresh.json' % self.outputFolder
        self.oxtrust_import_person_json = '%s/oxtrust-import-person.json' % self.outputFolder
        self.oxidp_config_json = '%s/oxidp-config.json' % self.outputFolder
        self.oxcas_config_json = '%s/oxcas-config.json' % self.outputFolder
        self.oxasimba_config_json = '%s/oxasimba-config.json' % self.outputFolder
        self.gluu_python_readme = '%s/conf/python/python.txt' % self.gluuBaseFolder
        self.ox_ldap_properties = '%s/ox-ldap.properties' % self.configFolder
        self.oxauth_static_conf_json = '%s/oxauth-static-conf.json' % self.outputFolder
        self.oxTrust_log_rotation_configuration = "%s/conf/oxTrustLogRotationConfiguration.xml" % self.gluuBaseFolder
        self.eduperson_schema_ldif = '%s/config/schema/96-eduperson.ldif'
        self.apache2_conf = '%s/httpd.conf' % self.outputFolder
        self.apache2_ssl_conf = '%s/https_gluu.conf' % self.outputFolder
        self.apache2_24_conf = '%s/httpd_2.4.conf' % self.outputFolder
        self.apache2_ssl_24_conf = '%s/https_gluu.conf' % self.outputFolder
        self.ldif_base = '%s/base.ldif' % self.outputFolder
        self.ldif_appliance = '%s/appliance.ldif' % self.outputFolder
        self.ldif_attributes = '%s/attributes.ldif' % self.outputFolder
        self.ldif_scopes = '%s/scopes.ldif' % self.outputFolder
        self.ldif_clients = '%s/clients.ldif' % self.outputFolder
        self.ldif_people = '%s/people.ldif' % self.outputFolder
        self.ldif_groups = '%s/groups.ldif' % self.outputFolder
        self.ldif_site = '%s/static/cache-refresh/o_site.ldif' % self.install_dir
        self.ldif_scripts = '%s/scripts.ldif' % self.outputFolder
        self.ldif_configuration = '%s/configuration.ldif' % self.outputFolder
        self.ldif_scim = '%s/scim.ldif' % self.outputFolder
        self.ldif_asimba = '%s/asimba.ldif' % self.outputFolder
        self.ldif_passport = '%s/passport.ldif' % self.outputFolder
        self.passport_config = '%s/passport-config.json' % self.configFolder
        self.encode_script = '%s/bin/encode.py' % self.gluuOptFolder
        self.cas_properties = '%s/cas.properties' % self.outputFolder
        self.asimba_configuration = '%s/asimba.xml' % self.outputFolder
        self.asimba_properties = '%s/asimba.properties' % self.outputFolder
        self.asimba_selector_configuration = '%s/conf/asimba-selector.xml' % self.gluuBaseFolder
        self.network = "/etc/sysconfig/network"
        self.system_profile_update = '%s/system_profile' % self.outputFolder

        self.staticIDP3FolderConf = '%s/static/idp3/conf' % self.install_dir
        self.staticIDP3FolderMetadata = '%s/static/idp3/metadata' % self.install_dir
        self.idp3_configuration_properties = '/idp.properties'
        self.idp3_configuration_ldap_properties = '/ldap.properties'
        self.idp3_configuration_saml_nameid = '/saml-nameid.properties'
        self.idp3_configuration_services = '/services.properties'
        self.idp3_configuration_password_authn = '/authn/password-authn-config.xml'
        self.idp3_metadata = '/idp-metadata.xml'

        ### rsyslog file customised for init.d
        self.rsyslogInitFile = "%s/static/etc/init.d/rsyslog" % self.install_dir

        self.ldap_setup_properties = '%s/opendj-setup.properties' % self.templateFolder

        # oxAuth/oxTrust Base64 configuration files
        self.pairwiseCalculationKey = None
        self.pairwiseCalculationSalt = None

        # OpenID key generation default setting
        self.default_openid_jks_dn_name = 'CN=oxAuth CA Certificates'
        self.default_key_algs = 'RS256 RS384 RS512 ES256 ES384 ES512'
        self.default_key_expiration = 365

        # oxTrust SCIM configuration
        self.scim_rs_client_id = None
        self.scim_rs_client_jwks = None
        self.scim_rs_client_jks_fn = "%s/scim-rs.jks" % self.certFolder
        self.scim_rs_client_jks_pass = None
        self.scim_rs_client_jks_pass_encoded = None

        self.scim_rp_client_id = None
        self.scim_rp_client_jwks = None
        self.scim_rp_client_jks_fn = "%s/scim-rp.jks" % self.outputFolder
        self.scim_rp_client_jks_pass = 'secret'

        # oxPassport Configuration
        self.ldif_passport_config = '%s/oxpassport-config.ldif' % self.outputFolder

        self.passport_rs_client_id = None
        self.passport_rs_client_jwks = None
        self.passport_rs_client_jks_fn = "%s/passport-rs.jks" % self.certFolder
        self.passport_rs_client_jks_pass = None
        self.passport_rs_client_jks_pass_encoded = None

        self.passport_rp_client_id = None
        self.passport_rp_client_jwks = None
        self.passport_rp_client_jks_fn = "%s/passport-rp.jks" % self.certFolder
        self.passport_rp_client_cert_alg = "RS512"
        self.passport_rp_client_cert_alias = None
        self.passport_rp_client_cert_fn = "%s/passport-rp.pem" % self.certFolder
        self.passport_rp_client_jks_pass = 'secret'

        self.ldif_files = [self.ldif_base,
                           self.ldif_appliance,
                           self.ldif_attributes,
                           self.ldif_scopes,
                           self.ldif_clients,
                           self.ldif_people,
                           self.ldif_groups,
                           self.ldif_site,
                           self.ldif_scripts,
                           self.ldif_configuration,
                           self.ldif_scim,
                           self.ldif_asimba,
                           self.ldif_passport,
                           self.ldif_passport_config
                           ]

        self.ce_templates = {self.oxauth_config_json: False,
                     self.gluu_python_readme: True,
                     self.oxtrust_config_json: False,
                     self.oxtrust_cache_refresh_json: False,
                     self.oxtrust_import_person_json: False,
                     self.oxidp_config_json: False,
                     self.oxcas_config_json: False,
                     self.oxasimba_config_json: False,
                     self.ox_ldap_properties: True,
                     self.oxauth_static_conf_json: False,
                     self.oxTrust_log_rotation_configuration: True,
                     self.ldap_setup_properties: False,
                     self.apache2_conf: False,
                     self.apache2_ssl_conf: False,
                     self.apache2_24_conf: False,
                     self.apache2_ssl_24_conf: False,
                     self.etc_hosts: False,
                     self.etc_hostname: False,
                     self.ldif_base: False,
                     self.ldif_appliance: False,
                     self.ldif_attributes: False,
                     self.ldif_scopes: False,
                     self.ldif_clients: False,
                     self.ldif_people: False,
                     self.ldif_groups: False,
                     self.ldif_scripts: False,
                     self.ldif_scim: False,
                     self.ldif_asimba: False,
                     self.ldif_passport: False,
                     self.ldif_passport_config: False,
                     self.cas_properties: False,
                     self.asimba_configuration: False,
                     self.asimba_properties: False,
                     self.asimba_selector_configuration: True,
                     self.network: False,
                     self.openldapSlapdConf: False,
                     self.openldapSymasConf: False
                     }

        self.oxauth_keys_utils_libs = [ 'bcprov-jdk15on-*.jar', 'bcpkix-jdk15on-*.jar', 'commons-lang-*.jar',
                                        'log4j-*.jar', 'commons-codec-*.jar', 'commons-cli-*.jar', 'commons-io-*.jar',
                                        'jettison-*.jar', 'oxauth-model-*.jar', 'oxauth-client-*.jar' ]

    def __repr__(self):
        try:
            return 'hostname'.ljust(30) + self.hostname.rjust(35) + "\n" \
                + 'orgName'.ljust(30) + self.orgName.rjust(35) + "\n" \
                + 'os'.ljust(30) + self.os_type.rjust(35) + "\n" \
                + 'city'.ljust(30) + self.city.rjust(35) + "\n" \
                + 'state'.ljust(30) + self.state.rjust(35) + "\n" \
                + 'countryCode'.ljust(30) + self.countryCode.rjust(35) + "\n" \
                + 'support email'.ljust(30) + self.admin_email.rjust(35) + "\n" \
                + 'Applications max ram'.ljust(30) + self.application_max_ram.rjust(35) + "\n" \
                + 'Admin Pass'.ljust(30) + self.ldapPass.rjust(35) + "\n" \
                + 'Install oxAuth'.ljust(30) + repr(self.installOxAuth).rjust(35) + "\n" \
                + 'Install oxTrust'.ljust(30) + repr(self.installOxTrust).rjust(35) + "\n" \
                + 'Install LDAP'.ljust(30) + repr(self.installLdap).rjust(35) + "\n" \
                + 'Install Apache 2 web server'.ljust(30) + repr(self.installHttpd).rjust(35) + "\n" \
                + 'Install Shibboleth SAML IDP'.ljust(30) + repr(self.installSaml).rjust(35) + "\n" \
                + 'Install Asimba SAML Proxy'.ljust(30) + repr(self.installAsimba).rjust(35) + "\n" \
                + 'Install CAS'.ljust(30) + repr(self.installCas).rjust(35) + "\n" \
                + 'Install oxAuth RP'.ljust(30) + repr(self.installOxAuthRP).rjust(35) + "\n" \
                + 'Install Passport '.ljust(30) + repr(self.installPassport).rjust(35) + "\n"
        except:
            s = ""
            for key in self.__dict__.keys():
                val = self.__dict__[key]
                s = s + "%s\n%s\n%s\n\n" % (key, "-" * len(key), val)
            return s

    def set_ownership(self):
        self.logIt("Changing ownership")
        realCertFolder = os.path.realpath(self.certFolder)
        realConfigFolder = os.path.realpath(self.configFolder)

        self.run([self.cmd_chown, '-R', 'jetty:jetty', realCertFolder])
        self.run([self.cmd_chown, '-R', 'jetty:jetty', realConfigFolder])
        self.run([self.cmd_chown, '-R', 'jetty:jetty', self.oxBaseDataFolder])

        # Set right permissions
        self.run([self.cmd_chmod, '-R', '550', realCertFolder])
        self.run([self.cmd_chmod, 'u+X', realCertFolder])

        if self.installOxAuth:
            self.run([self.cmd_chown, '-R', 'jetty:jetty', self.oxauth_openid_jwks_fn])
            self.run([self.cmd_chown, '-R', 'jetty:jetty', self.oxauth_openid_jks_fn])

        if self.installSaml:
            realIdp3Folder = os.path.realpath(self.idp3Folder)
            self.run([self.cmd_chown, '-R', 'jetty:jetty', realIdp3Folder])

    def get_ip(self):
        testIP = None
        detectedIP = None
        try:
            testSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            detectedIP = [(testSocket.connect(('8.8.8.8', 80)),
                           testSocket.getsockname()[0],
                           testSocket.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
        except:
            self.logIt("No detected IP address", True)
            self.logIt(traceback.format_exc(), True)
        if detectedIP:
            testIP = self.getPrompt("Enter IP Address", detectedIP)
        else:
            testIP = self.getPrompt("Enter IP Address")
        if not self.isIP(testIP):
            testIP = None
            print 'ERROR: The IP Address is invalid. Try again\n'
        return testIP

    def check_properties(self):
        self.logIt('Checking properties')
        while not self.hostname:
            testhost = raw_input('Hostname of this server: ').strip()
            if len(testhost.split('.')) >= 3:
                self.hostname = testhost
            else:
                print 'The hostname has to be at least three domain components. Try again\n'
        while not self.ip:
            self.ip = self.get_ip()
        while not self.orgName:
            self.orgName = raw_input('Organization Name: ').strip()
        while not self.countryCode:
            testCode = raw_input('2 Character Country Code: ').strip()
            if len(testCode) == 2:
                self.countryCode = testCode
            else:
                print 'Country code should only be two characters. Try again\n'
        while not self.city:
            self.city = raw_input('City: ').strip()
        while not self.state:
            self.state = raw_input('State or Province: ').strip()
        if not self.admin_email:
            tld = None
            try:
                tld = ".".join(self.hostname.split(".")[-2:])
            except:
                tld = self.hostname
            self.admin_email = "support@%s" % tld
        if not self.httpdKeyPass:
            self.httpdKeyPass = self.getPW()
        if not self.ldapPass:
            self.ldapPass = self.getPW()
        if not self.shibJksPass:
            self.shibJksPass = self.getPW()
        if not self.oxauth_openid_jks_pass:
            self.oxauth_openid_jks_pass = self.getPW()
        if not self.asimbaJksPass:
            self.asimbaJksPass = self.getPW()
        if not self.openldapKeyPass:
            self.openldapKeyPass = self.getPW()
        if not self.encode_salt:
            self.encode_salt= self.getPW() + self.getPW()
        if not self.baseInum:
            self.baseInum = '@!%s.%s.%s.%s' % tuple([self.getQuad() for i in xrange(4)])
        if not self.inumOrg:
            orgTwoQuads = '%s.%s' % tuple([self.getQuad() for i in xrange(2)])
            self.inumOrg = '%s!0001!%s' % (self.baseInum, orgTwoQuads)
        if not self.inumAppliance:
            applianceTwoQuads = '%s.%s' % tuple([self.getQuad() for i in xrange(2)])
            self.inumAppliance = '%s!0002!%s' % (self.baseInum, applianceTwoQuads)
        if not self.oxauth_client_id:
            clientTwoQuads = '%s.%s' % tuple([self.getQuad() for i in xrange(2)])
            self.oxauth_client_id = '%s!0008!%s' % (self.inumOrg, clientTwoQuads)
        if not self.scim_rs_client_id:
            scimClientTwoQuads = '%s.%s' % tuple([self.getQuad() for i in xrange(2)])
            self.scim_rs_client_id = '%s!0008!%s' % (self.inumOrg, scimClientTwoQuads)
        if not self.scim_rp_client_id:
            scimClientTwoQuads = '%s.%s' % tuple([self.getQuad() for i in xrange(2)])
            self.scim_rp_client_id = '%s!0008!%s' % (self.inumOrg, scimClientTwoQuads)
        if not self.passport_rs_client_id:
            passportClientTwoQuads = '%s.%s' % tuple([self.getQuad() for i in xrange(2)])
            self.passport_rs_client_id = '%s!0008!%s' % (self.inumOrg, passportClientTwoQuads)
        if not self.passport_rp_client_id:
            passportClientTwoQuads = '%s.%s' % tuple([self.getQuad() for i in xrange(2)])
            self.passport_rp_client_id = '%s!0008!%s' % (self.inumOrg, passportClientTwoQuads)
        if not self.inumApplianceFN:
            self.inumApplianceFN = self.inumAppliance.replace('@', '').replace('!', '').replace('.', '')
        if not self.inumOrgFN:
            self.inumOrgFN = self.inumOrg.replace('@', '').replace('!', '').replace('.', '')
        if not self.application_max_ram:
            self.application_max_ram = 3072

    def choose_from_list(self, list_of_choices, choice_name="item", default_choice_index=0):
        return_value = None
        choice_map = {}
        chosen_index = 0
        print "\nSelect the number for the %s from the following list:" % choice_name
        for choice in list_of_choices:
            choice_map[chosen_index] = choice
            chosen_index += 1
            print "  [%i]   %s" % (chosen_index, choice)
        while not return_value:
            choice_number = self.getPrompt("Please select a number listed above", str(default_choice_index + 1))
            try:
                choice_number = int(choice_number) - 1
                if (choice_number >= 0) & (choice_number < len(list_of_choices)):
                    return_value = choice_map[choice_number]
                else:
                    print '"%i" is not a valid choice' % (choice_number + 1)
            except:
                print 'Cannot convert "%s" to a number' % choice_number
                self.logIt(traceback.format_exc(), True)
        return return_value

    # = File system  =================================================================
    def findFiles(self, filePatterns, filesFolder):
        foundFiles = []
        try:
            for filePattern in filePatterns:
                fileFullPathPattern = "%s/%s" % (filesFolder, filePattern)
                for fileFullPath in glob.iglob(fileFullPathPattern):
                    foundFiles.append(fileFullPath)
        except:
            self.logIt("Error finding files %s in folder %s" % (":".join(filePatterns), filesFolder), True)
            self.logIt(traceback.format_exc(), True)

        return foundFiles

    def readFile(self, inFilePath):
        inFilePathText = None

        try:
            f = open(inFilePath)
            inFilePathText = f.read()
            f.close
        except:
            self.logIt("Error reading %s" % inFilePathText, True)
            self.logIt(traceback.format_exc(), True)

        return inFilePathText

    def writeFile(self, outFilePath, text):
        inFilePathText = None

        try:
            f = open(outFilePath, 'w')
            f.write(text)
            f.close()
        except:
            self.logIt("Error writing %s" % inFilePathText, True)
            self.logIt(traceback.format_exc(), True)

        return inFilePathText


    def copyFile(self, inFile, destFolder):
        try:
            shutil.copy(inFile, destFolder)
            self.logIt("Copied %s to %s" % (inFile, destFolder))
        except:
            self.logIt("Error copying %s to %s" % (inFile, destFolder), True)
            self.logIt(traceback.format_exc(), True)

    def copyTree(self, src, dst, symlinks=False, ignore=None):
        try:
            if not os.path.exists(dst):
                os.makedirs(dst)

            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                if os.path.isdir(s):
                    self.copyTree(s, d, symlinks, ignore)
                else:
                    if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                        shutil.copy2(s, d)

            self.logIt("Copied tree %s to %s" % (src, dst))
        except:
            self.logIt("Error copying tree %s to %s" % (src, dst), True)
            self.logIt(traceback.format_exc(), True)

    def createDirs(self, name):
        try:
            if not os.path.exists(name):
                os.makedirs(name, 0700)
                self.logIt('Created dir: %s' % name)
        except:
            self.logIt("Error making directory %s" % name, True)
            self.logIt(traceback.format_exc(), True)

    def removeDirs(self, name):
        try:
            if os.path.exists(name):
                shutil.rmtree(name)
                self.logIt('Removed dir: %s' % name)
        except:
            self.logIt("Error removing directory %s" % name, True)
            self.logIt(traceback.format_exc(), True)

    def removeFile(self, fileName):
        try:
            if os.path.exists(fileName):
                os.remove(fileName)
                self.logIt('Removed file: %s' % fileName)
        except:
            self.logIt("Error removing file %s" % fileName, True)
            self.logIt(traceback.format_exc(), True)

    # = Utilities ====================================================================

    def logIt(self, msg, errorLog=False):
        if errorLog:
            f = open(self.logError, 'a')
            f.write('%s %s\n' % (time.strftime('%X %x'), msg))
            f.close()
        f = open(self.log, 'a')
        f.write('%s %s\n' % (time.strftime('%X %x'), msg))
        f.close()

    def appendLine(self, line, fileName=False):
        try:
            f = open(fileName, 'a')
            f.write('%s\n' % line)
            f.close()
        except:
            self.logIt("Error loading file %s" % fileName)

    def setUlimits(self):
        try:
            if self.os_type in ['centos', 'redhat', 'fedora']:
                apache_user = 'apache'
            else:
                apache_user = 'www-data'

            self.appendLine("ldap       soft nofile     131072", "/etc/security/limits.conf")
            self.appendLine("ldap       hard nofile     262144", "/etc/security/limits.conf")
            self.appendLine("%s     soft nofile     131072" % apache_user, "/etc/security/limits.conf")
            self.appendLine("%s     hard nofile     262144" % apache_user, "/etc/security/limits.conf")
            self.appendLine("jetty      soft nofile     131072", "/etc/security/limits.conf")
            self.appendLine("jetty      hard nofile     262144", "/etc/security/limits.conf")
        except:
            self.logIt("Could not set limits.")
            self.logIt(traceback.format_exc(), True)

    def load_properties(self, fn):
        self.logIt('Loading Properties %s' % fn)
        p = Properties.Properties()
        try:
            p.load(open(fn))
            properties_list = p.keys()
            for prop in properties_list:
                try:
                    self.__dict__[prop] = p[prop]
                    if p[prop] == 'True':
                        self.__dict__[prop] = True
                    elif p[prop] == 'False':
                        self.__dict__[prop] = False
                except:
                    self.logIt("Error loading property %s" % prop)
                    self.logIt(traceback.format_exc(), True)
        except:
            self.logIt("Error loading properties", True)
            self.logIt(traceback.format_exc(), True)

    def load_json(self, fn):
        self.logIt('Loading JSON from %s' % fn)
        try:
            json_file = open(fn)
            json_text = json_file.read()
            json_file.close()
            return json.loads(json_text)
        except:
            self.logIt("Unable to read or parse json file from %s" % fn, True)
            self.logIt(traceback.format_exc(), True)
        return None

    # ================================================================================

    def configure_httpd(self):
        # CentOS 7.* + systemd + apache 2.4
        if self.os_type in ['centos', 'redhat', 'fedora'] and self.os_initdaemon == 'systemd' and self.apache_version == "2.4":
            self.copyFile(self.apache2_24_conf, '/etc/httpd/conf/httpd.conf')
            self.copyFile(self.apache2_ssl_24_conf, '/etc/httpd/conf.d/https_gluu.conf')

        # CentOS 6.* + init + apache 2.2
        if self.os_type == 'centos' and self.os_initdaemon == 'init':
            self.copyFile(self.apache2_conf, '/etc/httpd/conf/httpd.conf')
            self.copyFile(self.apache2_ssl_conf, '/etc/httpd/conf.d/https_gluu.conf')
        if self.os_type in ['redhat', 'fedora'] and self.os_initdaemon == 'init':
            self.copyFile(self.apache2_conf, '/etc/httpd/conf/httpd.conf')
            self.copyFile(self.apache2_ssl_conf, '/etc/httpd/conf.d/https_gluu.conf')
        if self.os_type in ['debian', 'ubuntu']:
            self.copyFile(self.apache2_ssl_conf, '/etc/apache2/sites-available/https_gluu.conf')
            self.run([self.cmd_ln, '-s', '/etc/apache2/sites-available/https_gluu.conf',
                      '/etc/apache2/sites-enabled/https_gluu.conf'])

    def copy_output(self):
        self.logIt("Copying rendered templates to final destination")

        # Detect sevice path and apache service name
        service_path = '/sbin/service'
        apache_service_name = 'httpd'
        if self.os_type in ['debian', 'ubuntu']:
            service_path = '/usr/sbin/service'
            apache_service_name = 'apache2'

        self.run([service_path, apache_service_name, 'stop'])
        for dest_fn in self.ce_templates.keys():
            if self.ce_templates[dest_fn]:
                fn = os.path.split(dest_fn)[-1]
                output_fn = os.path.join(self.outputFolder, fn)
                try:
                    self.logIt("Copying %s to %s" % (output_fn, dest_fn))
                    dest_dir = os.path.dirname(dest_fn)
                    if not os.path.exists(dest_dir):
                        self.logIt("Created destination folder %s" % dest_dir)
                        os.makedirs(dest_dir)
                    shutil.copyfile(output_fn, dest_fn)
                except:
                    self.logIt("Error writing %s to %s" % (output_fn, dest_fn), True)
                    self.logIt(traceback.format_exc(), True)

        self.run([service_path, apache_service_name, 'start'])

    def copy_scripts(self):
        self.logIt("Copying script files")
        for script in self.gluuScriptFiles:
            self.copyFile(script, self.gluuOptBinFolder)
        self.logIt("Rendering encode.py")
        try:
            f = open('%s/encode.py' % self.templateFolder)
            encode_script = f.read()
            f.close()
            f = open("%s/encode.py" % self.gluuOptBinFolder, 'w')
            f.write(encode_script % self.merge_dicts(self.__dict__, self.templateRenderingDict))
            f.close()
        except:
            self.logIt("Error rendering encode script")
            self.logIt(traceback.format_exc(), True)
        self.run([self.cmd_chmod, '-R', '700', self.gluuOptBinFolder])

    def copy_static(self):
        if self.installSaml:
            self.copyTree("%s/static/idp3/conf/" % self.install_dir, self.idp3ConfFolder)
            self.copyFile("%s/static/idp3/metadata/idp-metadata.xml" % self.install_dir, "%s/" % self.idp3MetadataFolder)

        if self.installOxAuth:
            self.copyFile("%s/static/auth/lib/duo_web.py" % self.install_dir, "%s/conf/python/" % self.gluuBaseFolder)
            self.copyFile("%s/static/auth/conf/duo_creds.json" % self.install_dir, "%s/" % self.certFolder)
            self.copyFile("%s/static/auth/conf/gplus_client_secrets.json" % self.install_dir, "%s/" % self.certFolder)
            self.copyFile("%s/static/auth/conf/super_gluu_creds.json" % self.install_dir, "%s/" % self.certFolder)
            self.copyFile("%s/static/auth/conf/cert_creds.json" % self.install_dir, "%s/" % self.certFolder)
            self.copyFile("%s/static/auth/conf/otp_configuration.json" % self.install_dir, "%s/" % self.certFolder)

    def detect_os_type(self):
        # TODO: Change this to support more distros. For example according to
        # http://unix.stackexchange.com/questions/6345/how-can-i-get-distribution-name-and-version-number-in-a-simple-shell-script
        distro_info = self.readFile('/etc/redhat-release')
        if distro_info == None:
            distro_info = self.readFile('/etc/os-release')

        if 'CentOS' in distro_info:
            return self.os_types[0]
        elif 'Red Hat' in distro_info:
            return self.os_types[1]
        elif 'Ubuntu' in distro_info:
            return self.os_types[3]
        elif 'Debian' in distro_info:
            return self.os_types[4]

        else:
            return self.choose_from_list(self.os_types, "Operating System")

    def detect_initd(self):
        return open(os.path.join('/proc/1/status'), 'r').read().split()[1]

    def determineApacheVersion(self, apache_cmd):
        cmd = "/usr/sbin/%s -v | egrep '^Server version'" % apache_cmd
        PIPE = subprocess.PIPE
        p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT, close_fds=True, cwd=None)
        apache_version = p.stdout.read().strip().split(' ')[2].split('/')[1]
        if re.match(r'2\.4\..*', apache_version):
            return "2.4"

        return "2.2"

    def determineApacheVersionForOS(self):
        if self.os_type in ['centos', 'redhat', 'fedora']:
            # httpd -v
            # Server version: Apache/2.2.15 (Unix)  /etc/redhat-release  CentOS release 6.7 (Final)
            # OR
            # Server version: Apache/2.4.6 (CentOS) /etc/redhat-release  CentOS Linux release 7.1.1503 (Core)
            return self.determineApacheVersion("httpd")
        else:
            return self.determineApacheVersion("apache2")

    def determineOpenDJVersion(self):
        f = open('/opt/opendj/template/config/buildinfo', 'r')
        encode_script = f.read().split()[0]
        f.close()

        if re.match(r'2\.6\.0\..*', encode_script):
            return "2.6"

        return "3.0"

    def installJRE(self):
        self.logIt("Installing server JRE 1.8 %s..." % self.jre_version)

        jreArchive = 'server-jre-8u%s-linux-x64.tar.gz' % self.jre_version
        jreDestinationPath = '/opt/jdk1.8.0_%s' % self.jre_version
        try:
            self.logIt("Extracting %s in /opt/" % jreArchive)
            self.run(['tar', '-xzf', '%s/%s' % (self.distAppFolder, jreArchive), '-C', '/opt/', '--no-xattrs', '--no-same-owner', '--no-same-permissions'])
        except:
            self.logIt("Error encountered while extracting archive %s" % jreArchive)
            self.logIt(traceback.format_exc(), True)

        self.run([self.cmd_ln, '-sf', jreDestinationPath, self.jre_home])
        self.run([self.cmd_chmod, '-R', "755", "%s/bin/" % jreDestinationPath])
        self.run([self.cmd_chown, '-R', 'root:root', jreDestinationPath])
        self.run([self.cmd_chown, '-h', 'root:root', self.jre_home])

    def extractOpenDJ(self):
        openDJArchive = 'opendj-server-3.0.0.zip'
        try:
            self.logIt("Unzipping %s in /opt/" % openDJArchive)
            self.run(['unzip', '-n', '-q', '%s/%s' % (self.distAppFolder, openDJArchive), '-d', '/opt/' ])
        except:
            self.logIt("Error encountered while doing unzip %s/%s -d /opt/" % (self.distAppFolder, openDJArchive))
            self.logIt(traceback.format_exc(), True)

        realLdapBaseFolder = os.path.realpath(self.ldapBaseFolder)
        self.run([self.cmd_chown, '-R', 'ldap:ldap', realLdapBaseFolder])

    def installJetty(self):
        self.logIt("Installing jetty %s..." % self.jetty_version)

        jettyTemp = '%s/temp' % self.jetty_dist
        self.run([self.cmd_mkdir, '-p', jettyTemp])
        self.run([self.cmd_chown, '-R', 'jetty:jetty', jettyTemp])

        jettyArchive = 'jetty-distribution-%s.tar.gz' % self.jetty_version
        jettyDestinationPath = '%s/jetty-distribution-%s' % (self.jetty_dist, self.jetty_version)
        try:
            self.logIt("Extracting %s into /opt/jetty" % jettyArchive)
            self.run(['tar', '-xzf', '%s/%s' % (self.distAppFolder, jettyArchive), '-C', self.jetty_dist, '--no-xattrs', '--no-same-owner', '--no-same-permissions'])
        except:
            self.logIt("Error encountered while extracting archive %s" % jettyArchive)
            self.logIt(traceback.format_exc(), True)

        self.run([self.cmd_ln, '-sf', jettyDestinationPath, self.jetty_home])
        self.run([self.cmd_chmod, '-R', "755", "%s/bin/" % jettyDestinationPath])
        self.run([self.cmd_chown, '-R', 'root:root', jettyDestinationPath])
        self.run([self.cmd_chown, '-h', 'root:root', self.jetty_home])

        self.run([self.cmd_mkdir, '-p', self.jetty_base])
        self.run([self.cmd_chown, '-R', 'jetty:jetty', self.jetty_base])

    def installNode(self):
        self.logIt("Installing node %s..." % self.node_version)

        nodeArchive = 'node-v%s-linux-x64.tar.xz' % self.node_version
        nodeDestinationPath = '/opt/node-v%s-linux-x64' % self.node_version
        try:
            self.logIt("Extracting %s into /opt" % nodeArchive)
            self.run(['tar', '-xJf', '%s/%s' % (self.distAppFolder, nodeArchive), '-C', '/opt/', '--no-xattrs', '--no-same-owner', '--no-same-permissions'])
        except:
            self.logIt("Error encountered while extracting archive %s" % nodeArchive)
            self.logIt(traceback.format_exc(), True)

        self.run([self.cmd_ln, '-sf', nodeDestinationPath, self.node_home])
        self.run([self.cmd_chmod, '-R', "755", "%s/bin/" % nodeDestinationPath])
        self.run([self.cmd_chown, '-R', 'jetty:jetty', nodeDestinationPath])
        self.run([self.cmd_chown, '-h', 'jetty:jetty', self.node_home])

    def installJettyService(self, serviceConfiguration, supportCustomizations=False):
        serviceName = serviceConfiguration['name']
        self.logIt("Installing jetty service %s..." % serviceName)
        jettyServiceBase = '%s/%s' % (self.jetty_base, serviceName)
        jettyModules = serviceConfiguration['jetty']['modules']
        jettyModulesList = jettyModules.split(',')

        self.logIt("Preparing %s service base folders" % serviceName)
        self.run([self.cmd_mkdir, '-p', jettyServiceBase])

        # Create ./ext/lib folder for custom libraries only if installed Jetty "ext" module 
        if "ext" in jettyModulesList:
            self.run([self.cmd_mkdir, '-p', "%s/lib/ext" % jettyServiceBase])
            
        # Create ./pages and ./web-resources folders for custom pages only if application supports thme 
        if supportCustomizations:
            self.run([self.cmd_mkdir, '-p', "%s/pages" % jettyServiceBase])
            self.run([self.cmd_mkdir, '-p', "%s/web-resources" % jettyServiceBase])

        self.logIt("Preparing %s service base configuration" % serviceName)
        jettyEnv = os.environ.copy()
        jettyEnv['PATH'] = '%s/bin:' % self.jre_home + jettyEnv['PATH']

        self.run([self.cmd_java, '-jar', '%s/start.jar' % self.jetty_home, 'jetty.home=%s' % self.jetty_home, 'jetty.base=%s' % jettyServiceBase, '--add-to-start=%s' % jettyModules], None, jettyEnv)
        self.run([self.cmd_chown, '-R', 'jetty:jetty', jettyServiceBase])

        jettyServiceConfiguration = '%s/jetty/%s' % (self.outputFolder, serviceName)
        self.copyFile(jettyServiceConfiguration, "/etc/default")
        self.run([self.cmd_chown, 'root:root', "/etc/default/%s" % serviceName])

        self.run([self.cmd_ln, '-sf', '%s/bin/jetty.sh' % self.jetty_home, '/etc/init.d/%s' % serviceName])

        # Enable service autoload on Gluu-Server startup
        if self.os_type in ['centos', 'fedora', 'redhat']:
            if self.os_initdaemon == 'systemd':
                self.run(["/usr/bin/systemctl", 'enable', serviceName])
            else:
                self.run(["/sbin/chkconfig", serviceName, "on"])
        elif self.os_type in ['ubuntu', 'debian']:
            self.run(["/usr/sbin/update-rc.d", serviceName, 'defaults', '60', '20'])

        serviceConfiguration['installed'] = True

    def installJython(self):
        self.logIt("Installing Jython %s..." % self.jython_version)
        jythonInstaller = 'jython-%s.jar' % self.jython_version

        try:
            self.run(['rm', '-fr', '/opt/jython-%s' % self.jython_version])
            self.run([self.cmd_java, '-jar', '%s/jython-installer-%s.jar' % (self.distAppFolder, self.jython_version), '-v', '-s', '-d', '/opt/jython-%s' % self.jython_version, '-t', 'standard', '-e', 'ensurepip'])
        except:
            self.logIt("Error installing jython-installer-%s.jar" % self.jython_version)
            self.logIt(traceback.format_exc(), True)

        self.run([self.cmd_ln, '-sf', '/opt/jython-%s' % self.jython_version, '/opt/jython'])
        self.run([self.cmd_chown, '-R', 'root:root', '/opt/jython-%s' % self.jython_version])
        self.run([self.cmd_chown, '-h', 'root:root', '/opt/jython'])

    def downloadWarFiles(self):
        if self.downloadWars:
            print "Downloading oxAuth war file..."
            self.run(['/usr/bin/wget', self.oxauth_war, '--no-verbose', '--retry-connrefused', '--tries=10', '-O', '%s/oxauth.war' % self.distAppFolder])
            print "Downloading oxTrust war file..."
            self.run(['/usr/bin/wget', self.oxtrust_war, '--no-verbose', '--retry-connrefused', '--tries=10', '-O', '%s/identity.war' % self.distAppFolder])
            print "Downloading CAS war file..."
            self.run(['/usr/bin/wget', self.cas_war, '--no-verbose', '--retry-connrefused', '--tries=10', '-O', '%s/cas.war' % self.distAppFolder])

            print "Finished downloading latest war files"

        if self.installAsimba:
            # Asimba is not part of CE package. We need to download it if needed
            distAsimbaPath = '%s/%s' % (self.distWarFolder, "asimba.war")
            if not os.path.exists(distAsimbaPath):
                print "Downloading Asimba war file..."
                self.run(['/usr/bin/wget', self.asimba_war, '--no-verbose', '--retry-connrefused', '--tries=10', '-O', '%s/asimba.war' % self.distWarFolder])

        if self.installOxAuthRP:
            # oxAuth RP is not part of CE package. We need to download it if needed
            distOxAuthRpPath = '%s/%s' % (self.distWarFolder, "oxauth-rp.war")
            if not os.path.exists(distOxAuthRpPath):
                print "Downloading oxAuth RP war file..."
                self.run(['/usr/bin/wget', self.oxauth_rp_war, '--no-verbose', '--retry-connrefused', '--tries=10', '-O', '%s/oxauth-rp.war' % self.distWarFolder])

        if self.downloadWars and self.installSaml:
            print "Downloading Shibboleth IDP v3 war file..."
            self.run(['/usr/bin/wget', self.idp3_war, '--no-verbose', '-c', '--retry-connrefused', '--tries=10', '-O', '%s/idp.war' % self.distWarFolder])
            print "Downloading Shibboleth IDP v3 keygenerator..."
            self.run(['/usr/bin/wget', self.idp3_cml_keygenerator, '--no-verbose', '-c', '--retry-connrefused', '--tries=10', '-O', self.distWarFolder + '/idp3_cml_keygenerator.jar'])
            print "Downloading Shibboleth IDP v3 binary distributive file..."
            self.run(['/usr/bin/wget', self.idp3_dist_jar, '--no-verbose', '-c', '--retry-connrefused', '--tries=10', '-O', self.distWarFolder + '/shibboleth-idp.jar'])

    def encode_passwords(self):
        self.logIt("Encoding passwords")
        try:
            self.encoded_ldap_pw = self.ldap_encode(self.ldapPass)

            cmd = "%s %s" % (self.oxEncodePWCommand, self.shibJksPass)
            self.encoded_shib_jks_pw = os.popen(cmd, 'r').read().strip()
            cmd = "%s %s" % (self.oxEncodePWCommand, self.ldapPass)
            self.encoded_ox_ldap_pw = os.popen(cmd, 'r').read().strip()
            self.oxauthClient_pw = self.getPW()
            cmd = "%s %s" % (self.oxEncodePWCommand, self.oxauthClient_pw)
            self.oxauthClient_encoded_pw = os.popen(cmd, 'r').read().strip()
        except:
            self.logIt("Error encoding passwords", True)
            self.logIt(traceback.format_exc(), True)

    def encode_test_passwords(self):
        self.logIt("Encoding test passwords")
        try:
            self.templateRenderingDict['oxauthClient_2_pw'] = self.getPW()
            cmd = "%s %s" % (self.oxEncodePWCommand, self.templateRenderingDict['oxauthClient_2_pw'])
            self.templateRenderingDict['oxauthClient_2_encoded_pw'] = os.popen(cmd, 'r').read().strip()

            self.templateRenderingDict['oxauthClient_3_pw'] = self.getPW()
            cmd = "%s %s" % (self.oxEncodePWCommand, self.templateRenderingDict['oxauthClient_3_pw'])
            self.templateRenderingDict['oxauthClient_3_encoded_pw'] = os.popen(cmd, 'r').read().strip()

            self.templateRenderingDict['oxauthClient_4_pw'] = self.getPW()
            cmd = "%s %s" % (self.oxEncodePWCommand, self.templateRenderingDict['oxauthClient_4_pw'])
            self.templateRenderingDict['oxauthClient_4_encoded_pw'] = os.popen(cmd, 'r').read().strip()
        except:
            self.logIt("Error encoding test passwords", True)
            self.logIt(traceback.format_exc(), True)

    def gen_cert(self, suffix, password, user='root', cn=None):
        self.logIt('Generating Certificate for %s' % suffix)
        key_with_password = '%s/%s.key.orig' % (self.certFolder, suffix)
        key = '%s/%s.key' % (self.certFolder, suffix)
        csr = '%s/%s.csr' % (self.certFolder, suffix)
        public_certificate = '%s/%s.crt' % (self.certFolder, suffix)
        self.run([self.opensslCommand,
                  'genrsa',
                  '-des3',
                  '-out',
                  key_with_password,
                  '-passout',
                  'pass:%s' % password,
                  '2048'
        ])
        self.run([self.opensslCommand,
                  'rsa',
                  '-in',
                  key_with_password,
                  '-passin',
                  'pass:%s' % password,
                  '-out',
                  key
        ])

        certCn = cn
        if certCn == None:
            certCn = self.hostname
             
        self.run([self.opensslCommand,
                  'req',
                  '-new',
                  '-key',
                  key,
                  '-out',
                  csr,
                  '-subj',
                  '/C=%s/ST=%s/L=%s/O=%s/CN=%s/emailAddress=%s' % (self.countryCode, self.state, self.city, self.orgName, certCn, self.admin_email)
        ])
        self.run([self.opensslCommand,
                  'x509',
                  '-req',
                  '-days',
                  '365',
                  '-in',
                  csr,
                  '-signkey',
                  key,
                  '-out',
                  public_certificate
        ])
        self.run([self.cmd_chown, '%s:%s' % (user, user), key_with_password])
        self.run([self.cmd_chmod, '700', key_with_password])
        self.run([self.cmd_chown, '%s:%s' % (user, user), key])
        self.run([self.cmd_chmod, '700', key])

        self.run([self.cmd_keytool, "-import", "-trustcacerts", "-alias", "%s_%s" % (self.hostname, suffix), \
                  "-file", public_certificate, "-keystore", self.defaultTrustStoreFN, \
                  "-storepass", "changeit", "-noprompt"])

    def generate_crypto(self):
        try:
            self.logIt('Generating certificates and keystores')
            self.gen_cert('httpd', self.httpdKeyPass, 'jetty')
            self.gen_cert('shibIDP', self.shibJksPass, 'jetty')
            self.gen_cert('idp-encryption', self.shibJksPass, 'jetty')
            self.gen_cert('idp-signing', self.shibJksPass, 'jetty')
            self.gen_cert('asimba', self.asimbaJksPass, 'jetty')
            self.gen_cert('openldap', self.openldapKeyPass, 'ldap', "localhost")
            # Shibboleth IDP and Asimba will be added soon...
            self.gen_keystore('shibIDP',
                              self.shibJksFn,
                              self.shibJksPass,
                              '%s/shibIDP.key' % self.certFolder,
                              '%s/shibIDP.crt' % self.certFolder,
                              'jetty')
            self.gen_keystore('asimba',
                              self.asimbaJksFn,
                              self.asimbaJksPass,
                              '%s/asimba.key' % self.certFolder,
                              '%s/asimba.crt' % self.certFolder,
                              'jetty')
            self.run([self.cmd_chown, '-R', 'jetty:jetty', self.certFolder])
            self.run([self.cmd_chmod, '-R', '500', self.certFolder])
            # oxTrust UI can add key to asimba's keystore
            self.run([self.cmd_chmod, 'u+w', self.asimbaJksFn])
        except:
            self.logIt("Error generating cyrpto")
            self.logIt(traceback.format_exc(), True)

    def gen_keystore(self, suffix, keystoreFN, keystorePW, inKey, inCert, user='root'):
        self.logIt("Creating keystore %s" % suffix)
        # Convert key to pkcs12
        pkcs_fn = '%s/%s.pkcs12' % (self.certFolder, suffix)
        self.run([self.opensslCommand,
                  'pkcs12',
                  '-export',
                  '-inkey',
                  inKey,
                  '-in',
                  inCert,
                  '-out',
                  pkcs_fn,
                  '-name',
                  self.hostname,
                  '-passout',
                  'pass:%s' % keystorePW
        ])
        # Import p12 to keystore
        self.run([self.cmd_keytool,
                  '-importkeystore',
                  '-srckeystore',
                  '%s/%s.pkcs12' % (self.certFolder, suffix),
                  '-srcstorepass',
                  keystorePW,
                  '-srcstoretype',
                  'PKCS12',
                  '-destkeystore',
                  keystoreFN,
                  '-deststorepass',
                  keystorePW,
                  '-deststoretype',
                  'JKS',
                  '-keyalg',
                  'RSA',
                  '-noprompt'
        ])
        self.run([self.cmd_chown, '%s:%s' % (user, user), pkcs_fn])
        self.run([self.cmd_chmod, '700', pkcs_fn])
        self.run([self.cmd_chown, '%s:%s' % (user, user), keystoreFN])
        self.run([self.cmd_chmod, '700', keystoreFN])

    def gen_openid_jwks_jks_keys(self, jks_path, jks_pwd, jks_create = True, key_expiration = None, dn_name = None, key_algs = None):
        self.logIt("Generating oxAuth OpenID Connect keys")

        if dn_name == None:
            dn_name = self.default_openid_jks_dn_name

        if key_algs == None:
            key_algs = self.default_key_algs

        if key_expiration == None:
            key_expiration = self.default_key_expiration


        # We can remove this once KeyGenerator will do the same
        if jks_create == True:
            self.logIt("Creating empty JKS keystore")
            # Create JKS with dummy key
            cmd = " ".join([self.cmd_keytool,
                      '-genkey',
                      '-alias',
                      'dummy',
                      '-keystore',
                      jks_path,
                      '-storepass',
                      jks_pwd,
                      '-keypass',
                      jks_pwd,
                      '-dname',
                      '"%s"' % dn_name])
            self.run(['/bin/sh', '-c', cmd])

            # Delete dummy key from JKS
            cmd = " ".join([self.cmd_keytool,
                      '-delete',
                      '-alias',
                      'dummy',
                      '-keystore',
                      jks_path,
                      '-storepass',
                      jks_pwd,
                      '-keypass',
                      jks_pwd,
                      '-dname',
                      '"%s"' % dn_name])
            self.run(['/bin/sh', '-c', cmd])

        oxauth_lib_files = self.findFiles(self.oxauth_keys_utils_libs, self.jetty_user_home_lib)

        cmd = " ".join([self.cmd_java,
                        "-Dlog4j.defaultInitOverride=true",
                        "-cp",
                        ":".join(oxauth_lib_files),
                        "org.xdi.oxauth.util.KeyGenerator",
                        "-keystore",
                        jks_path,
                        "-keypasswd",
                        jks_pwd,
                        "-algorithms",
                        "%s" % key_algs,
                        "-dnname",
                        '"%s"' % dn_name,
                        "-expiration",
                        "%s" % key_expiration])
        args = ['/bin/sh', '-c', cmd]

        self.logIt("Runnning: %s" % " ".join(args))
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, err = p.communicate()
            p.wait()
            if err:
                self.logIt(err, True)
            if output:
                return output.split(os.linesep)
        except:
            self.logIt("Error running command : %s" % " ".join(args), True)
            self.logIt(traceback.format_exc(), True)

        return None

    def export_openid_key(self, jks_path, jks_pwd, cert_alias, cert_path):
        self.logIt("Exporting oxAuth OpenID Connect keys")

        oxauth_lib_files = self.findFiles(self.oxauth_keys_utils_libs, self.jetty_user_home_lib)

        cmd = " ".join([self.cmd_java,
                        "-Dlog4j.defaultInitOverride=true",
                        "-cp",
                        ":".join(oxauth_lib_files),
                        "org.xdi.oxauth.util.KeyExporter",
                        "-keystore",
                        jks_path,
                        "-keypasswd",
                        jks_pwd,
                        "-alias",
                        cert_alias,
                        "-exportfile",
                        cert_path])
        self.run(['/bin/sh', '-c', cmd])

    def write_openid_keys(self, fn, jwks):
        self.logIt("Writing oxAuth OpenID Connect keys")
        if not jwks:
            self.logIt("Failed to write oxAuth OpenID Connect key to %s" % fn)
            return

        try:
            jwks_text = '\n'.join(jwks)
            f = open(fn, 'w')
            f.write(jwks_text)
            f.close()
            self.run([self.cmd_chown, 'jetty:jetty', fn])
            self.run([self.cmd_chmod, '600', fn])
            self.logIt("Wrote oxAuth OpenID Connect key to %s" % fn)
        except:
            self.logIt("Error writing command : %s" % fn, True)
            self.logIt(traceback.format_exc(), True)

    def generate_oxauth_openid_keys(self):
        jwks = self.gen_openid_jwks_jks_keys(self.oxauth_openid_jks_fn, self.oxauth_openid_jks_pass)
        self.write_openid_keys(self.oxauth_openid_jwks_fn, jwks)

    def generate_base64_string(self, lines, num_spaces):
        if not lines:
            return None

        plain_text = ''.join(lines)
        plain_b64encoded_text = plain_text.encode('base64').strip()

        if num_spaces > 0:
            plain_b64encoded_text = self.reindent(plain_b64encoded_text, num_spaces)

        return plain_b64encoded_text

    def genRandomString(self, N):
        return ''.join(random.SystemRandom().choice(string.ascii_lowercase
                                     + string.ascii_uppercase
                                     + string.digits) for _ in range(N))

    def generate_scim_configuration(self):
        self.scim_rs_client_jks_pass = self.getPW()

        cmd = "%s %s" % (self.oxEncodePWCommand, self.scim_rs_client_jks_pass)
        self.scim_rs_client_jks_pass_encoded = os.popen(cmd, 'r').read().strip()

        self.scim_rs_client_jwks = self.gen_openid_jwks_jks_keys(self.scim_rs_client_jks_fn, self.scim_rs_client_jks_pass)
        self.templateRenderingDict['scim_rs_client_base64_jwks'] = self.generate_base64_string(self.scim_rs_client_jwks, 1)

        self.scim_rp_client_jwks = self.gen_openid_jwks_jks_keys(self.scim_rp_client_jks_fn, self.scim_rp_client_jks_pass)
        self.templateRenderingDict['scim_rp_client_base64_jwks'] = self.generate_base64_string(self.scim_rp_client_jwks, 1)

    def generate_passport_configuration(self):
        self.passport_rs_client_jks_pass = self.getPW()

        cmd = "%s %s" % (self.oxEncodePWCommand, self.passport_rs_client_jks_pass)
        self.passport_rs_client_jks_pass_encoded = os.popen(cmd, 'r').read().strip()

        self.passport_rs_client_jwks = self.gen_openid_jwks_jks_keys(self.passport_rs_client_jks_fn, self.passport_rs_client_jks_pass)
        self.templateRenderingDict['passport_rs_client_base64_jwks'] = self.generate_base64_string(self.passport_rs_client_jwks, 1)

        self.passport_rp_client_jwks = self.gen_openid_jwks_jks_keys(self.passport_rp_client_jks_fn, self.passport_rp_client_jks_pass)
        self.templateRenderingDict['passport_rp_client_base64_jwks'] = self.generate_base64_string(self.passport_rp_client_jwks, 1)

    def getPrompt(self, prompt, defaultValue=None):
        try:
            if defaultValue:
                user_input = raw_input("%s [%s] : " % (prompt, defaultValue)).strip()
                if user_input == '':
                    return defaultValue
                else:
                    return user_input
            else:
                input = False
                while not input:
                    user_input = raw_input("%s : " % prompt).strip()
                    if user_input != '':
                        input = True
                        return user_input
        except KeyboardInterrupt:
            sys.exit()
        except:
            return None

    def getPW(self, size=12, chars=string.ascii_uppercase + string.digits + string.lowercase):
        return ''.join(random.choice(chars) for _ in range(size))

    def getQuad(self):
        return str(uuid.uuid4())[:4].upper()

    def prepare_openid_keys_generator(self):
        self.logIt("Preparing files needed to run OpenId keys generator")
        # Unpack oxauth.war to get libs needed to run key generator
        oxauthWar = 'oxauth.war'
        distOxAuthPath = '%s/%s' % (self.distWarFolder, oxauthWar)

        tmpOxAuthDir = '%s/tmp_oxauth' % self.distWarFolder

        self.logIt("Unpacking %s..." % oxauthWar)
        self.removeDirs(tmpOxAuthDir)
        self.createDirs(tmpOxAuthDir)

        self.run([self.cmd_jar,
                  'xf',
                  distOxAuthPath], tmpOxAuthDir)

        tmpLibsOxAuthPath = '%s/WEB-INF/lib' % tmpOxAuthDir

        self.logIt("Copying files to %s..." % self.jetty_user_home_lib)
        oxauth_lib_files = self.findFiles(self.oxauth_keys_utils_libs, tmpLibsOxAuthPath)
        for oxauth_lib_file in oxauth_lib_files:
            self.copyFile(oxauth_lib_file, self.jetty_user_home_lib)

        self.removeDirs(tmpOxAuthDir)

    def install_gluu_base(self):
        self.logIt("Installing Gluu base...")
        self.prepare_openid_keys_generator()

        self.generate_scim_configuration()
        self.generate_passport_configuration()

        self.ldap_binddn = self.openldapRootUser

        if self.installSaml:
            self.oxTrustConfigGeneration = "true"
        else:
            self.oxTrustConfigGeneration = "false"

    def load_certificate_text(self, filePath):
        self.logIt("Load certificate %s" % filePath)
        f = open(filePath)
        certificate_text = f.read()
        f.close()
        certificate_text = certificate_text.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').strip()
        return certificate_text

    def install_oxauth(self):
        self.logIt("Copying identity.war into jetty webapps folder...")

        jettyServiceName = 'oxauth'
        self.installJettyService(self.jetty_app_configuration[jettyServiceName], True)

        jettyServiceWebapps = '%s/%s/webapps' % (self.jetty_base, jettyServiceName)
        self.copyFile('%s/oxauth.war' % self.distWarFolder, jettyServiceWebapps)

    def install_oxtrust(self):
        self.logIt("Copying oxauth.war into jetty webapps folder...")

        jettyServiceName = 'identity'
        self.installJettyService(self.jetty_app_configuration[jettyServiceName], True)

        jettyServiceWebapps = '%s/%s/webapps' % (self.jetty_base, jettyServiceName)
        self.copyFile('%s/identity.war' % self.distWarFolder, jettyServiceWebapps)

    def install_saml(self):
        if self.installSaml:
            self.logIt("Install SAML Shibboleth IDP v3...")

            # Put latest SAML templates
            identityWar = 'identity.war'
            distIdentityPath = '%s/%s' % (self.distWarFolder, identityWar)

            tmpIdentityDir = '%s/tmp_identity' % self.distWarFolder

            self.logIt("Unpacking %s from %s..." % ('oxtrust-configuration.jar', identityWar))
            self.removeDirs(tmpIdentityDir)
            self.createDirs(tmpIdentityDir)

            identityConfFilePattern = 'WEB-INF/lib/oxtrust-configuration-%s.jar' % self.oxVersion

            self.run([self.cmd_jar,
                      'xf',
                      distIdentityPath], tmpIdentityDir)

            self.logIt("Unpacking %s..." % 'oxtrust-configuration.jar')
            self.run([self.cmd_jar,
                      'xf',
                      identityConfFilePattern], tmpIdentityDir)

            self.logIt("Preparing SAML templates...")
            self.removeDirs('%s/conf/shibboleth3' % self.gluuBaseFolder)
            self.createDirs('%s/conf/shibboleth3/idp' % self.gluuBaseFolder)

            # Put IDP templates to oxTrust conf folder
            jettyIdentityServiceName = 'identity'
            jettyIdentityServiceConf = '%s/%s/conf' % (self.jetty_base, jettyIdentityServiceName)
            self.run([self.cmd_mkdir, '-p', jettyIdentityServiceConf])

            self.copyTree('%s/shibboleth3' % tmpIdentityDir, '%s/shibboleth3' % jettyIdentityServiceConf)

            self.removeDirs(tmpIdentityDir)

            # unpack IDP3 JAR with static configs
            self.run([self.cmd_jar, 'xf', self.distWarFolder + '/shibboleth-idp.jar'], '/opt')
            self.removeDirs('/opt/META-INF')

            # copy templates
            self.copyFile(self.staticIDP3FolderConf + self.idp3_configuration_properties, self.idp3ConfFolder + self.idp3_configuration_properties)
            self.copyFile(self.staticIDP3FolderConf + self.idp3_configuration_ldap_properties, self.idp3ConfFolder + self.idp3_configuration_ldap_properties)
            self.copyFile(self.staticIDP3FolderConf + self.idp3_configuration_saml_nameid, self.idp3ConfFolder + self.idp3_configuration_saml_nameid)
            self.copyFile(self.staticIDP3FolderConf + self.idp3_configuration_services, self.idp3ConfFolder + self.idp3_configuration_services)
            self.copyFile(self.staticIDP3FolderConf + self.idp3_configuration_password_authn, self.idp3ConfFolder + self.idp3_configuration_password_authn)
            self.copyFile(self.staticIDP3FolderMetadata + self.idp3_metadata, self.idp3MetadataFolder + self.idp3_metadata)

            # Process templates
            self.renderTemplateInOut(self.idp3ConfFolder + self.idp3_configuration_properties, self.idp3ConfFolder, self.idp3ConfFolder)
            self.renderTemplateInOut(self.idp3ConfFolder + self.idp3_configuration_ldap_properties, self.idp3ConfFolder, self.idp3ConfFolder)
            self.renderTemplateInOut(self.idp3ConfFolder + self.idp3_configuration_saml_nameid, self.idp3ConfFolder, self.idp3ConfFolder)
            self.renderTemplateInOut(self.idp3ConfFolder + self.idp3_configuration_services, self.idp3ConfFolder, self.idp3ConfFolder)
            self.renderTemplateInOut(self.idp3ConfFolder + self.idp3_configuration_password_authn, self.idp3ConfFolder + '/authn', self.idp3ConfFolder + '/authn')

            # load certificates to update metadata
            self.idp3EncryptionCertificateText = self.load_certificate_text(self.certFolder + '/idp-encryption.crt')
            self.idp3SigningCertificateText = self.load_certificate_text(self.certFolder + '/idp-signing.crt')
            # update IDP3 metadata
            self.renderTemplateInOut(self.idp3MetadataFolder + self.idp3_metadata, self.idp3MetadataFolder, self.idp3MetadataFolder)

            self.idpWarFullPath = '%s/idp.war' % self.distWarFolder

            # generate new keystore with AES symmetric key
            # there is one throuble with IDP3 - it doesn't load keystore from /etc/certs. It acceptas %{idp.home}/credentials/sealer.jks  %{idp.home}/credentials/sealer.kver format only.
            self.run([self.cmd_java,'-classpath', self.distWarFolder + '/idp3_cml_keygenerator.jar', 'org.xdi.oxshibboleth.keygenerator.KeyGenerator', self.idp3CredentialsFolder, self.shibJksPass], self.idp3CredentialsFolder)

            jettyIdpServiceName = 'idp'
            jettyIdpServiceWebapps = '%s/%s/webapps' % (self.jetty_base, jettyIdpServiceName)

            self.installJettyService(self.jetty_app_configuration[jettyIdpServiceName])
            self.copyFile('%s/idp.war' % self.distWarFolder, jettyIdpServiceWebapps)

            # chown -R jetty:jetty /opt/shibboleth-idp
            # self.run([self.cmd_chown,'-R', 'jetty:jetty', self.idp3Folder], '/opt')
            self.run([self.cmd_chown, '-R', 'jetty:jetty', jettyIdpServiceWebapps], '/opt')

    def install_asimba(self):
        asimbaWar = 'asimba.war'
        distAsimbaPath = '%s/%s' % (self.distWarFolder, asimbaWar)

        tmpAsimbaDir = '%s/tmp_asimba' % self.distTmpFolder

        self.logIt("Unpacking %s..." % asimbaWar)
        self.removeDirs(tmpAsimbaDir)
        self.createDirs(tmpAsimbaDir)

        self.run([self.cmd_jar,
                  'xf',
                  distAsimbaPath], tmpAsimbaDir)

        self.logIt("Configuring Asimba...")
        self.copyFile(self.asimba_configuration, '%s/WEB-INF/conf/asimba.xml' % tmpAsimbaDir)
        self.copyFile(self.asimba_properties, '%s/WEB-INF/asimba.properties' % tmpAsimbaDir)

        self.logIt("Generating asimba.war...")
        self.run([self.cmd_jar,
                  'cmf',
                  'tmp_asimba/META-INF/MANIFEST.MF',
                  'asimba.war',
                  '-C',
                  '%s/' % tmpAsimbaDir ,
                  '.'], self.distTmpFolder)

        self.logIt("Copying asimba.war into jetty webapps folder...")
        jettyServiceName = 'asimba'
        self.installJettyService(self.jetty_app_configuration[jettyServiceName])

        jettyServiceWebapps = '%s/%s/webapps' % (self.jetty_base, jettyServiceName)
        self.copyFile('%s/asimba.war' % self.distTmpFolder, jettyServiceWebapps)

        self.removeDirs(tmpAsimbaDir)
        self.removeFile('%s/asimba.war' % self.distTmpFolder)

    def install_cas(self):
        casWar = 'cas.war'
        distCasPath = '%s/%s' % (self.distWarFolder, casWar)
        tmpCasDir = '%s/tmp_cas' % self.distTmpFolder

        self.logIt("Unpacking %s..." % casWar)
        self.removeDirs(tmpCasDir)
        self.createDirs(tmpCasDir)

        self.run([self.cmd_jar,
                  'xf',
                  distCasPath], tmpCasDir)

        self.logIt("Configuring CAS...")
        casTemplatePropertiesPath = '%s/cas.properties' % self.outputFolder
        casWarPropertiesPath = '%s/WEB-INF/cas.properties' % tmpCasDir

        self.copyFile(casTemplatePropertiesPath, casWarPropertiesPath)

        self.logIt("Generating cas.war...")
        self.run([self.cmd_jar,
                  'cmf',
                  'tmp_cas/META-INF/MANIFEST.MF',
                  'cas.war',
                  '-C',
                  '%s/' % tmpCasDir,
                  '.'], self.distTmpFolder)

        self.logIt("Copying cas.war into jetty webapps folder...")
        jettyServiceName = 'cas'
        self.installJettyService(self.jetty_app_configuration[jettyServiceName])

        jettyServiceWebapps = '%s/%s/webapps' % (self.jetty_base, jettyServiceName)
        self.copyFile('%s/cas.war' % self.distTmpFolder, jettyServiceWebapps)

        self.removeDirs(tmpCasDir)
        self.removeFile('%s/cas.war' % self.distTmpFolder)

    def install_oxauth_rp(self):
        oxAuthRPWar = 'oxauth-rp.war'
        distOxAuthRpPath = '%s/%s' % (self.distWarFolder, oxAuthRPWar)

        self.logIt("Copying oxauth-rp.war into jetty webapps folder...")

        jettyServiceName = 'oxauth-rp'
        self.installJettyService(self.jetty_app_configuration[jettyServiceName])

        jettyServiceWebapps = '%s/%s/webapps' % (self.jetty_base, jettyServiceName)
        self.copyFile('%s/oxauth-rp.war' % self.distWarFolder, jettyServiceWebapps)

    def install_passport(self):
        self.logIt("Installing npm and Node.Js...")
        # TODO

        self.logIt("Installing Passport...")
        # TODO

        self.logIt("Preparing Passport OpenID RP certificate...")
        passport_rp_client_jwks_json = json.loads(''.join(self.passport_rp_client_jwks))
        for jwks_key in passport_rp_client_jwks_json["keys"]:
            if jwks_key["alg"]  == self.passport_rp_client_cert_alg: 
                self.passport_rp_client_cert_alias = jwks_key["kid"]
                break

        self.export_openid_key(self.passport_rp_client_jks_fn, self.passport_rp_client_jks_pass, self.passport_rp_client_cert_alias, self.passport_rp_client_cert_fn)
        self.renderTemplateInOut(self.passport_config, self.templateFolder, self.configFolder)

    def install_gluu_components(self):
        if self.installOxAuth:
            self.install_oxauth()

        if self.installOxTrust:
            self.install_oxtrust()

        if self.installSaml:
            self.install_saml()

        if self.installCas:
            self.install_cas()

        if self.installAsimba:
            self.install_asimba()

        if self.installOxAuthRP:
            self.install_oxauth_rp()

        if self.installPassport:
            self.install_passport()

    def isIP(self, address):
        try:
            socket.inet_aton(address)
            return True
        except socket.error:
            return False

    def ldap_encode(self, password):
        salt = os.urandom(4)
        sha = hashlib.sha1(password)
        sha.update(salt)
        b64encoded = '{0}{1}'.format(sha.digest(), salt).encode('base64').strip()
        encrypted_password = '{{SSHA}}{0}'.format(b64encoded)
        return encrypted_password

    def createUser(self, userName, homeDir):
        try:
            useradd = '/usr/sbin/useradd'
            self.run([useradd, '--system', '--create-home', '--user-group', '--shell', '/bin/bash', '--home-dir', homeDir, userName])
        except:
            self.logIt("Error adding users", True)
            self.logIt(traceback.format_exc(), True)

    def createUsers(self):
        self.createUser('ldap', self.ldap_user_home)
        self.createUser('jetty', self.jetty_user_home)

    def makeFolders(self):
        try:
            # Allow write to /tmp
            self.run([self.cmd_chmod, 'ga+w', "/tmp"])

            # Create these folder on all instances
            self.run([self.cmd_mkdir, '-p', self.configFolder])
            self.run([self.cmd_mkdir, '-p', self.certFolder])
            self.run([self.cmd_mkdir, '-p', self.outputFolder])
            self.run([self.cmd_mkdir, '-p', self.jetty_user_home_lib])

            # OS /etc/default folder
            osDefault = "/etc/default"
            if not os.path.exists(osDefault):
                self.run([self.cmd_mkdir, '-p', osDefault])

            if self.installOxTrust | self.installOxAuth:
                self.run([self.cmd_mkdir, '-p', self.gluuOptFolder])
                self.run([self.cmd_mkdir, '-p', self.gluuOptBinFolder])
                self.run([self.cmd_mkdir, '-p', self.oxPhotosFolder])
                self.run([self.cmd_mkdir, '-p', self.oxTrustRemovedFolder])
                self.run([self.cmd_mkdir, '-p', self.oxTrustCacheRefreshFolder])

                # Customizations folders
                self.run([self.cmd_mkdir, '-p', self.oxCustomizationFolder])
                self.run([self.cmd_mkdir, '-p', "%s/oxauth" % self.oxCustomizationFolder])
                self.run([self.cmd_mkdir, '-p', "%s/oxauth/libs" % self.oxCustomizationFolder])
                self.run([self.cmd_mkdir, '-p', "%s/oxauth/pages" % self.oxCustomizationFolder])
                self.run([self.cmd_mkdir, '-p', "%s/oxauth/resources" % self.oxCustomizationFolder])

                self.run([self.cmd_mkdir, '-p', "%s/oxtrust" % self.oxCustomizationFolder])
                self.run([self.cmd_mkdir, '-p', "%s/oxtrust/libs" % self.oxCustomizationFolder])
                self.run([self.cmd_mkdir, '-p', "%s/oxtrust/pages" % self.oxCustomizationFolder])
                self.run([self.cmd_mkdir, '-p', "%s/oxtrust/resources" % self.oxCustomizationFolder])

                self.run([self.cmd_chown, '-R', 'jetty:jetty', self.oxCustomizationFolder])

            if self.installSaml:
                self.run([self.cmd_mkdir, '-p', self.idp3Folder])
                self.run([self.cmd_mkdir, '-p', self.idp3MetadataFolder])
                self.run([self.cmd_mkdir, '-p', self.idp3LogsFolder])
                self.run([self.cmd_mkdir, '-p', self.idp3LibFolder])
                self.run([self.cmd_mkdir, '-p', self.idp3ConfFolder])
                self.run([self.cmd_mkdir, '-p', self.idp3ConfAuthnFolder])
                self.run([self.cmd_mkdir, '-p', self.idp3CredentialsFolder])
                # self.run([self.cmd_mkdir, '-p', self.idp3WarFolder])
                self.run([self.cmd_chown, '-R', 'jetty:jetty', self.idp3Folder])

            if self.installLdap:
                self.run([self.cmd_mkdir, '-p', '/opt/gluu/data'])
        except:
            self.logIt("Error making folders", True)
            self.logIt(traceback.format_exc(), True)

    def customiseSystem(self):
        # Render customized part
        if self.os_initdaemon == 'init':
            self.renderTemplate(self.system_profile_update)
            renderedSystemProfile = self.readFile(self.system_profile_update)
    
            # Read source file
            currentSystemProfile = self.readFile(self.sysemProfile)
    
            # Write merged file
            resultSystemProfile = "\n".join((currentSystemProfile, renderedSystemProfile))
            self.writeFile(self.sysemProfile, resultSystemProfile)
    
            # Fix new file permissions
            self.run([self.cmd_chmod, '644', self.sysemProfile])

    def configureSystem(self):
        self.customiseSystem()
        self.createUsers()
        self.makeFolders()

    def make_salt(self):
        try:
            f = open("%s/salt" % self.configFolder, 'w')
            f.write('encodeSalt = %s' % self.encode_salt)
            f.close()
        except:
            self.logIt("Error writing salt", True)
            self.logIt(traceback.format_exc(), True)
            sys.exit()


    def make_oxauth_salt(self):
        self.pairwiseCalculationKey = self.genRandomString(random.randint(20,30))
        self.pairwiseCalculationSalt = self.genRandomString(random.randint(20,30))

    def promptForProperties(self):
        # IP address needed only for Apache2 and hosts file update
        if self.installHttpd:
            self.ip = self.get_ip()

        detectedHostname = None
        try:
            detectedHostname = socket.gethostbyaddr(socket.gethostname())[0]
        except:
            try:
                detectedHostname = os.popen("/bin/hostname").read().strip()
            except:
                self.logIt("No detected hostname", True)
                self.logIt(traceback.format_exc(), True)
        if detectedHostname:
            self.hostname = self.getPrompt("Enter hostname", detectedHostname)
        else:
            self.hostname = self.getPrompt("Enter hostname")

        # Get city and state|province code
        self.city = self.getPrompt("Enter your city or locality")
        self.state = self.getPrompt("Enter your state or province two letter code")

        # Get the Country Code
        long_enough = False
        while not long_enough:
            countryCode = self.getPrompt("Enter two letter Country Code")
            if len(countryCode) != 2:
                print "Country code must be two characters"
            else:
                self.countryCode = countryCode
                long_enough = True

        self.orgName = self.getPrompt("Enter Organization Name")
        self.admin_email = self.getPrompt('Enter email address for support at your organization')
        self.application_max_ram = self.getPrompt("Enter maximum RAM for applications in MB", '3072')
        randomPW = self.getPW()
        self.ldapPass = self.getPrompt("Optional: enter password for oxTrust and LDAP superuser", randomPW)

        promptForOxAuth = self.getPrompt("Install oxAuth OAuth2 Authorization Server?", "Yes")[0].lower()
        if promptForOxAuth == 'y':
            self.installOxAuth = True
        else:
            self.installOxAuth = False

        promptForOxTrust = self.getPrompt("Install oxTrust Admin UI?", "Yes")[0].lower()
        if promptForOxTrust == 'y':
            self.installOxTrust = True
        else:
            self.installOxTrust = False

        promptForLDAP = self.getPrompt("Install LDAP Server?", "Yes")[0].lower()
        if promptForLDAP == 'y':
            self.installLdap = True
        else:
            self.installLdap = False

        promptForHTTPD = self.getPrompt("Install Apache HTTPD Server", "Yes")[0].lower()
        if promptForHTTPD == 'y':
            self.installHttpd = True
        else:
            self.installHttpd = False

        promptForShibIDP = self.getPrompt("Install Shibboleth SAML IDP?", "No")[0].lower()
        if promptForShibIDP == 'y':
            self.shibboleth_version = 'v3'
            self.installSaml = True
        else:
            self.installSaml = False

        promptForAsimba = self.getPrompt("Install Asimba SAML Proxy?", "No")[0].lower()
        if promptForAsimba == 'y':
            self.installAsimba = True
        else:
            self.installAsimba = False

        promptForCAS = self.getPrompt("Install CAS?", "No")[0].lower()
        if promptForCAS == 'y':
            self.installCas = True
        else:
            self.installCas = False

        promptForOxAuthRP = self.getPrompt("Install oxAuth RP?", "No")[0].lower()
        if promptForOxAuthRP == 'y':
            self.installOxAuthRP = True
        else:
            self.installOxAuthRP = False

        promptForPassport = self.getPrompt("Install Passport?", "No")[0].lower()
        if promptForPassport == 'y':
            self.installPassport = True
        else:
            self.installPassport = False

    def get_filepaths(self, directory):
        file_paths = []

        for root, directories, files in os.walk(directory):
            for filename in files:
                # filepath = os.path.join(root, filename)
                file_paths.append(filename)

        return file_paths

    def renderTemplateInOut(self, filePath, templateFolder, outputFolder):
        self.logIt("Rendering template %s" % filePath)
        fn = os.path.split(filePath)[-1]
        f = open(os.path.join(templateFolder, fn))
        template_text = f.read()
        f.close()
        newFn = open(os.path.join(outputFolder, fn), 'w+')
        newFn.write(template_text % self.merge_dicts(self.__dict__, self.templateRenderingDict))
        newFn.close()

    def renderTemplate(self, filePath):
        self.renderTemplateInOut(filePath, self.templateFolder, self.outputFolder)

    def render_templates(self):
        self.logIt("Rendering templates")
        for fullPath in self.ce_templates.keys():
            try:
                self.renderTemplate(fullPath)
            except:
                self.logIt("Error writing template %s" % fullPath, True)
                self.logIt(traceback.format_exc(), True)

    def render_configuration_template(self):
        self.logIt("Rendering configuration templates")

        fullPath = self.ldif_configuration
        try:
            self.renderTemplate(fullPath)
        except:
            self.logIt("Error writing template %s" % fullPath, True)
            self.logIt(traceback.format_exc(), True)

    def render_templates_folder(self, templatesFolder):
        self.logIt("Rendering templates folder: %s" % templatesFolder)

        for templateBase, templateDirectories, templateFiles in os.walk(templatesFolder):
            for templateFile in templateFiles:
                fullPath = '%s/%s' % (templateBase, templateFile)
                try:
                    self.logIt("Rendering test template %s" % fullPath)
                    # Remove ./template/ and everything left of it from fullPath
                    fn = re.match(r'(^.+/templates/)(.*$)', fullPath).groups()[1]
                    f = open(os.path.join(self.templateFolder, fn))
                    template_text = f.read()
                    f.close()

                    fullOutputFile = os.path.join(self.outputFolder, fn)
                    # Create full path to the output file
                    fullOutputDir = os.path.dirname(fullOutputFile)
                    if not os.path.exists(fullOutputDir):
                        os.makedirs(fullOutputDir)

                    newFn = open(fullOutputFile, 'w+')
                    newFn.write(template_text % self.merge_dicts(self.__dict__, self.templateRenderingDict))
                    newFn.close()
                except:
                    self.logIt("Error writing template %s" % fullPath, True)
                    self.logIt(traceback.format_exc(), True)

    def render_test_templates(self):
        self.logIt("Rendering test templates")

        testTepmplatesFolder = '%s/test/' % self.templateFolder
        self.render_templates_folder(testTepmplatesFolder)

    def render_jetty_templates(self):
        self.logIt("Rendering jetty templates")

        jettyTepmplatesFolder = '%s/jetty/' % self.templateFolder
        self.render_templates_folder(jettyTepmplatesFolder)

    def reindent(self, text, num_spaces):
        text = string.split(text, '\n')
        text = [(num_spaces * ' ') + string.lstrip(line) for line in text]
        text = string.join(text, '\n')

        return text

    def generate_base64_file(self, fn, num_spaces):
        self.logIt('Loading file %s' % fn)
        plain_file_b64encoded_text = None
        try:
            plain_file = open(fn)
            plain_file_text = plain_file.read()
            plain_file_b64encoded_text = plain_file_text.encode('base64').strip()
            plain_file.close()
        except:
            self.logIt("Error loading file", True)
            self.logIt(traceback.format_exc(), True)

        if num_spaces > 0:
            plain_file_b64encoded_text = self.reindent(plain_file_b64encoded_text, num_spaces)

        return plain_file_b64encoded_text

    def generate_base64_ldap_file(self, fn):
        return self.generate_base64_file(fn, 1)

    def generate_base64_configuration(self):
        self.templateRenderingDict['oxauth_config_base64'] = self.generate_base64_ldap_file(self.oxauth_config_json)
        self.templateRenderingDict['oxauth_static_conf_base64'] = self.generate_base64_ldap_file(self.oxauth_static_conf_json)
        self.templateRenderingDict['oxauth_error_base64'] = self.generate_base64_ldap_file(self.oxauth_error_json)
        self.templateRenderingDict['oxauth_openid_key_base64'] = self.generate_base64_ldap_file(self.oxauth_openid_jwks_fn)

        self.templateRenderingDict['oxtrust_config_base64'] = self.generate_base64_ldap_file(self.oxtrust_config_json);
        self.templateRenderingDict['oxtrust_cache_refresh_base64'] = self.generate_base64_ldap_file(self.oxtrust_cache_refresh_json)
        self.templateRenderingDict['oxtrust_import_person_base64'] = self.generate_base64_ldap_file(self.oxtrust_import_person_json)

        self.templateRenderingDict['oxidp_config_base64'] = self.generate_base64_ldap_file(self.oxidp_config_json)
        self.templateRenderingDict['oxcas_config_base64'] = self.generate_base64_ldap_file(self.oxcas_config_json)
        self.templateRenderingDict['oxasimba_config_base64'] = self.generate_base64_ldap_file(self.oxasimba_config_json)

    # args = command + args, i.e. ['ls', '-ltr']
    def run(self, args, cwd=None, env=None, useWait=False):
        self.logIt('Running: %s' % ' '.join(args))
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env)
            if useWait:
                code = p.wait()
                self.logIt('Run: %s with result code: %d' % (' '.join(args), code) )
            else:
                output, err = p.communicate()
                if output:
                    self.logIt(output)
                if err:
                    self.logIt(err, True)
        except:
            self.logIt("Error running command : %s" % " ".join(args), True)
            self.logIt(traceback.format_exc(), True)

    def save_properties(self):
        self.logIt('Saving properties to %s' % self.savedProperties)

        def getString(value):
            if isinstance(value, str):
                return value.strip()
            elif isinstance(value, bool):
                return str(value)
            else:
                return ""
        try:
            p = Properties.Properties()
            keys = self.__dict__.keys()
            keys.sort()
            for key in keys:
                value = getString(self.__dict__[key])
                if value != '':
                    p[key] = value
            p.store(open(self.savedProperties, 'w'))
        except:
            self.logIt("Error saving properties", True)
            self.logIt(traceback.format_exc(), True)

    def createLdapPw(self):
        try:
            f = open(self.ldapPassFn, 'w')
            f.write(self.ldapPass)
            f.close()
            self.run([self.cmd_chown, 'ldap:ldap', self.ldapPassFn])
        except:
            self.logIt("Error writing temporary LDAP password.")
            self.logIt(traceback.format_exc(), True)

    def deleteLdapPw(self):
        try:
            os.remove(self.ldapPassFn)
            os.remove(os.path.join(self.ldapBaseFolder, 'opendj-setup.properties'))
        except:
            self.logIt("Error deleting ldap pw. Make sure %s is deleted" % self.ldapPassFn)
            self.logIt(traceback.format_exc(), True)

    def install_opendj(self):
        self.logIt("Running OpenDJ Setup")
        # Copy opendj-setup.properties so user ldap can find it in /opt/opendj
        setupPropsFN = os.path.join(self.ldapBaseFolder, 'opendj-setup.properties')
        shutil.copy("%s/opendj-setup.properties" % self.outputFolder, setupPropsFN)
        self.set_ownership()
        try:
            ldapSetupCommand = '%s/setup' % self.ldapBaseFolder
            setupCmd = "cd /opt/opendj ; export OPENDJ_JAVA_HOME=" + self.jre_home + " ; " + " ".join([ldapSetupCommand,
                                      '--no-prompt',
                                      '--cli',
                                      '--propertiesFilePath',
                                      setupPropsFN,
                                      '--acceptLicense'])
            self.run(['/bin/su',
                      'ldap',
                      '-c',
                      setupCmd])
        except:
            self.logIt("Error running LDAP setup script", True)
            self.logIt(traceback.format_exc(), True)

        try:
            ldapDsJavaPropCommand = "%s/bin/dsjavaproperties" % self.ldapBaseFolder
            dsjavaCmd = "cd /opt/opendj/bin ; %s" % ldapDsJavaPropCommand
            self.run(['/bin/su',
                      'ldap',
                      '-c',
                      dsjavaCmd
            ])
        except:
            self.logIt("Error running dsjavaproperties", True)
            self.logIt(traceback.format_exc(), True)

        try:
            stopDsJavaPropCommand = "%s/bin/stop-ds" % self.ldapBaseFolder
            dsjavaCmd = "cd /opt/opendj/bin ; %s" % stopDsJavaPropCommand
            self.run(['/bin/su',
                      'ldap',
                      '-c',
                      dsjavaCmd
            ])
        except:
            self.logIt("Error running stop-ds", True)
            self.logIt(traceback.format_exc(), True)

    def setup_init_scripts(self):
        if self.os_initdaemon == 'initd':
            for init_file in self.init_files:
                try:
                    script_name = os.path.split(init_file)[-1]
                    self.copyFile(init_file, "/etc/init.d")
                    self.run([self.cmd_chmod, "755", "/etc/init.d/%s" % script_name])
                except:
                    self.logIt("Error copying script file %s to /etc/init.d" % init_file)
                    self.logIt(traceback.format_exc(), True)

        if self.os_type in ['centos', 'fedora']:
            for service in self.redhat_services:
                self.run(["/sbin/chkconfig", service, "on"])
        elif self.os_type in ['redhat']:
            for service in self.redhat_services:
                self.run(["/sbin/chkconfig", service, "on"])
        elif self.os_type in ['ubuntu', 'debian']:
            for service in self.debian_services:
                self.run(["/usr/sbin/update-rc.d", service, 'enable'])


    def start_services(self):
        # Detect service path and apache service name
        service_path = '/sbin/service'
        apache_service_name = 'httpd'
        if self.os_type in ['centos', 'redhat', 'fedora'] and self.os_initdaemon == 'systemd':
           service_path = '/usr/bin/systemctl'
           apache_service_name = 'httpd'
        elif self.os_type in ['debian', 'ubuntu']:
           service_path = '/usr/sbin/service'
           apache_service_name = 'apache2'

        # Apache HTTPD
        if self.os_type in ['centos', 'redhat', 'fedora'] and self.os_initdaemon == 'systemd':
           self.run([service_path, 'enable', apache_service_name])
           self.run([service_path, 'start', apache_service_name])
        else:
           self.run([service_path, apache_service_name, 'start'])

        # Memcached
        if self.os_type in ['centos', 'redhat', 'fedora'] and self.os_initdaemon == 'systemd':
           self.run([service_path, 'start', 'memcached.service'])
        else:
           self.run([service_path, 'memcached', 'start'])

        # Openldap
        if self.installLdap:
            # FIXME Tested on ubuntu only
            if self.os_type in ['centos', 'redhat', 'fedora'] and self.os_initdaemon == 'systemd':
               self.run([service_path, 'restart', 'rsyslog.service'])
               self.run([service_path, 'start', 'solserver.service'])
            else:
	       # Below two lines are specifically for Ubuntu 14.04
               self.copyFile(self.rsyslogInitFile, "/etc/init.d")
               self.removeFile("/etc/init/rsyslog.conf")
               self.run([service_path, 'rsyslog', 'restart'])
               self.run([service_path, 'solserver', 'start'])

        # Jetty services
        try:
            # Iterate through all components and start installed
            for applicationName, applicationConfiguration in self.jetty_app_configuration.iteritems():
                if applicationConfiguration['installed']:
                    if self.os_type in ['centos', 'redhat', 'fedora'] and self.os_initdaemon == 'systemd':
                       self.run([service_path, 'start', applicationName], None, None, True)
                    else:
                       self.run([service_path, applicationName, 'start'], None, None, True)
        except:
            self.logIt("Error starting Jetty services")
            self.logIt(traceback.format_exc(), True)

    def update_hostname(self):
        self.logIt("Copying hosts and hostname to final destination")

        if self.os_initdaemon == 'systemd' and self.os_type in ['centos', 'redhat', 'fedora']:
            self.run(['/usr/bin/hostnamectl', 'set-hostname', self.hostname])
        else:
            if self.os_type in ['debian', 'ubuntu']:
                self.copyFile("%s/hostname" % self.outputFolder, self.etc_hostname)

            if self.os_type in ['centos', 'redhat', 'fedora']:
                self.copyFile("%s/network" % self.outputFolder, self.network)

            self.run(['/bin/hostname', self.hostname])

        self.copyFile("%s/hosts" % self.outputFolder, self.etc_hosts)

    def install_openldap(self):
        self.logIt("Installing OpenLDAP from package")

        # Determine package type
        packageRpm = True
        packageExtension = ".rpm"
        if self.os_type in ['debian', 'ubuntu']:
            packageRpm = False
            packageExtension = ".deb"

        openLdapDistFolder = "%s/%s" % (self.distFolder, "symas")

        # Find package
        packageName = None
        for file in os.listdir(openLdapDistFolder):
            if file.endswith(packageExtension):
                packageName = "%s/%s" % ( openLdapDistFolder, file )

        if packageName == None:
            raise Exception('Failed to find OpenLDAP package in folder %s !' % directory)

        self.logIt("Found package '%s' for install" % packageName)
        if packageRpm:
           self.run([self.cmd_rpm, '--install', '--verbose', '--hash', packageName])
        else:
           self.run([self.cmd_dpkg, '--install', packageName])

    def configure_openldap(self):
        self.logIt("Configuring OpenLDAP")
        # 1. Copy the conf files to
        self.copyFile(self.openldapSlapdConf, self.openldapConfFolder)
        self.copyFile(self.openldapSymasConf, self.openldapConfFolder)
        # 2. Copy the schema files into place
        self.copyFile("%s/static/openldap/gluu.schema" % self.install_dir, "/opt/gluu/")
        self.copyFile("%s/static/openldap/custom.schema" % self.install_dir, "/opt/gluu/")
        # 4. Create the PEM file from key and crt
        with open(self.openldapTLSCACert, 'w') as pem:
            with open(self.openldapTLSCert, 'r') as crt:
                pem.write(crt.read())
            with open(self.openldapTLSKey, 'r') as key:
                pem.write(key.read())

    def import_ldif_openldap(self):
        self.logIt("Importing LDIF files into OpenLDAP")
        cmd = os.path.join(self.openldapBinFolder, 'slapadd')
        config = os.path.join(self.openldapConfFolder, 'slapd.conf')
        for ldif in self.ldif_files:
            if 'site.ldif' in ldif:
                self.run([cmd, '-b', 'o=site', '-f', config, '-l', ldif])
            else:
                self.run([cmd, '-b', 'o=gluu', '-f', config, '-l', ldif])
        # Generate the cn=config directory
        self.run([self.cmd_mkdir, '-p', self.openldapCnConfig])
        self.run([self.slaptest, '-f', self.openldapSlapdConf, '-F', self.openldapCnConfig])

    def setup_openldap_logging(self):
        self.run([self.cmd_mkdir, '-p', self.openldapLogDir])
        self.run([self.cmd_chown, '-R', 'syslog:adm', self.openldapLogDir])
        if not os.path.isdir('/etc/rsyslog.d/'):
            self.run([self.cmd_mkdir, '-p', '/etc/rsyslog.d/'])
        self.copyFile(self.openldapSyslogConf, '/etc/rsyslog.d/')
        self.copyFile(self.openldapLogrotate, '/etc/logrotate.d/')

    def install_ldap_server(self):
        self.logIt("Running OpenDJ Setup")

        installObject.extractOpenDJ()
        installObject.opendj_version = installObject.determineOpenDJVersion()
        installObject.createLdapPw()
        installObject.install_opendj()
        installObject.deleteLdapPw()

        self.logIt("Running OpenLDAP Setup")
        installObject.setup_openldap_logging()
        installObject.install_openldap()
        installObject.configure_openldap()
        installObject.import_ldif_openldap()

    def calculate_aplications_memory(self):
        self.logIt("Calculating memory setting for applications")

        installedComponents = []
        allowedApplicationsMemory = {}

        if self.installOxAuth:
            installedComponents.append(self.jetty_app_configuration['oxauth'])
        if self.installOxTrust:
            installedComponents.append(self.jetty_app_configuration['identity'])
        if self.installSaml:
            installedComponents.append(self.jetty_app_configuration['idp'])
        if self.installCas:
            installedComponents.append(self.jetty_app_configuration['cas'])
        if self.installAsimba:
            installedComponents.append(self.jetty_app_configuration['asimba'])
        if self.installOxAuthRP:
            installedComponents.append(self.jetty_app_configuration['oxauth-rp'])

        usedRatio = 0.0
        for installedComponent in installedComponents:
            usedRatio += installedComponent['memory']['ratio']

        ratioMultiplier = 1.0 + (1.0 - usedRatio)/usedRatio

        for installedComponent in installedComponents:
            allowedRatio = installedComponent['memory']['ratio'] * ratioMultiplier
            allowedMemory = int(round(allowedRatio * int(self.application_max_ram)))

            if allowedMemory > installedComponent['memory']['max_allowed_mb']:
                allowedMemory = installedComponent['memory']['max_allowed_mb']

            allowedApplicationsMemory[installedComponent['name']] = allowedMemory

        # Iterate through all components into order to prepare all keys
        for applicationName, applicationConfiguration in self.jetty_app_configuration.iteritems():
            if allowedApplicationsMemory.has_key(applicationName):
                applicationMemory = allowedApplicationsMemory.get(applicationName)
                self.templateRenderingDict["%s_max_mem" % applicationName] = applicationMemory
            else:
                self.templateRenderingDict["%s_max_mem" % applicationName] = 256

    def merge_dicts(self, *dict_args):
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)

        return result
############################   Main Loop   #################################################

def print_help():
    print "\nUse setup.py to configure your Gluu Server and to add initial data required for"
    print "oxAuth and oxTrust to start. If setup.properties is found in this folder, these"
    print "properties will automatically be used instead of the interactive setup."
    print "Options:"
    print ""
    print "    -a   Install Asimba"
    print "    -r   Install oxAuth RP"
    print "    -c   Install CAS"
    print "    -p   Install Passport"
    print "    -d   specify the directory where community-edition-setup is located. Defaults to '.'"
    print "    -f   specify setup.properties file"
    print "    -h   Help"
    print "    -n   No interactive prompt before install starts. Run with -f"
    print "    -N   No apache httpd server"
    print "    -s   Install the Shibboleth IDP"
    print "    -u   Update hosts file with IP address / hostname"
    print "    -w   Get the development head war files"
    print "    --allow_pre_released_applications"

def getOpts(argv, setupOptions):
    try:
        opts, args = getopt.getopt(argv, "acd:f:hNnsuwr", ['allow_pre_released_applications'])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-a':
            setupOptions['installAsimba'] = True
        elif opt == '-c':
            setupOptions['installCas'] = True
        elif opt == '-d':
            if os.path.exists(arg):
                setupOptions['install_dir'] = arg
            else:
                print 'System folder %s does not exist. Installing in %s' % (arg, os.getcwd())
        elif opt == '-h':
            print_help()
            sys.exit()
        elif opt == "-f":
            try:
                if os.path.isfile(arg):
                    setupOptions['setup_properties'] = arg
                    print "Found setup properties %s\n" % arg
                else:
                    print "\nOoops... %s file not found for setup properties.\n" % arg
            except:
                print "\nOoops... %s file not found\n" % arg
        elif opt == "-n":
            setupOptions['noPrompt'] = True
        elif opt == "-N":
            setupOptions['installHTTPD'] = False
        elif opt == "-s":
            setupOptions['installSaml'] = True
        elif opt == "-u":
            pass  # TODO implement this option or remove it from help
        elif opt == "-w":
            setupOptions['downloadWars'] = True
        elif opt == '-r':
            setupOptions['installOxAuthRP'] = True
        elif opt == '-p':
            setupOptions['installPassport'] = True
        elif opt == '--allow_pre_released_applications':
            setupOptions['allowPreReleasedApplications'] = True
    return setupOptions

if __name__ == '__main__':

    setupOptions = {
        'install_dir': '.',
        'setup_properties': None,
        'noPrompt': False,
        'downloadWars': False,
        'installOxAuth': True,
        'installOxTrust': True,
        'installLDAP': True,
        'installHTTPD': True,
        'installSaml': False,
        'installAsimba': False,
        'installCas': False,
        'installOxAuthRP': False,
        'installPassport': False,
        'allowPreReleasedApplications': False
    }
    if len(sys.argv) > 1:
        setupOptions = getOpts(sys.argv[1:], setupOptions)

    installObject = Setup(setupOptions['install_dir'])

    installObject.downloadWars = setupOptions['downloadWars']

    installObject.installOxAuth = setupOptions['installOxAuth']
    installObject.installOxTrust = setupOptions['installOxTrust']
    installObject.installLdap = setupOptions['installLDAP']
    installObject.installHttpd = setupOptions['installHTTPD']
    installObject.installSaml = setupOptions['installSaml']
    installObject.installAsimba = setupOptions['installAsimba']
    installObject.installCas = setupOptions['installCas']
    installObject.installOxAuthRP = setupOptions['installOxAuthRP']
    installObject.installPassport = setupOptions['installPassport']
    installObject.allowPreReleasedApplications = setupOptions['allowPreReleasedApplications']

    # Get the OS type
    installObject.os_type = installObject.detect_os_type()
    # Get the init type
    installObject.os_initdaemon = installObject.detect_initd()
    # Get apache version
    installObject.apache_version = installObject.determineApacheVersionForOS()

    print "\nInstalling Gluu Server..."
    print "Detected OS  :  %s" % installObject.os_type
    print "Detected init:  %s" % installObject.os_initdaemon
    print "Detected Apache:  %s" % installObject.apache_version

    print "\nInstalling Gluu Server...\n\nFor more info see:\n  %s  \n  %s\n" % (installObject.log, installObject.logError)
    print "\n** All clear text passwords contained in %s.\n" % installObject.savedProperties
    try:
        os.remove(installObject.log)
        installObject.logIt('Removed %s' % installObject.log)
    except:
        pass
    try:
        os.remove(installObject.logError)
        installObject.logIt('Removed %s' % installObject.logError)
    except:
        pass

    installObject.logIt("Installing Gluu Server", True)

    if setupOptions['setup_properties']:
        installObject.logIt('%s Properties found!\n' % setupOptions['setup_properties'])
        installObject.load_properties(setupOptions['setup_properties'])
    elif os.path.isfile(installObject.setup_properties_fn):
        installObject.logIt('%s Properties found!\n' % installObject.setup_properties_fn)
        installObject.load_properties(installObject.setup_properties_fn)
    else:
        installObject.logIt("%s Properties not found. Interactive setup commencing..." % installObject.setup_properties_fn)
        installObject.promptForProperties()

    # Validate Properties
    installObject.check_properties()

    # Show to properties for approval
    print '\n%s\n' % `installObject`
    proceed = "NO"
    if not setupOptions['noPrompt']:
        proceed = raw_input('Proceed with these values [Y|n] ').lower().strip()
    if (setupOptions['noPrompt'] or not len(proceed) or (len(proceed) and (proceed[0] == 'y'))):
        try:
            installObject.configureSystem()
            installObject.downloadWarFiles()
            installObject.calculate_aplications_memory()
            installObject.installJRE()
            installObject.installJetty()
            installObject.installJython()
            installObject.installNode()
            installObject.make_salt()
            installObject.make_oxauth_salt()
            installObject.copy_scripts()
            installObject.install_gluu_base()
            installObject.encode_passwords()
            installObject.encode_test_passwords()
            installObject.render_templates()
            installObject.generate_crypto()
            installObject.generate_oxauth_openid_keys()
            installObject.generate_base64_configuration()
            installObject.render_configuration_template()
            installObject.update_hostname()
            installObject.setUlimits()
            installObject.configure_httpd()
            installObject.install_ldap_server()
            installObject.copy_output()
            installObject.setup_init_scripts()
            installObject.render_jetty_templates()
            installObject.install_gluu_components()
            installObject.render_test_templates()
            installObject.copy_static()
            installObject.set_ownership()
            installObject.start_services()
            installObject.save_properties()
        except:
            installObject.logIt("***** Error caught in main loop *****", True)
            installObject.logIt(traceback.format_exc(), True)
        print "\n\n Gluu Server installation successful! Point your browser to https://%s\n\n" % installObject.hostname
    else:
        installObject.save_properties()
        print "Properties saved to %s. Change filename to %s if you want to re-use" % \
                         (installObject.savedProperties, installObject.setup_properties_fn)

# END
