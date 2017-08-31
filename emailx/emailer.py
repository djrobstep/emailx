from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import smtplib
import email.utils
import mimetypes

from six.moves.email_mime_base import MIMEBase
from six.moves.email_mime_text import MIMEText
from six.moves.email_mime_multipart import MIMEMultipart
from six import python_2_unicode_compatible
from contextlib import contextmanager

from .unicode import to_str, to_text, to_bytes, listify

DEFAULT_PORT = 587

COMMASPACE = u', '

REAL_SEND = False


def emailsplit(x):
    try:
        a, b = x.split('<', 1)
    except ValueError:
        a, b = '', x
    return a.strip(), b.rstrip('>').strip()


class Recipient(object):
    def __init__(self, *args):
        try:
            self.name, self.address = args
        except ValueError:
            try:
                self.name, self.address = args[0]
            except ValueError:
                self.name, self.address = emailsplit(args[0])

        self.name = to_text(self.name)
        self.address = to_text(self.address)

    @property
    def formatted(self):
        f = email.utils.formataddr((self.name, self.address))
        return f

    def __repr__(self):
        name_str = repr(to_str(self.name))
        address_str = repr(to_str(self.address))
        return 'Recipient({}, {})'.format(name_str, address_str)

    def __str__(self):
        return self.formatted


def format_recipients(recipientlist):
    return [str(each) for each in recipientlist]


def recipients_as_unicode(recipientlist):
    return COMMASPACE.join([each.formatted for each in recipientlist])


def parse_address_list(addresslist):
    return listify(addresslist)


@python_2_unicode_compatible
class Email(object):
    def __init__(self, source, subject, body, to_addresses,
                 cc_addresses=None,
                 bcc_addresses=None,
                 msg=None,
                 reply_addresses=None,
                 return_path=None,
                 text_body=None,
                 html_body=None,
                 attachments=None):

        self.subject = subject
        self.text = text_body or body

        cc_addresses = cc_addresses or []
        bcc_addresses = bcc_addresses or []

        self.FROM = Recipient(source)

        self.TO = [Recipient(each) for each in listify(to_addresses)]
        self.CC = [Recipient(each) for each in listify(cc_addresses)]
        self.BCC = [Recipient(each) for each in listify(bcc_addresses)]

        msg = msg or MIMEMultipart('alternative')
        msg.set_charset('utf-8')
        msg['To'] = recipients_as_unicode(self.TO)

        if cc_addresses:
            msg['Cc'] = recipients_as_unicode(self.CC)

        msg['From'] = str(self.FROM)
        msg.set_unixfrom(str(self.FROM))

        msg['Subject'] = self.subject

        part1 = MIMEText(self.text, 'plain', 'utf8')
        msg.attach(part1)

        if html_body:
            part2 = MIMEText(html_body, 'html', 'utf8')
            msg.attach(part2)

        self.RECIPIENTS = self.TO + self.CC + self.BCC
        self.MSG = msg

        attachments = attachments or {}

        for attname, attcontents in attachments.items():
            ctype, encoding = mimetypes.guess_type(attname)

            if ctype is None or encoding is not None:
                # No guess could be made, or the file is
                # encoded (compressed), so use a generic
                # bag-of-bits type.
                ctype = 'application/octet-stream'

            maintype, subtype = ctype.split('/', 1)
            byt = to_bytes(attcontents)
            att = MIMEBase(maintype, subtype)

            att.set_payload(byt)
            att.add_header('Content-Disposition', 'attachment', filename=attname)

            email.encoders.encode_base64(att)
            msg.attach(att)

    @property
    def to_addresses(self):
        return format_recipients(self.RECIPIENTS)

    def __str__(self):
        return self.MSG.as_string()


class SmtpConnection(object):
    def __init__(
        self,
        smtp_server,
        dummy_send_only=False,
        dummy_recipients=None,
        actually_send=True
    ):

        self.smtp = smtp_server
        self.actually_send = actually_send
        self.dummy_send_only = dummy_send_only
        self.dummy_recipients = dummy_recipients

    def send(self, email):
        if self.dummy_send_only:
            to_addrs = self.dummy_recipients
        else:
            to_addrs = email.to_addresses  # pragma: no cover

        params = dict(
            from_addr=email.FROM.formatted,
            to_addrs=to_addrs,
            msg=email.MSG.as_string()
        )

        if self.actually_send:
            self.smtp.sendmail(**params)

        params['email'] = email
        params['specified_to_addrs'] = email.to_addresses


@contextmanager
def smtp_connection(
        servername,
        login_creds,
        debug=False,
        dummy_send_only=False,
        dummy_recipients=None,
        actually_send=True,
        timeout=2.0):

    if actually_send:
        try:
            server, port = servername.split(':')
        except ValueError:
            server, port = servername, DEFAULT_PORT

        _servername = '{}:{}'.format(server, port)

        try:
            server = smtplib.SMTP(_servername, timeout=timeout)

            if debug:
                server.set_debuglevel(True)

            server.ehlo_or_helo_if_needed()

            if server.has_extn('STARTTLS'):
                server.starttls()
                server.ehlo()

            if login_creds:
                server.login(*login_creds)

            yield SmtpConnection(
                server,
                actually_send=True,
                dummy_send_only=dummy_send_only,
                dummy_recipients=parse_address_list(dummy_recipients))
        finally:
            if server:
                server.quit()

    else:
        yield SmtpConnection(
            None,
            actually_send=False,
            dummy_send_only=dummy_send_only,
            dummy_recipients=parse_address_list(dummy_recipients)
        )
