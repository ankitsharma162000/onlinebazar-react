from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendingquestion',
            name='escalated_to',
            field=models.CharField(
                choices=[('superadmin', 'SuperAdmin'), ('seller', 'Seller')],
                default='superadmin', max_length=20
            ),
        ),
        migrations.AddField(
            model_name='pendingquestion',
            name='seller_email',
            field=models.EmailField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pendingquestion',
            name='order_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='pendingquestion',
            name='product_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='chatmessage',
            name='sender',
            field=models.CharField(
                choices=[('user', 'User'), ('bot', 'Bot'), ('admin', 'Admin'), ('seller', 'Seller')],
                max_length=10
            ),
        ),
    ]
