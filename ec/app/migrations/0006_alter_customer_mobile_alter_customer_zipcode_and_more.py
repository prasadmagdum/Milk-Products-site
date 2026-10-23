from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_contactmessage_order_orderitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='mobile',
            field=models.CharField(max_length=16),
        ),
        migrations.AlterField(
            model_name='customer',
            name='zipcode',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='shipping_cost',
            field=models.DecimalField(decimal_places=2, default=Decimal('40.00'), max_digits=8),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='discounted_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='selling_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
    ]
