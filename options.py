DEBUG = False
HOST = "ldap://snark-ldap.netsoc.tcd.ie"
UseTLS = True
TLS_CACERTFILE = "/etc/ldap/certs/ldapCA.pem"


#Validation
class ConfigurationError(Exception):

        def __init__(self, msg, *args, **kwargs):
                super(ConfigurationError, self).__init__(msg, *args, **kwargs)
if UseTLS:
        try:
                if TLS_CACERTFILE is None:
                        raise TypeError("ERROR: TLS_CACERTFILE\
                                        must be set if you want\
                                        to use StartTLS to connect to LDAP.")
        except NameError:
            raise ConfigurationError(
                "You must specify the configuration option TLS_CACERTFILE\
                with the path of the tls CA certificate file in options.py\
                if you wish to use StartTLS to connect to LDAP.")
