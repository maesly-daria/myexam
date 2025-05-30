from django.db import migrations

def create_customuser_table(apps, schema_editor):
    # SQL для создания таблицы
    schema_editor.execute("""
        CREATE TABLE IF NOT EXISTS recreation_customuser (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password VARCHAR(128) NOT NULL,
            last_login DATETIME NULL,
            is_superuser BOOLEAN NOT NULL,
            username VARCHAR(150) NOT NULL UNIQUE,
            first_name VARCHAR(150) NOT NULL,
            last_name VARCHAR(150) NOT NULL,
            email VARCHAR(254) NOT NULL,
            is_staff BOOLEAN NOT NULL,
            is_active BOOLEAN NOT NULL,
            date_joined DATETIME NOT NULL,
            phone VARCHAR(20) NOT NULL UNIQUE,
            patronymic VARCHAR(100) NULL
        )
    """)

class Migration(migrations.Migration):
    dependencies = [
        # Укажите реальное имя последней примененной миграции
        ('recreation', '0012_customuser_birth_date_customuser_bookings_and_more'),  # Замените на фактическое имя
    ]

    operations = [
        migrations.RunPython(create_customuser_table),
    ]