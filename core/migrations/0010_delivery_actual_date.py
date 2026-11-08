from importlib import import_module
from django.db import migrations
from django.db import models

previous = import_module('core.migrations.0007_client_workflow_guards').SQL
start = previous.index(" ELSIF TG_TABLE_NAME='core_delivery' THEN")
end = previous.index(" ELSIF TG_TABLE_NAME='core_extensionauthorization' THEN", start)
new_branch = """
 ELSIF TG_TABLE_NAME='core_delivery' THEN
  IF NOT EXISTS(SELECT 1 FROM core_period p JOIN core_benefit b ON b.id=p.benefit_id JOIN core_family f ON f.id=b.family_id
    JOIN core_membership m ON m.family_id=b.family_id AND m.person_id=NEW.recipient_id AND m.ended_at IS NULL
    WHERE p.id=NEW.period_id AND f.status='approved'
      AND NEW.delivered_on >= b.original_start
      AND NEW.delivered_on <= (now() AT TIME ZONE 'America/Sao_Paulo')::date) THEN
   RAISE EXCEPTION 'Data de entrega invalida ou pessoa sem vinculo' USING ERRCODE='23514';
  END IF;
"""
function_sql = (previous[:start] + new_branch + previous[end:]).split('CREATE OR REPLACE FUNCTION cestas_family_update()')[0]

class Migration(migrations.Migration):
    dependencies=[('core','0009_exception_document_flag')]
    operations=[migrations.RunSQL(function_sql, migrations.RunSQL.noop),migrations.RemoveConstraint(model_name='period',name='six_periods_only'),migrations.AddConstraint(model_name='period',constraint=models.CheckConstraint(condition=models.Q(number__gte=1,number__lte=32767),name='six_periods_only'))]
