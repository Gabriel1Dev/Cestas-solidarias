from pathlib import Path
from django.db import migrations
SQL=Path(__file__).with_suffix('.sql').read_text(encoding='utf-8')
REVERSE='DROP FUNCTION cestas_immutable() CASCADE; DROP FUNCTION cestas_family_update() CASCADE; DROP FUNCTION cestas_insert() CASCADE;'
class Migration(migrations.Migration):
    dependencies=[('core','0001_initial')]
    operations=[migrations.RunSQL(SQL,REVERSE)]
