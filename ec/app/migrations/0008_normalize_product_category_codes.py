from django.db import migrations


def normalize_milkshake_category(apps, schema_editor):
    Product = apps.get_model('app', 'Product')
    Product.objects.filter(category='Ms').update(category='MS')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_wishlistitem_and_more'),
    ]

    operations = [
        migrations.RunPython(
            normalize_milkshake_category,
            migrations.RunPython.noop,
        ),
    ]
