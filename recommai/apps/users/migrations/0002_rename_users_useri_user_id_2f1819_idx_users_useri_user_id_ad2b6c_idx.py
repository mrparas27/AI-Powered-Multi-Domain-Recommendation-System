from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="userinteraction",
            new_name="users_useri_user_id_ad2b6c_idx",
            old_name="users_useri_user_id_2f1819_idx",
        ),
    ]
