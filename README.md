# emailx: easy as hell email sending for python

Install like this:

    pip install emailx

Use like this:

    from emailx import Email, smtp_connection

    SMTP = 'smtp.example.com'

    LOGIN = ('alex', 'password123')

    dummy_recipients = 'Alex <alex+testing@example.com>'

    with smtp_connection(SMTP, LOGIN) as c:
        e = Email(
            source='Alex <alex@example.com>',
            subject='Hello',
            body='Body',
            html_body='<html>Body</html>',
            to_addresses='Bobby <bobby@example.com',
            bcc_addresses='Kim <kim@example.com>',
            attachments={
              'a.csv': csv_data
            }
        )
        c.send(e)
