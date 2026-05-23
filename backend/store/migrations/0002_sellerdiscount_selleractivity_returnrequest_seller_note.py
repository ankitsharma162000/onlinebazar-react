from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
        ('seller', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnrequest',
            name='seller_note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='SellerDiscount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('discount_type', models.CharField(choices=[('flat', 'Flat Amount (Rs.)'), ('percent', 'Percentage (%)')], max_length=10)),
                ('value', models.DecimalField(decimal_places=2, max_digits=8)),
                ('is_active', models.BooleanField(default=True)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_discounts', to='seller.seller')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_discounts', to='store.product')),
            ],
            options={'db_table': 'store_sellerdiscount', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SellerActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('action', models.CharField(choices=[
                    ('discount_added', 'Discount Added'),
                    ('discount_removed', 'Discount Removed'),
                    ('price_changed', 'Price Changed'),
                    ('return_approved', 'Return Approved'),
                    ('return_rejected', 'Return Rejected'),
                ], max_length=30)),
                ('details', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='seller.seller')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.product')),
            ],
            options={'db_table': 'store_selleractivity', 'ordering': ['-created_at']},
        ),
    ]
