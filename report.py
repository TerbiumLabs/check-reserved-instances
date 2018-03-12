"""Report and templating functionality."""

from __future__ import print_function

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import smtplib

import jinja2

import pkg_resources

from check_reserved_instances.aws import instance_ids, reserve_expiry

TEMPLATE_DIR = pkg_resources.resource_filename(
    'check_reserved_instances', 'templates')

text_template = """
##########################################################
####            Reserved Instances Report            #####
##########################################################
{% for service in report %}
Below is the report on {{ service }} reserved instances:
    {%- if report[service]['unused_reservations'] -%}
      {%- for type, count in report[service]['unused_reservations'].items() %}
UNUSED RESERVATION!\t({{ count }})\t{{ type[0] }}\t{{ type[1] }}{%- if reserve_expiry %}\tExpires in {{ reserve_expiry[type]|string }} days.{%- endif %}
      {%- endfor %}
    {%- else %}
You have no unused {{ service }} reservations.
    {%- endif %}
    {%- if report[service]['unreserved_instances'] %}
      {%- for type, count in report[service]['unreserved_instances'].items() %}
NOT RESERVED!\t({{ count }})\t{{ type[0] }}\t{{ type[1] }}{% if instance_ids %}\t{{ ", ".join(instance_ids[type]) }}{% endif %}
      {%- endfor %}
    {%- else %}
You have no unreserved {{ service }} instances.
    {%- endif %}
({{ report[service]['qty_running_instances'] }}) running on-demand {{ service }} instances
({{ report[service]['qty_reserved_instances'] }}) {{ service }} reservations
({{ report[service]['qty_unreserved_instances'] }}) Unreserved {{ service }} reservations
{% endfor %}
"""  # noqa


def report_results(config, results):
    """Print results to stdout and email if configured.

    Args:
        config (dict): The application configuration.
        results (dict): The results to report.

    """
    report_text = jinja2.Template(text_template).render(
        report=results, instance_ids=instance_ids,
        reserve_expiry=reserve_expiry)

    print(report_text)

    if config.get('Email'):
        report_html = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
            trim_blocks=True
        ).get_template('html_template.html').render(
            report=results, instance_ids=instance_ids,
            reserve_expiry=reserve_expiry)

        email_config = config['Email']
        smtp_recipients = email_config['smtp_recipients']
        smtp_sendas = email_config['smtp_sendas']
        smtp_host = email_config['smtp_host']
        smtp_port = int(email_config['smtp_port'])
        smtp_user = email_config['smtp_user']
        smtp_password = email_config['smtp_password']
        smtp_tls = bool(email_config['smtp_tls'])

        print('\nSending emails to {}'.format(smtp_recipients))
        mailmsg = MIMEMultipart('alternative')
        mailmsg['Subject'] = 'Reserved Instance Report'
        mailmsg['To'] = smtp_recipients
        mailmsg['From'] = smtp_sendas
        email_text = MIMEText(report_text, 'plain')
        email_html = MIMEText(report_html, 'html')
        mailmsg.attach(email_text)
        mailmsg.attach(email_html)
        mailmsg = mailmsg.as_string()
        smtp = smtplib.SMTP(smtp_host, smtp_port)
        if smtp_tls:
            smtp.starttls()
        if smtp_user:
            smtp.login(smtp_user, smtp_password)
        smtp.sendmail(smtp_sendas, smtp_recipients, mailmsg)
        smtp.quit()
    else:
        print('\nNot sending email for this report')
