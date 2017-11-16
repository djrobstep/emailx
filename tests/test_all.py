from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from emailx import smtp_connection, Email, Recipient, recipients_as_unicode, emailsplit, Recipients
from mock import patch
import json


def test_addresses():
    assert emailsplit('A McB <c@example.com>') == ('A McB', 'c@example.com')

    r1 = Recipient((b'A B', 'a@example.com'))
    r2 = Recipient('B C', 'b@example.com')
    r3 = Recipient('A McB<c@example.com>')

    assert r1.name == 'A B'
    assert r2.name == 'B C'
    assert r3.name == 'A McB'

    assert r1.address == 'a@example.com'
    assert r2.address == 'b@example.com'
    assert r3.address == 'c@example.com'

    assert r1.formatted == 'A B <a@example.com>'
    assert r2.formatted == 'B C <b@example.com>'

    assert recipients_as_unicode([r1, r2]) == \
        'A B <a@example.com>, B C <b@example.com>'

    assert repr(r1) == "Recipient('A B', 'a@example.com')"

    rr = Recipients([r1, r2, r3])

    assert isinstance(rr, list)

    assert len(rr) == 3

    EXPECTED = 'A B <a@example.com>, B C <b@example.com>, A McB <c@example.com>'
    assert str(rr) == EXPECTED

    assert str(Recipients(EXPECTED)) == EXPECTED
    assert str(Recipients([])) == ''


def test_emailer():
    with patch('smtplib.SMTP'):
        SOURCE = ('Captain Test', 'test@example.com')

        SUBJECT = 'a test \xd2 email'
        BODY = 'A test **markd\xd2wn** message.'

        TO = [(b'Citizen A', 'a@example.com'), ('Citizen B', 'b@example.com')]

        CC = [('Citizen CC', 'cc@example.com')]

        BCC = [('Citizen BCC', 'bcc@example.com')]

        SERVER = 'smtp.example.com'
        LOGIN = ('username', 'password')

        DUMMY_RECIPIENTS = 'Captain Dummy <developer@example.com>'

        with smtp_connection(
            SERVER,
            LOGIN,
            debug=True,
            dummy_send_only=True,
            dummy_recipients=DUMMY_RECIPIENTS
        ) as smtp:

            m = Email(
                source=SOURCE,
                subject=SUBJECT,
                to_addresses=TO,
                cc_addresses=CC,
                bcc_addresses=BCC,
                text_body=BODY,
                html_body='A test <em>markd\xd2wn</em> message.',
                return_path='returnpath@example.com',
                reply_to='replyto@example.com',
                attachments={
                    'blah.csv': 'abc\u2026',
                    'x.binary': b'abc'
                }
            )

            assert [each.formatted for each in m.recipients] == \
                [Recipient(each).formatted for each in (TO + CC + BCC)]

            smtp.send(m)

            call_args, = smtp.smtp.sendmail.call_args_list
            args, kwargs = call_args
            assert kwargs['from_addr'] == 'Captain Test <test@example.com>'
            assert kwargs['to_addrs'] == [u'Captain Dummy <developer@example.com>']

            assert m.to_addresses.formatted == [
                'Citizen A <a@example.com>', 'Citizen B <b@example.com>',
                'Citizen CC <cc@example.com>', 'Citizen BCC <bcc@example.com>'
            ]

            message_as_string = str(m)

            assert 'x.binary' in message_as_string
            assert 'blah.csv' in message_as_string

            m_for_json = m.for_json()
            assert m_for_json['return_path'] == 'returnpath@example.com'

            assert m_for_json == {
                'attachments': {'blah.csv': 'YWJj4oCm', 'x.binary': 'YWJj'},
                'bcc': ['Citizen BCC <bcc@example.com>'],
                'cc': ['Citizen CC <cc@example.com>'],
                'html_body': 'A test <em>markdÒwn</em> message.',
                'reply_to': 'replyto@example.com',
                'return_path': 'returnpath@example.com',
                'source': 'Captain Test <test@example.com>',
                'subject': 'a test Ò email',
                'text_body': 'A test **markdÒwn** message.',
                'to': ['Citizen A <a@example.com>', 'Citizen B <b@example.com>']
            }

            assert json.loads(m.json()) == m_for_json
