from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("external_apis", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="apicache",
            new_name="external_ap_provide_6ddffc_idx",
            old_name="external_ap_provider_2414e0_idx",
        ),
    ]
