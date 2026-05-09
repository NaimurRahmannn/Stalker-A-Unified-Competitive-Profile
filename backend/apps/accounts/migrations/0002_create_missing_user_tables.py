from django.db import migrations


def create_missing_user_tables(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    existing_tables = schema_editor.connection.introspection.table_names()

    if User._meta.db_table not in existing_tables:
        schema_editor.create_model(User)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_missing_user_tables, migrations.RunPython.noop),
    ]
