from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from emailx import smtp_connection, Email, Recipient, recipients_as_unicode, emailsplit, HISTORY
from mock import patch


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
                body=BODY,
                to_addresses=TO,
                cc_addresses=CC,
                bcc_addresses=BCC,
                html_body='A test <em>markd\xd2wn</em> message.',
                attachments={
                    'blah.csv': 'abc\u2026',
                    'x.binary': b'abc'
                }
            )

            assert [each.formatted for each in m.RECIPIENTS] == \
                [Recipient(each).formatted for each in (TO + CC + BCC)]

            smtp.send(m)

            call_args, = smtp.smtp.sendmail.call_args_list
            args, kwargs = call_args
            assert kwargs['from_addr'] == 'Captain Test <test@example.com>'
            assert kwargs['to_addrs'] == [u'Captain Dummy <developer@example.com>']

            assert m.to_addresses == [
                'Citizen A <a@example.com>', 'Citizen B <b@example.com>',
                'Citizen CC <cc@example.com>', 'Citizen BCC <bcc@example.com>'
            ]

            message_as_string = m.MSG.as_string()

            assert 'x.binary' in message_as_string
            assert 'blah.csv' in message_as_string

        assert len(HISTORY) == 1
