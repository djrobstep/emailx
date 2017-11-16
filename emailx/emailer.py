from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import smtplib
import email.utils
import mimetypes
import json

from base64 import b64encode

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


@python_2_unicode_compatible
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


@python_2_unicode_compatible
class Recipients(list):
    def __init__(self, recipientlist):
        super(Recipients, self).__init__(
            parse_address_list(recipientlist)
        )

    def __str__(self):
        return recipients_as_unicode(self)

    @property
    def formatted(self):
        return format_recipients(self)


def format_recipients(recipientlist):
    return [str(each) for each in recipientlist]


def recipients_as_unicode(recipientlist):
    return COMMASPACE.join([str(_) for _ in recipientlist])


def parse_address_list(addresslist):
    addresslist = listify(addresslist)

    if all(isinstance(_, Recipient) for _ in addresslist):
        return list(addresslist)

    return [Recipient(_) for _ in addresslist]


def add_attachments(msg, attachments):
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

        att.add_header(
            'Content-Disposition',
            'attachment',
            filename=attname
        )

        email.encoders.encode_base64(att)
        msg.attach(att)


@python_2_unicode_compatible
class Email(object):
    def __init__(
        self,
        source,
        subject,
        to_addresses,
        cc_addresses=None,
        bcc_addresses=None,
        reply_to=None,
        return_path=None,
        text_body=None,
        html_body=None,
        attachments=None
    ):

        self.subject = subject
        self.text_body = text_body
        self.html_body = html_body

        self.source = Recipient(source)

        self.to = Recipients(to_addresses)
        self.cc = Recipients(cc_addresses)
        self.bcc = Recipients(bcc_addresses)

        self.return_path = return_path and Recipient(return_path) or None
        self.reply_to = reply_to and Recipient(reply_to) or None

        self.attachments = attachments or {}

    @property
    def msg(self):
        msg = MIMEMultipart('alternative')
        msg.set_charset('utf-8')

        msg['To'] = str(self.to)
        msg['From'] = str(self.source)

        msg.set_unixfrom(str(self.source))

        if self.cc:
            msg['Cc'] = str(self.cc)

        if self.return_path:
            msg['Return-Path'] = str(self.return_path)

        if self.reply_to:
            msg['Reply-To'] = str(self.reply_to)

        msg['Subject'] = self.subject

        if self.text_body:
            part1 = MIMEText(self.text_body, 'plain', 'utf8')
            msg.attach(part1)

        if self.html_body:
            part2 = MIMEText(self.html_body, 'html', 'utf8')
            msg.attach(part2)

        if self.attachments:
            add_attachments(msg, self.attachments)

        return msg

    @property
    def recipients(self):
        return self.to + self.cc + self.bcc

    @property
    def to_addresses(self):
        return Recipients(self.recipients)

    def for_json(self):
        proplist = [
            'source',
            'subject',
            'to',
            'cc',
            'bcc',
            'reply_to',
            'return_path',
            'text_body',
            'html_body'
        ]

        def process(x):
            try:
                return x.formatted
            except AttributeError:
                return to_text(x)

        j = {
            _: process(getattr(self, _))
            for _
            in proplist
            if getattr(self, _) is not None
        }

        j['attachments'] = {
            k: b64encode(to_bytes(v)).decode('utf-8')
            for k, v
            in self.attachments.items()
        }

        return j

    def json(self):
        return json.dumps(self.for_json(), indent=4)

    def __str__(self):
        return self.msg.as_string()


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
        self.dummy_recipients = Recipients(dummy_recipients)

    def send(self, email):
        if self.dummy_send_only:
            to_addrs = self.dummy_recipients
        else:
            to_addrs = email.to_addresses  # pragma: no cover

        params = dict(
            from_addr=email.source.formatted,
            to_addrs=to_addrs.formatted,
            msg=email.msg.as_string()
        )

        if self.actually_send:
            self.smtp.sendmail(**params)


@contextmanager
def smtp_connection(
        servername,
        login_creds,
        debug=False,
        dummy_send_only=False,
        dummy_recipients=None,
        actually_send=True,
        timeout=10.0):

    if actually_send:
        try:
            server_part, port = servername.split(':')
        except ValueError:
            server_part, port = servername, DEFAULT_PORT

        _servername = '{}:{}'.format(server_part, port)

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

        server.quit()

    else:
        yield SmtpConnection(
            None,
            actually_send=False,
            dummy_send_only=dummy_send_only,
            dummy_recipients=parse_address_list(dummy_recipients)
        )
