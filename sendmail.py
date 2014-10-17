# Python interface to /usr/lib/sendmail

import subprocess

default_from_address = "support@netsoc.tcd.ie"


def sendmail(msg, other_args=None, **kwargs):

    if other_args is None:
        other_args = {}
    other_args.update(kwargs)
    if 'From' not in msg:
        if 'From' in other_args:
            msg['From'] = other_args['From']
        else:
            msg['From'] = default_from_address
    if 'To' not in msg and 'To' in other_args:
        msg['To'] = other_args['To']
    if 'Subject' not in msg and 'Subject' in other_args:
        msg['Subject'] = other_args['Subject']

    for h in ['From', 'To', 'Subject']:
        if h not in msg:
            raise Exception(
                "Mail message sending failed, must contain %s header" % h)

    if 'DRY_RUN' in other_args:
        print "Sending:"
        print msg
        print ""
    else:
        print "Sending mail from %s to %s" %\
            (msg['From'], msg['To'])
        sendmail = subprocess.Popen(
            ["/usr/lib/sendmail",
             "-f",
             msg['From']],
            stdin=subprocess.PIPE)
        sendmail.communicate(msg.as_string())
