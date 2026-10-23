from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def merge_duplicate_cart_items(apps, schema_editor):
    from django.db.models import Count, Sum

    Cart = apps.get_model('app', 'Cart')
    duplicates = Cart.objects.values('user_id', 'product_id').annotate(
        item_count=Count('id'),
        total_quantity=Sum('quantity'),
    ).filter(item_count__gt=1)
    for duplicate in duplicates:
        items = Cart.objects.filter(
            user_id=duplicate['user_id'],
            product_id=duplicate['product_id'],
        ).order_by('id')
        keep = items.first()
        keep.quantity = duplicate['total_quantity']
        keep.save(update_fields=['quantity'])
        items.exclude(pk=keep.pk).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0006_alter_customer_mobile_alter_customer_zipcode_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WishlistItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.RunPython(merge_duplicate_cart_items, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='cart',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_cart_user_product'),
        ),
        migrations.AddConstraint(
            model_name='wishlistitem',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_wishlist_user_product'),
        ),
    ]
