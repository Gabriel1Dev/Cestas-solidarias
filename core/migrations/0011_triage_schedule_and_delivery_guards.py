from importlib import import_module

from django.db import migrations, models


def fill_missing_schedule_times(apps, schema_editor):
    Authorization = apps.get_model('core', 'ScheduleAuthorization')
    Configuration = apps.get_model('core', 'Configuration')
    default = Configuration.objects.using(schema_editor.connection.alias).filter(pk=1).values_list('distribution_time', flat=True).first()
    default = default or '09:00'
    for auth in Authorization.objects.using(schema_editor.connection.alias).filter(time__isnull=True).iterator():
        scheduled = auth.period.scheduled_time
        Authorization.objects.using(schema_editor.connection.alias).filter(pk=auth.pk).update(time=scheduled or default)


previous = import_module('core.migrations.0007_client_workflow_guards').SQL
function_start = previous.index('CREATE OR REPLACE FUNCTION cestas_insert()')
start = previous.index(" ELSIF TG_TABLE_NAME='core_delivery' THEN")
end = previous.index(" ELSIF TG_TABLE_NAME='core_extensionauthorization' THEN", start)
delivery_branch = """
 ELSIF TG_TABLE_NAME='core_delivery' THEN
  IF NOT EXISTS(SELECT 1 FROM core_period p JOIN core_benefit b ON b.id=p.benefit_id JOIN core_family f ON f.id=b.family_id
    JOIN core_membership m ON m.family_id=b.family_id AND m.person_id=NEW.recipient_id AND m.ended_at IS NULL
    WHERE p.id=NEW.period_id AND f.status='approved'
      AND NEW.delivered_on>=b.original_start
      AND NEW.delivered_on<=(now() AT TIME ZONE 'America/Sao_Paulo')::date
      AND (NOT NEW.historical OR (NEW.delivered_on<(now() AT TIME ZONE 'America/Sao_Paulo')::date
        AND EXISTS(SELECT 1 FROM auth_user u WHERE u.id=NEW.recorded_by_id AND u.is_superuser)))) THEN
   RAISE EXCEPTION 'Entrega fora do periodo/agendamento ou pessoa sem vinculo' USING ERRCODE='23514';
  END IF;
"""
function_end = previous.index('END $$;', end) + len('END $$;')
insert_sql = previous[function_start:start] + delivery_branch + previous[end:function_end]
insert_sql = insert_sql.replace('NEW.months>6', 'NEW.months>3')
immutable_function = """
CREATE OR REPLACE FUNCTION cestas_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME IN ('core_benefit','core_period') AND current_setting('cestas.allow_triage_duration', true)='1' THEN
  IF TG_TABLE_NAME='core_benefit' THEN
   IF EXISTS(SELECT 1 FROM core_family f WHERE f.id=OLD.family_id AND f.status='pending')
      AND NOT EXISTS(SELECT 1 FROM core_delivery d JOIN core_period p ON p.id=d.period_id WHERE p.benefit_id=OLD.id) THEN
    IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
   END IF;
  ELSE
   IF EXISTS(SELECT 1 FROM core_family f JOIN core_benefit b ON b.family_id=f.id WHERE b.id=OLD.benefit_id AND f.status='pending')
      AND NOT EXISTS(SELECT 1 FROM core_delivery d JOIN core_period p ON p.id=d.period_id WHERE p.benefit_id=OLD.benefit_id) THEN
    IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
   END IF;
  END IF;
 END IF;
 RAISE EXCEPTION 'Historico imutavel: use anotacao de correcao auditada' USING ERRCODE='23514';
END $$;
"""


class Migration(migrations.Migration):
    dependencies = [('core', '0010_delivery_actual_date')]

    operations = [
        migrations.RunPython(fill_missing_schedule_times, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='scheduleauthorization', name='time',
            field=models.TimeField(),
        ),
        migrations.RunSQL(immutable_function + insert_sql, migrations.RunSQL.noop),
    ]
