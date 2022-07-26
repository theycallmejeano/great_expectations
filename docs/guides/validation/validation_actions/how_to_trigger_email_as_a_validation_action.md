---
title: How to trigger Email as an Action
---

import TechnicalTag from '@site/docs/term_tags/_tag.mdx';

This guide will help you trigger emails as an <TechnicalTag tag="action" text="Action" /> . It will allow you to send an email including information about a <TechnicalTag tag="validation_result" text="Validation Result" />, including whether or not the <TechnicalTag tag="validation" text="Validation" /> succeeded.

:::note Prerequisites 
This how-to guide assumes that you have already:

* Configured an email account on the SMTP server you are going to use to send the email
* Identified the email addresses that messages will be sent to.
* Created a <TechnicalTag tag="checkpoint" text="Checlpoint" /> which will be configured to send the emails.
:::

## Steps

### 1. Edit your configuration variables with email related information

Open `uncommitted/config_variables.yml` file and add the following variables by adding the following lines:

````yaml
smtp_address: [address of the smtp server]
smtp_port: [port used by the smtp server]
sender_login: [login used to send the email]
sender_password: [password used to send the email]
sender_alias: [optional alias used to send the email (default = sender_login)]
receiver_emails: [addresses you want to send the email to]  # each address must be separated by commas
````

### 2. Update `action_list` in your Checkpoint configuration

Open `great_expectations.yml` and add `send_email_on_validation_result` Action to `validation_operators`. Make sure the following section exists in the `great_expectations.yml` file.

````yaml
action_list:
    - name: send_email_on_validation_result # name can be set to any value
      action:
        class_name: EmailAction
        notify_on: all # possible values: "all", "failure", "success"
        notify_with: # optional list containing the DataDocs sites to include in the notification. Defaults to including links to all configured sites.
        # You can choose between using SSL encryption, TLS encryption or none of them (not advised)
        use_tls: False
        use_ssl: True
        renderer:
          module_name: great_expectations.render.renderer.email_renderer
          class_name: EmailRenderer
        # put the actual following information in the uncommitted/config_variables.yml file
        # or pass in as environment variable
        smtp_address: ${smtp_address}
        smtp_port: ${smtp_port}
        sender_login: ${sender_login}
        sender_password: ${sender_password}
        sender_alias: ${sender_alias}
        receiver_emails: ${receiver_emails}  # string containing email addresses separated by commas
````

### 3. Test your updated Action list

Run your Checkpoint to Validate a <TechnicalTag tag="batch" text="Batch" /> of data and receive an email on the success or failure of the Validation.

:::note Reminder
Our [guide on how to Validate data by running a Checkpoint](../how_to_validate_data_by_running_a_checkpoint.md) has instructions for this step.
:::

If successful, you should receive an email that looks like this:

![image](../../../../docs/images/email_example.png)

## Additional notes

If your `great_expectations.yml` contains multiple configurations for Data Docs sites, all of them will be included in the email by default. If you would like to be more specific, you can configure the `notify_with` variable in your Checkpoint configuration.

The following example will configure the email to include links <TechnicalTag tag="data_docs" text="Data Docs" /> at local_site and s3_site.

```yaml
# Example data_docs_sites configuration in `great_expectations.yml`
data_docs_sites:
  local_site:
    class_name: SiteBuilder
    show_how_to_buttons: true
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: uncommitted/data_docs/local_site/
    site_index_builder:
      class_name: DefaultSiteIndexBuilder
  s3_site:  # this is a user-selected name - you may select your own
    class_name: SiteBuilder
    store_backend:
      class_name: TupleS3StoreBackend
      bucket: data-docs.my_org  # UPDATE the bucket name here to match the bucket you configured above.
    site_index_builder:
      class_name: DefaultSiteIndexBuilder
      show_cta_footer: true
```

```yaml
# Example Checkpoint configuration
action_list:
    - name: send_email_on_validation_result # name can be set to any value
          action:
            class_name: EmailAction
            notify_on: all # possible values: "all", "failure", "success"
            #--------------------------------
            # This is what was configured
            #--------------------------------
            notify_with:
              - local_site
              - gcs_site
            use_ssl: True
            use_tls: False
            renderer:
              module_name: great_expectations.render.renderer.email_renderer
              class_name: EmailRenderer
            # put the actual following information in the uncommitted/config_variables.yml file
            # or pass in as environment variable
            smtp_address: ${smtp_address}
            smtp_port: ${smtp_port}
            sender_login: ${sender_login}
            sender_password: ${sender_password}
            sender_alias: ${sender_alias}
            receiver_emails: ${receiver_emails} # string containing email addresses separated by commas
```

## Additional resources

The EmailAction uses smtplib. You can get more information about this module [here](https://docs.python.org/3/library/smtplib.html).
