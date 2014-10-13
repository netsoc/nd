# Python interface to /usr/lib/sendmail

import subprocess

default_from_address = "support@netsoc.tcd.ie"


def sendmail(msg, dict=None, **kwargs):

    if dict is None:
        dict = {}
    dict.update(kwargs)
    if 'From' not in msg:
        if 'From' in dict:
            msg['From'] = dict['From']
        else:
            msg['From'] = default_from_address
    if 'To' not in msg and 'To' in dict:
        msg['To'] = dict['To']
    if 'Subject' not in msg and 'Subject' in dict:
        msg['Subject'] = dict['Subject']

    for h in ['From', 'To', 'Subject']:
        if h not in msg:
            raise Exception(
                "Mail message sending failed, must contain %s header" % h)

    if 'DRY_RUN' in dict:
        print "Sending:"
        print msg
        print ""
    else:
        print "Sending mail from %s to %s" %\
            (msg['From'], msg['To'])
        sendmail = subprocess.Popen(
            ["/usr/lib/sendmail",
             kwargs["To"],
             msg['From']],
            stdin=subprocess.PIPE)
        sendmail.communicate(msg.as_string())
